"use server";

import "@/lib/undici-config";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { headers } from "next/headers";
import { PDFDocument } from "pdf-lib";
import { verify_key, get_restricted_key } from "@/lib/db_pool";
import { fetch_geolocation } from "@/lib/geoip";
import { timestamp } from "@/lib/timestamp";
import {
  CHECK_ORDER,
  type CheckId,
  type CheckResult,
  type DiligenceEvent,
  type ExtractedProfile,
  type RiskLevel,
  type SanctionsMatch,
  type WebRegistry,
  type WebRegistryField,
} from "@/lib/diligence-types";

// ─── Config (server-only: none of this reaches the browser) ───────────────
const PROTECTED_ACCESS = process.env.PROTECTED_ACCESS !== "false";
const AGENT_URL = (process.env.DILIGENCE_AGENT_URL ?? "").replace(/\/+$/, "");
const HINTS_PATH = process.env.DILIGENCE_HINTS_PATH ?? path.join(process.cwd(), "data", "llm_hints_diligence.json");
const API_PREFIX = "/api/v1/sparrow-agents";
const PDF_PAGE_LIMIT_WITH_KEY = 10;
const PDF_PAGE_LIMIT_FREE_TIER = 3;
const MAX_FILE_BYTES = 5 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/tiff", "image/webp", "application/pdf"];
const LONG_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

// ─── Types ────────────────────────────────────────────────────────────────
type Emit = (event: DiligenceEvent) => void;

interface RunContext {
  file: File;
  sparrowKey: string;
  clientIp: string;
  country: string;
  isPdf: boolean;
  pageCount: number;
}

// Shape of the agent's "assess" findings (see summary.py).
interface Finding {
  check: string;
  severity: "needs_review" | "incomplete" | "info" | "clean";
  message: string;
  details?: {
    top_matches?: { name?: string | null; entry_type?: string | null; score?: number | null; list?: string | null }[];
    registry?: Record<string, { value?: string | null; source_url?: string | null } | null>;
  };
}

type AgentResult = Record<string, unknown> & { status?: string; error?: string };

// ─── Helpers ──────────────────────────────────────────────────────────────
// Reads the uploaded file itself to find out whether it is a PDF and how many
// pages it has - client-reported values are never trusted (same as Process).
async function resolveActualPdfInfo(
  file: File,
): Promise<{ isPdf: boolean; pageCount: number } | { error: string }> {
  const looksLikePdf = file.type === "application/pdf" || file.name?.toLowerCase().endsWith(".pdf");
  if (!looksLikePdf) return { isPdf: false, pageCount: 1 };

  try {
    const bytes = await file.arrayBuffer();
    const pdfDoc = await PDFDocument.load(bytes, { ignoreEncryption: true });
    return { isPdf: true, pageCount: pdfDoc.getPageCount() };
  } catch {
    return { error: "The uploaded file could not be read as a valid PDF. Please check the file and try again." };
  }
}

function text(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const s = String(value).trim();
  return s === "" || s.toLowerCase() === "null" || s.toLowerCase() === "none" ? null : s;
}

// ─── Which checks apply ────────────────────────────────────────────────────
const IDENTITY_FIELDS = ["company_name", "street", "postal_code", "city", "country", "registration_number", "vat_id"] as const;

// VIES covers EU member states (Greece uses EL; XI is Northern Ireland, covered for goods).
const EU_VAT_PREFIXES = new Set([
  "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU",
  "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "XI",
]);
const UK_COUNTRY_NAMES = new Set(["united kingdom", "uk", "great britain", "gb", "england", "scotland", "wales", "northern ireland"]);

function vatPrefix(fields: Record<string, unknown>): string {
  const vat = String(fields.vat_id ?? "").trim().replace(/\s+/g, "").toUpperCase();
  return vat.length >= 2 && /^[A-Z]{2}/.test(vat) ? vat.slice(0, 2) : "";
}

