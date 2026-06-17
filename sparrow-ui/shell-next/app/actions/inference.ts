"use server";

import { verify_key, get_restricted_key } from "@/lib/db_pool";
import { fetch_geolocation } from "@/lib/geoip";
import { timestamp } from "@/lib/timestamp";
import { headers } from "next/headers";

// ─── Config ───────────────────────────────────────────────────────────────
const PROTECTED_ACCESS = process.env.PROTECTED_ACCESS !== "false";
const BACKEND_URL = process.env.BACKEND_URL!;
const PDF_PAGE_LIMIT_WITH_KEY = 10;
const PDF_PAGE_LIMIT_FREE_TIER = 3;
const LONG_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

function getModelOptions(): Record<string, string> {
  const options: Record<string, string> = {};
  let i = 1;
  while (true) {
    const val = process.env[`BACKEND_OPTIONS_${i}`];
    if (!val) break;
    const parts = val.split(",");
    if (parts.length >= 3) {
      options[parts[2]] = `${parts[0]},${parts[1]}`;
    }
    i++;
  }
  return options;
}

// ─── Types ────────────────────────────────────────────────────────────────
export type InferenceError = { error: string };
export type InferenceSuccess = { data: object; durationSec: number };
export type InferenceResult = InferenceSuccess | InferenceError;

// ─── Helpers ──────────────────────────────────────────────────────────────
function parseQuery(query: string): { queryJson: string | object } | { error: string } {
  const trimmed = query.trim();
  if (trimmed === "*") return { queryJson: "*" };

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    return { error: "Invalid JSON format in query input." };
  }

  if (typeof parsed !== "object" || parsed === null) {
    return { error: "Invalid input. Only JSON objects, arrays of objects, or wildcard '*' are allowed." };
  }

  if (Array.isArray(parsed)) {
    if (!parsed.every((item) => typeof item === "object" && item !== null && !Array.isArray(item))) {
      return { error: "Invalid input. Arrays must contain only JSON objects." };
    }
  }

  return { queryJson: parsed };
}

// ─── run_inference ────────────────────────────────────────────────────────
export async function run_inference(formData: FormData): Promise<InferenceResult> {
  const file      = formData.get("file") as File | null;
  const query     = formData.get("query") as string;
  let sparrowKey    = (formData.get("sparrowKey") as string) ?? "";
  const isPdf     = formData.get("isPdf") === "true";
  const pageCount = parseInt(formData.get("pageCount") as string) || 1;
  const tableExtraction = formData.get("tableExtraction") === "true";
  const validationOff   = formData.get("validationOff") === "true";
  const modelName = formData.get("modelName") as string;

  // ── File check ───────────────────────────────────────────────────────
  if (!file || file.size === 0) {
    return { error: "No file provided. Please upload a file before submitting." };
  }

  // ── Query check ──────────────────────────────────────────────────────
  if (!query || query.trim() === "") {
    return { error: "No query provided. Please enter a query before submitting." };
  }

  // ── Query parse ──────────────────────────────────────────────────────
  const queryResult = parseQuery(query);
  if ("error" in queryResult) return { error: queryResult.error };
  let queryJson = queryResult.queryJson;

  // ── Key validation ───────────────────────────────────────────────────
  const headersList = await headers();
  const clientIp = headersList.get("x-forwarded-for")?.split(",")[0].trim()
    ?? headersList.get("x-real-ip")
    ?? "unknown";

  if (PROTECTED_ACCESS) {
    if (sparrowKey && sparrowKey.trim() !== "") {
      const valid = await verify_key(sparrowKey);
      if (!valid) {
        return { error: "Invalid Sparrow key. Please check your key or leave empty for limited usage." };
      }
      if (isPdf && pageCount > PDF_PAGE_LIMIT_WITH_KEY) {
        return {
          error: `PDFs are limited to maximum ${PDF_PAGE_LIMIT_WITH_KEY} pages even with a valid Sparrow key. This document has ${pageCount} pages. For larger documents, please contact us at abaranovskis@redsamuraiconsulting.com.`,
        };
      }
    } else {
      // restrictedKey stays strictly on the server — never returned to client
      const restrictedKey = await get_restricted_key(clientIp);
      if (!restrictedKey) {
        return {
          error: "Rate limit exceeded or no available keys. Please obtain a Sparrow key by emailing abaranovskis@redsamuraiconsulting.com.",
        };
      }
      if (isPdf && pageCount > PDF_PAGE_LIMIT_FREE_TIER) {
        return {
          error: `Free tier is limited to PDFs with maximum ${PDF_PAGE_LIMIT_FREE_TIER} pages. This document has ${pageCount} pages. For larger documents, please obtain a Sparrow key by emailing abaranovskis@redsamuraiconsulting.com.`,
        };
      }
      sparrowKey = restrictedKey;
    }
  } else {
    console.log(`[${timestamp()}] Protected access disabled - skipping key validation for IP: ${clientIp}`);
    if (!sparrowKey || sparrowKey.trim() === "") {
      sparrowKey = "unrestricted_access";
    }
  }

  // ── Build options ─────────────────────────────────────────────────────
  const modelOptions = getModelOptions();
  const modelKeys = Object.keys(modelOptions);
  let table = false;
  let tableTemplate = "";
  const selectedOptions: string[] = [];

  if (tableExtraction) {
    queryJson = "*";
    table = true;
    tableTemplate = "sparrow_generic_table";
    selectedOptions.push("mlx,mlx-community/dots.ocr-bf16");
  }
  if (validationOff) selectedOptions.push("validation_off");

  let finalOptions = modelOptions[modelName] ?? modelOptions[modelKeys[0]];
  if (selectedOptions.length > 0) finalOptions += "," + selectedOptions.join(",");

  // ── Call FastAPI backend ──────────────────────────────────────────────
  const country = await fetch_geolocation(clientIp);
  const shortModel = modelName.includes("Standard") ? "Standard" : modelName.includes("Advanced") ? "Advanced" : "Table";
  console.log(`[${timestamp()}] Inference request - IP: ${clientIp}, Model: ${shortModel}, Table: ${table}, Country: ${country}`);

  const backendForm = new FormData();
  backendForm.append("file", file);
  backendForm.append("query",          queryJson === "*" ? "*" : JSON.stringify(queryJson));
  backendForm.append("pipeline",       "sparrow-parse");
  backendForm.append("table",          String(table));
  backendForm.append("table_template", tableTemplate);
  backendForm.append("options",        finalOptions);
  backendForm.append("debug_dir",      "");
  backendForm.append("debug",          "false");
  backendForm.append("sparrow_key",    sparrowKey);   // never exposed to client
  backendForm.append("client_ip",      clientIp);
  backendForm.append("country",        country);

  const startTime = Date.now();
  const response = await fetch(BACKEND_URL, {
    method: "POST",
    headers: { accept: "application/json" },
    body: backendForm,
    signal: AbortSignal.timeout(LONG_TIMEOUT_MS),
  });

  const durationSec = (Date.now() - startTime) / 1000;

  if (!response.ok) {
    const text = await response.text();
    return { error: `Request failed with status code ${response.status}: ${text}` };
  }

  const data = await response.json() as object;
  return { data, durationSec };
}