// VIES only for EU VAT numbers, Companies House only for UK companies;
// GLEIF, both sanctions lists and web research always.
function planChecks(fields: Record<string, unknown>): { run: CheckId[]; notApplicable: Partial<Record<CheckId, string>> } {
  const prefix = vatPrefix(fields);
  const country = String(fields.country ?? "").trim().toLowerCase();
  const run: CheckId[] = [];
  const notApplicable: Partial<Record<CheckId, string>> = {};

  if (EU_VAT_PREFIXES.has(prefix)) run.push("vies_check");
  else notApplicable.vies_check = "No EU VAT ID on the document.";

  run.push("gleif_check");

  if (UK_COUNTRY_NAMES.has(country) || prefix === "GB") run.push("companies_house_check");
  else notApplicable.companies_house_check = "Not a UK company.";

  run.push("ofac_check", "eu_sanctions_check", "web_research_check");
  return { run, notApplicable };
}

// ─── Agent calls ───────────────────────────────────────────────────────────
async function agentStep(
  ctx: RunContext,
  step: string,
  fields: Record<string, unknown>,
  timeoutMs: number,
): Promise<{ result: AgentResult; seconds: number }> {
  const resultKey = ({ summarize: "summary", assess: "assessment" } as Record<string, string>)[step] ?? step;
  const started = Date.now();
  try {
    const response = await fetch(`${AGENT_URL}${API_PREFIX}/execute/data`, {
      method: "POST",
      headers: { accept: "application/json", "content-type": "application/json" },
      body: JSON.stringify({
        agent_name: "diligence",
        sparrow_key: ctx.sparrowKey,   // never exposed to client
        input_data: { step, ...fields },
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) {
      const detail = await response.text();
      console.error(`[${timestamp()}] Diligence step ${step} returned ${response.status}: ${detail.slice(0, 300)}`);
      return { result: { status: "failed", error: `status ${response.status}` }, seconds: (Date.now() - started) / 1000 };
    }
    const payload = await response.json() as { result?: Record<string, AgentResult> };
    const inner = payload.result?.[resultKey];
    if (!inner) {
      console.error(`[${timestamp()}] Diligence step ${step}: no '${resultKey}' in response`);
      return { result: { status: "failed", error: "no result in response" }, seconds: (Date.now() - started) / 1000 };
    }
    return { result: inner, seconds: (Date.now() - started) / 1000 };
  } catch (err) {
    console.error(`[${timestamp()}] Diligence step ${step} failed:`, err);
    return { result: { status: "failed", error: "service not reachable" }, seconds: (Date.now() - started) / 1000 };
  }
}

// ─── Findings -> CheckResult ───────────────────────────────────────────────
function toCheckResult(id: CheckId, agentResult: AgentResult, findings: Finding[], seconds: number): CheckResult {
  const mine = findings.filter((f) => f.check === id);
  const message = mine.map((f) => f.message).join(" ") || "No details available.";

  if (agentResult.status === "skipped") {
    return { id, status: "skipped", duration_sec: seconds, message };
  }
  if (agentResult.status !== "success" || mine.some((f) => f.severity === "incomplete")) {
    return { id, status: "failed", duration_sec: seconds, message };
  }

  const level = mine.some((f) => f.severity === "needs_review")
    ? "review"
    : mine.some((f) => f.severity === "info")
      ? "info"
      : "ok";

  const result: CheckResult = { id, status: "success", duration_sec: seconds, level, message };

  const matches: SanctionsMatch[] = mine.flatMap((f) => f.details?.top_matches ?? []).map((m) => ({
    name: String(m.name ?? ""),
    kind: m.entry_type ?? "entry",
    score: Number(m.score ?? 0),
    list: String(m.list ?? ""),
  }));
  if (matches.length > 0) result.matches = matches;

  const rawRegistry = mine.find((f) => f.details?.registry)?.details?.registry;
  if (rawRegistry) {
    const registry: WebRegistry = {};
    for (const [key, entry] of Object.entries(rawRegistry)) {
      if (entry?.value && entry.source_url) {
        registry[key as WebRegistryField] = { value: String(entry.value), source_url: entry.source_url };
      }
    }
    if (Object.keys(registry).length > 0) {
      result.registry = registry;
      if (level !== "review") result.message = "Company details (web, unverified)";
    }
  }
  return result;
}

// ─── Preparation: validate the upload and resolve the key ──────────────────
async function prepareRun(formData: FormData): Promise<RunContext | { error: string }> {
  const file = formData.get("file") as File | null;
  let sparrowKey = ((formData.get("sparrowKey") as string) ?? "").trim();

  if (!AGENT_URL) {
    console.error(`[${timestamp()}] DILIGENCE_AGENT_URL is not set`);
    return { error: "The due diligence service is not configured." };
  }

  // ── File checks (enforced here, not only in the browser) ──────────────
  if (!file || file.size === 0) {
    return { error: "No file provided. Please upload a document before running." };
  }
  if (file.size > MAX_FILE_BYTES) {
    return { error: "The file is larger than 5 MB." };
  }
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return { error: "Unsupported file type. Please upload a PDF, PNG, JPG, TIFF or WebP file." };
  }

  const pdfInfo = await resolveActualPdfInfo(file);
  if ("error" in pdfInfo) return { error: pdfInfo.error };
  const { isPdf, pageCount } = pdfInfo;

  // ── Key resolution - once per run; the key stays on the server ─────────
  const headersList = await headers();
  const clientIp = headersList.get("x-forwarded-for")?.split(",")[0].trim()
    ?? headersList.get("x-real-ip")
    ?? "unknown";

  if (PROTECTED_ACCESS) {
    if (sparrowKey) {
      const valid = await verify_key(sparrowKey);
      if (!valid) {
        return { error: "Invalid Sparrow key. Please check your key or leave empty for limited usage." };
      }
      if (isPdf && pageCount > PDF_PAGE_LIMIT_WITH_KEY) {
        return {
          error: `PDFs are limited to maximum ${PDF_PAGE_LIMIT_WITH_KEY} pages even with a valid Sparrow key. This document has ${pageCount} pages.`,
        };
      }
    } else {
      const restrictedKey = await get_restricted_key(clientIp);
      if (!restrictedKey) {
        return {
          error: "Rate limit exceeded or no available keys. Please obtain a Sparrow key by emailing abaranovskis@redsamuraiconsulting.com.",
        };
      }
      if (isPdf && pageCount > PDF_PAGE_LIMIT_FREE_TIER) {
        return {
          error: `Free tier is limited to PDFs with maximum ${PDF_PAGE_LIMIT_FREE_TIER} pages. This document has ${pageCount} pages.`,
        };
      }
      sparrowKey = restrictedKey;
    }
  } else if (!sparrowKey) {
    sparrowKey = "unrestricted_access";
  }

  const country = await fetch_geolocation(clientIp);
  return { file, sparrowKey, clientIp, country, isPdf, pageCount };
}

// ─── Step 1: extraction ────────────────────────────────────────────────────
async function extract(ctx: RunContext): Promise<{ extraction: AgentResult & { extracted_data?: Record<string, unknown> | null }; seconds: number } | { error: string }> {
  // Field-level rules for the diligence extraction.
  let hints: Buffer;
  try {
    hints = await readFile(HINTS_PATH);
  } catch {
    console.error(`[${timestamp()}] Diligence hints file not found: ${HINTS_PATH}`);
    return { error: "The due diligence service is not configured." };
  }

  console.log(`[${timestamp()}] Diligence extraction request - IP: ${ctx.clientIp}, PDF: ${ctx.isPdf}, Pages: ${ctx.pageCount}, Country: ${ctx.country}`);

  const body = new FormData();
  body.append("agent_name", "diligence");
  body.append("sparrow_key", ctx.sparrowKey);   // never exposed to client
  body.append("extraction_params", "{}");
  body.append("client_ip", ctx.clientIp);       // so Sparrow logs the extraction against the user's IP
  body.append("country", ctx.country);
  body.append("file", ctx.file);
  body.append("hints_file", new Blob([new Uint8Array(hints)], { type: "application/json" }), path.basename(HINTS_PATH));

  const startTime = Date.now();
  let payload: { result?: { extraction?: AgentResult & { extracted_data?: Record<string, unknown> | null } } };
  try {
    const response = await fetch(`${AGENT_URL}${API_PREFIX}/execute/file`, {
      method: "POST",
      headers: { accept: "application/json" },
      body,
      signal: AbortSignal.timeout(LONG_TIMEOUT_MS),
    });
    if (!response.ok) {
      const detail = await response.text();
      console.error(`[${timestamp()}] Diligence agent returned ${response.status}: ${detail.slice(0, 300)}`);
      return { error: "The due diligence service could not process the document. Please try again." };
    }
    payload = await response.json();
  } catch (err) {
    console.error(`[${timestamp()}] Diligence agent call failed:`, err);
    return { error: "The due diligence service is not reachable. Please try again later." };
  }
  const seconds = (Date.now() - startTime) / 1000;

  const extraction = payload.result?.extraction;
  if (!extraction || extraction.status !== "success" || !extraction.extracted_data) {
    console.error(`[${timestamp()}] Diligence extraction failed: ${extraction?.error ?? "no extraction in response"}`);
    return { error: "The company details could not be read from this document." };
  }
  return { extraction, seconds };
}

// ─── run_diligence ─────────────────────────────────────────────────────────
// Called in-process, server-side only, by app/api/diligence/route.ts. Runs the
// whole flow - extraction, the applicable checks, the verdict and the written
// summary - and reports each step through `emit` as it finishes. The Sparrow
// key is resolved once and never leaves this function.
export async function run_diligence(formData: FormData, emit: Emit): Promise<void> {
  const ctx = await prepareRun(formData);
  if ("error" in ctx) {
    emit({ type: "error", message: ctx.error });
    return;
  }

  // ── 1. Extraction ─────────────────────────────────────────────────────
  const extracted = await extract(ctx);
  if ("error" in extracted) {
    emit({ type: "error", message: extracted.error });
    return;
  }
  const data = extracted.extraction.extracted_data!;
  const profile: ExtractedProfile = {
    company_name: text(data.company_name),
    street: text(data.street),
    postal_code: text(data.postal_code),
    city: text(data.city),
    country: text(data.country),
    registration_number: text(data.registration_number),
    vat_id: text(data.vat_id),
    document_suitable: String(data.document_suitable ?? "").trim().toLowerCase() === "true",
  };
  emit({ type: "extraction", duration_sec: extracted.seconds, profile });
  console.log(`[${timestamp()}] Diligence extraction done in ${extracted.seconds.toFixed(1)}s - suitable: ${profile.document_suitable}`);

  // Results collected so far; the verdict and summary steps read this object.
  const results: Record<string, unknown> = { extraction: extracted.extraction };

  const assess = async (): Promise<{ risk_level: RiskLevel; findings: Finding[] } | null> => {
    const { result } = await agentStep(ctx, "assess", { results }, 60_000);
    if (result.status !== "success") return null;
    return { risk_level: result.risk_level as RiskLevel, findings: (result.findings ?? []) as Finding[] };
  };

  // ── 2. Checks (only when the document identifies a company) ───────────
  if (profile.document_suitable && profile.company_name) {
    const fields = Object.fromEntries(IDENTITY_FIELDS.map((k) => [k, data[k] ?? null]));
    const { run, notApplicable } = planChecks(fields);
    emit({ type: "plan", run, not_applicable: notApplicable });

    for (const id of CHECK_ORDER.filter((c) => run.includes(c))) {
      emit({ type: "check_started", id });

      // Web research is the slow step and only rarely changes the outcome, so
      // the verdict from the fast checks is shown before it finishes.
      if (id === "web_research_check") {
        const preliminary = await assess();
        if (preliminary) emit({ type: "verdict", risk_level: preliminary.risk_level });
      }

      const { result, seconds } = await agentStep(ctx, id, fields, 300_000);
      results[id] = result;

      const assessed = await assess();
      emit({ type: "check", result: toCheckResult(id, result, assessed?.findings ?? [], seconds) });
      console.log(`[${timestamp()}] Diligence ${id}: ${result.status} in ${seconds.toFixed(1)}s`);
    }
  }

  // ── 3. Final verdict (deterministic, instant) ─────────────────────────
  const final = await assess();
  if (!final) {
    emit({ type: "error", message: "The verdict could not be determined. Please try again." });
    return;
  }
  emit({ type: "verdict", risk_level: final.risk_level });
  console.log(`[${timestamp()}] Diligence verdict: ${final.risk_level}`);

  // ── 4. Written summary (slow: language model) ─────────────────────────
  const { result: summary, seconds: summarySeconds } = await agentStep(ctx, "summarize", { results }, 300_000);
  const narrative = typeof summary.narrative === "string" && summary.narrative.trim() !== ""
    ? summary.narrative.trim()
    : "A written summary could not be generated for this run. The results above are complete.";
  emit({ type: "narrative", text: narrative, duration_sec: summarySeconds });
  console.log(`[${timestamp()}] Diligence summary done in ${summarySeconds.toFixed(1)}s`);
}