// ─── summarize_result ─────────────────────────────────────────────────────
export type SummarizeResult = { summary: string } | InferenceError;

export async function summarize_result(
  data: unknown,
  sparrowKey: string,
  modelName: string,
): Promise<SummarizeResult> {
  // ── Resolve key server-side ──────────────────────────────────────────
  const headersList = await headers();
  const clientIp = headersList.get("x-forwarded-for")?.split(",")[0].trim()
    ?? headersList.get("x-real-ip")
    ?? "unknown";

  let resolvedKey = sparrowKey;

  if (PROTECTED_ACCESS) {
    if (!sparrowKey || sparrowKey.trim() === "") {
      const restrictedKey = await get_restricted_key(clientIp);
      if (!restrictedKey) {
        return { error: "Rate limit exceeded. Please obtain a Sparrow key by emailing abaranovskis@redsamuraiconsulting.com." };
      }
      resolvedKey = restrictedKey;
    }
  } else {
    if (!resolvedKey || resolvedKey.trim() === "") {
      resolvedKey = "unrestricted_access";
    }
  }

  // ── Build query ──────────────────────────────────────────────────────
  const jsonStr = JSON.stringify(data, null, 2);
  const query = `instruction: summarize this json data, payload: ${jsonStr}`;

  // ── Resolve model options ────────────────────────────────────────────
  const modelOptions = getModelOptions();
  const modelKeys = Object.keys(modelOptions);
  const finalOptions = modelOptions[modelName] ?? modelOptions[modelKeys[0]];

  // ── Build instruction URL ────────────────────────────────────────────
  const instructionUrl = BACKEND_URL.replace("/inference", "/instruction-inference");

  // ── Geolocation ──────────────────────────────────────────────────────
  const country = await fetch_geolocation(clientIp);
  const shortModel = modelName.includes("Standard") ? "Standard" : modelName.includes("Advanced") ? "Advanced" : "Table";
  console.log(`[${timestamp()}] Summarize request - IP: ${clientIp}, Model: ${shortModel}, Country: ${country}`);

  // ── Call backend ─────────────────────────────────────────────────────
  try {
    const formData = new FormData();
    formData.append("query",      query);
    formData.append("pipeline",   "sparrow-instructor");
    formData.append("options",    finalOptions);
    formData.append("debug_dir",  "");
    formData.append("debug",      "false");
    formData.append("sparrow_key", resolvedKey);
    formData.append("client_ip",  clientIp);
    formData.append("country",    country);

    const response = await fetch(instructionUrl, {
      method: "POST",
      headers: { accept: "application/json" },
      body: formData,
      signal: AbortSignal.timeout(LONG_TIMEOUT_MS),
    });

    if (!response.ok) {
      const text = await response.text();
      return { error: `Failed to generate summary. Status code: ${response.status}: ${text}` };
    }

    const raw = await response.json();
    let summary: string;
    if (typeof raw === "string") {
      summary = raw;
    } else if (typeof raw === "object" && raw !== null) {
      const val = Object.values(raw)[0];
      summary = typeof val === "string" ? val : JSON.stringify(raw);
    } else {
      summary = String(raw);
    }
    return { summary };
  } catch (err) {
    return { error: `Error generating summary: ${String(err)}` };
  }
}