"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import {
  CircleAlert,
  CircleCheck,
  ExternalLink,
  FileSearch,
  Info,
  Minus,
  Play,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestionMark,
} from "lucide-react";
import { UploadCard } from "./diligence-upload-card";
import { DEFAULT_MOCK_SCENARIO, MOCK_SCENARIOS, runMockDiligence } from "@/lib/diligence-mock";
import {
  CHECK_META,
  CHECK_ORDER,
  type CheckId,
  type CheckResult,
  type DiligenceEvent,
  type ExtractedProfile,
  type RiskLevel,
  type WebRegistry,
  type WebRegistryField,
} from "@/lib/diligence-types";

// While the API is not connected, results come from mock.ts.
const USE_MOCK = true;

// ─── State ────────────────────────────────────────────────────────────────
type Phase = "idle" | "extracting" | "checking" | "summarizing" | "done" | "error";

interface RowState {
  status: "pending" | "running" | "done" | "na";
  result?: CheckResult;
  reason?: string;
}

interface State {
  phase: Phase;
  profile: ExtractedProfile | null;
  extractionSec: number | null;
  planned: boolean;
  rows: Record<CheckId, RowState>;
  verdict: { risk_level: RiskLevel; reason?: string } | null;
  narrative: { text: string; duration_sec: number } | null;
  error: string | null;
}

const emptyRows = (): Record<CheckId, RowState> =>
  Object.fromEntries(CHECK_ORDER.map((id) => [id, { status: "pending" }])) as Record<CheckId, RowState>;

const initialState: State = {
  phase: "idle",
  profile: null,
  extractionSec: null,
  planned: false,
  rows: emptyRows(),
  verdict: null,
  narrative: null,
  error: null,
};

type Action = { type: "start" } | { type: "reset" } | DiligenceEvent;

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "reset":
      return initialState;
    case "start":
      return { ...initialState, phase: "extracting" };
    case "extraction":
      return {
        ...state,
        profile: action.profile,
        extractionSec: action.duration_sec,
        phase: action.profile.document_suitable ? "checking" : "summarizing",
      };
    case "plan": {
      const rows = { ...state.rows };
      for (const id of action.run) rows[id] = { status: "pending" };
      for (const [id, reason] of Object.entries(action.not_applicable)) {
        rows[id as CheckId] = { status: "na", reason };
      }
      return { ...state, planned: true, rows };
    }
    case "check_started":
      return { ...state, rows: { ...state.rows, [action.id]: { status: "running" } } };
    case "check":
      return {
        ...state,
        rows: {
          ...state.rows,
          [action.result.id]: action.result.status === "skipped"
            ? { status: "na", result: action.result, reason: action.result.message }
            : { status: "done", result: action.result },
        },
      };
    case "verdict": {
      // Anything that never ran (e.g. document not assessable) is not applicable.
      const rows = { ...state.rows };
      for (const id of CHECK_ORDER) {
        if (rows[id].status === "pending") rows[id] = { status: "na", reason: "Not run." };
      }
      return { ...state, rows, verdict: { risk_level: action.risk_level, reason: action.reason }, phase: "summarizing" };
    }
    case "narrative":
      return { ...state, narrative: { text: action.text, duration_sec: action.duration_sec }, phase: "done" };
    case "error":
      return { ...state, error: action.message, phase: "error" };
  }
}

// ─── Small pieces ─────────────────────────────────────────────────────────
const REGISTRY_LABELS: [WebRegistryField, string][] = [
  ["company_name", "Name"],
  ["registration_number", "Registration no."],
  ["vat_number", "VAT no."],
  ["status", "Status"],
  ["registered", "Registered"],
  ["deregistered", "Deregistered"],
  ["address", "Address"],
  ["activity", "Activity"],
];

function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function RowIcon({ row }: { row: RowState }) {
  if (row.status === "running") return <span className="spinner" />;
  if (row.status === "pending") return <span className="dd-dot" />;
  if (row.status === "na") return <Minus size={14} />;
  const r = row.result;
  if (r?.status === "failed") return <CircleAlert size={16} />;
  if (r?.level === "review") return <CircleAlert size={16} />;
  if (r?.level === "info") return <Info size={16} />;
  return <CircleCheck size={16} />;
}

function rowTone(row: RowState): "ok" | "review" | "info" | "failed" | "muted" {
  if (row.status !== "done" || !row.result) return "muted";
  if (row.result.status === "failed") return "failed";
  return row.result.level ?? "info";
}

const BADGE_TEXT: Record<string, string> = { ok: "Clear", review: "Review", info: "Info", failed: "Failed" };

function RegistryTable({ registry }: { registry: WebRegistry }) {
  const rows = REGISTRY_LABELS.filter(([key]) => registry[key]);
  if (rows.length === 0) return null;
  return (
    <div className="dd-detail">
      <div className="dd-registry">
        {rows.map(([key, label]) => {
          const v = registry[key]!;
          return (
            <div className="dd-registry-row" key={key}>
              <span className="dd-registry-label">{label}</span>
              <span className="dd-registry-value">{v.value}</span>
              <a className="dd-source" href={v.source_url} target="_blank" rel="noopener noreferrer" title={v.source_url}>
                {domainOf(v.source_url)} <ExternalLink size={11} />
              </a>
            </div>
          );
        })}
      </div>
      <div className="hint" style={{ marginTop: 8 }}>
        Taken from public web pages and not verified — compare with your document.
      </div>
    </div>
  );
}

function CheckRow({ id, row }: { id: CheckId; row: RowState }) {
  const meta = CHECK_META[id];
  const tone = rowTone(row);
  const result = row.result;

  let message: string;
  if (row.status === "pending") message = "Waiting";
  else if (row.status === "running") message = "Checking…";
  else if (row.status === "na") message = row.reason ?? "Not applicable.";
  else message = result?.message ?? "";

  return (
    <div className="dd-row" data-state={row.status} data-tone={tone}>
      <div className="dd-row-icon">
        <RowIcon row={row} />
      </div>
      <div className="dd-row-main">
        <div className="dd-row-top">
          <span className="dd-row-title">{meta.title}</span>
          <span className="dd-row-sub">{meta.subtitle}</span>
        </div>
        <div className="dd-row-msg">{message}</div>

        {result?.matches && result.matches.length > 0 && (
          <div className="dd-detail">
            <ul className="dd-matches">
              {result.matches.map((m, i) => (
                <li key={i}>
                  <span className="dd-match-name">{m.name}</span>
                  <span className="dd-match-meta">
                    {m.kind} · score {m.score.toFixed(2)} · {m.list}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result?.registry && <RegistryTable registry={result.registry} />}
      </div>
      <div className="dd-row-side">
        {row.status === "done" && <span className="dd-badge" data-tone={tone}>{BADGE_TEXT[tone]}</span>}
        {row.status === "na" && <span className="dd-badge" data-tone="muted">Not applicable</span>}
        {result && <span className="dd-time">{result.duration_sec.toFixed(1)}s</span>}
      </div>
    </div>
  );
}

function ExtractionRow({ state }: { state: State }) {
  const running = state.phase === "extracting";
  const done = state.profile !== null;
  const suitable = state.profile?.document_suitable ?? true;
  let message = "Waiting";
  if (running) message = "Reading the document…";
  else if (done) message = suitable ? "Company details read from the document." : "No specific company could be identified in this document.";
  const tone = done ? (suitable ? "ok" : "info") : "muted";

  return (
    <div className="dd-row" data-state={running ? "running" : done ? "done" : "pending"} data-tone={tone}>
      <div className="dd-row-icon">
        {running ? <span className="spinner" /> : done ? (suitable ? <CircleCheck size={16} /> : <Info size={16} />) : <span className="dd-dot" />}
      </div>
      <div className="dd-row-main">
        <div className="dd-row-top">
          <span className="dd-row-title">Document extraction</span>
          <span className="dd-row-sub">Sparrow reads the company identity</span>
        </div>
        <div className="dd-row-msg">{message}</div>
      </div>
      <div className="dd-row-side">
        {done && <span className="dd-badge" data-tone={tone}>{suitable ? "Done" : "Info"}</span>}
        {state.extractionSec !== null && <span className="dd-time">{state.extractionSec.toFixed(1)}s</span>}
      </div>
    </div>
  );
}

// ─── Identity card ────────────────────────────────────────────────────────
function IdentityCard({ profile }: { profile: ExtractedProfile }) {
  const cityLine = [profile.postal_code, profile.city].filter(Boolean).join(" ");
  const address = [profile.street, cityLine, profile.country].filter(Boolean).join(", ");
  const items: [string, string | null][] = [
    ["Company", profile.company_name],
    ["Address", address || null],
    ["Registration no.", profile.registration_number],
    ["VAT ID", profile.vat_id],
  ];
  return (
    <div className="card dd-appear">
      <div className="card-header">
        <div>
          <div className="card-title"><FileSearch size={14} /> Identified company</div>
          <div className="card-desc">Read from your document</div>
        </div>
      </div>
      <div className="card-body">
        <dl className="dd-kv">
          {items.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd className={v ? undefined : "dd-empty"}>{v ?? "—"}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

// ─── Verdict card ─────────────────────────────────────────────────────────
const VERDICT_META: Record<RiskLevel, { title: string; tone: "ok" | "review" | "muted"; Icon: typeof ShieldCheck }> = {
  clean: { title: "Clean", tone: "ok", Icon: ShieldCheck },
  review_required: { title: "Review required", tone: "review", Icon: ShieldAlert },
  incomplete: { title: "Incomplete", tone: "muted", Icon: ShieldQuestionMark },
  not_assessable: { title: "Not assessable", tone: "muted", Icon: ShieldQuestionMark },
};

function VerdictCard({ state }: { state: State }) {
  const { phase, verdict, narrative, rows, planned, profile } = state;

  if (phase === "idle") {
    return (
      <div className="card">
        <div className="empty">
          <div className="empty-icon"><ShieldCheck size={20} /></div>
          <h3>No results yet</h3>
          <p>Upload a company document and run the checks. Results appear check by check as they complete.</p>
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="tip" style={{ borderColor: "hsl(var(--destructive) / 0.25)", background: "hsl(var(--destructive) / 0.05)" }}>
        <div className="tip-icon" style={{ color: "hsl(var(--destructive))" }}><CircleAlert size={14} /></div>
        <div>
          <div className="tip-title" style={{ color: "hsl(var(--destructive))" }}>Something went wrong</div>
          <div className="tip-body">{state.error}</div>
        </div>
      </div>
    );
  }

  // Before the verdict: progress.
  if (!verdict) {
    const applicable = CHECK_ORDER.filter((id) => rows[id].status !== "na");
    const finished = applicable.filter((id) => rows[id].status === "done").length;
    const total = applicable.length;
    const pct = planned && total > 0 ? Math.round((finished / total) * 100) : 4;
    return (
      <div className="card">
        <div className="card-body dd-progress-card">
          <div className="row" style={{ gap: 10 }}>
            <span className="spinner" />
            <div style={{ fontSize: 14, fontWeight: 600 }}>
              {phase === "extracting" || !planned ? "Reading the document…" : "Running checks"}
            </div>
            {planned && (
              <div className="hint" style={{ marginLeft: "auto", flex: "none" }}>
                {finished} of {total} complete
              </div>
            )}
          </div>
          <div className="dd-progress"><div className="dd-progress-fill" style={{ width: `${pct}%` }} /></div>
        </div>
      </div>
    );
  }

  const meta = VERDICT_META[verdict.risk_level];
  const done = CHECK_ORDER.map((id) => rows[id]).filter((r) => r.status === "done" && r.result);
  const counts = {
    review: done.filter((r) => r.result!.level === "review").length,
    ok: done.filter((r) => r.result!.level === "ok").length,
    info: done.filter((r) => r.result!.level === "info").length,
  };
  const naCount = CHECK_ORDER.filter((id) => rows[id].status === "na").length;
  const companyLine = profile?.document_suitable
    ? [profile.company_name, profile.city && profile.country ? `${profile.city}, ${profile.country}` : null].filter(Boolean).join(" · ")
    : null;

  return (
    <div className="card dd-appear">
      <div className="card-body dd-verdict" data-tone={meta.tone}>
        <div className="dd-verdict-icon"><meta.Icon size={22} /></div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="dd-verdict-label">Risk level</div>
          <div className="dd-verdict-title">{meta.title}</div>
          {companyLine && <div className="dd-verdict-company">{companyLine}</div>}
          {done.length > 0 && (
            <div className="dd-counts">
              {counts.review > 0 && <span className="dd-badge" data-tone="review">{counts.review} to review</span>}
              {counts.ok > 0 && <span className="dd-badge" data-tone="ok">{counts.ok} clear</span>}
              {counts.info > 0 && <span className="dd-badge" data-tone="info">{counts.info} info</span>}
              {naCount > 0 && <span className="dd-badge" data-tone="muted">{naCount} not applicable</span>}
            </div>
          )}
        </div>
      </div>
      <div className="card-foot dd-narrative">
        {narrative ? (
          <>
            <p className="dd-narrative-text">{narrative.text}</p>
            <p className="dd-disclaimer">
              Informational screening aid based on public data sources. This is not a legal compliance
              determination. Verify any flagged match against the authoritative source before acting on it.
            </p>
          </>
        ) : (
          <div className="row" style={{ gap: 8, color: "hsl(var(--muted-foreground))", fontSize: 13 }}>
            <span className="spinner" /> Writing summary…
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────
export function DiligenceClient() {
  const [file, setFile] = useState<File | null>(null);
  const [scenario, setScenario] = useState(DEFAULT_MOCK_SCENARIO);
  const [state, dispatch] = useReducer(reducer, initialState);
  const abortRef = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const running = state.phase === "extracting" || state.phase === "checking" || state.phase === "summarizing";

  useEffect(() => () => abortRef.current?.abort(), []);

  const handleFile = useCallback((f: File | null) => {
    abortRef.current?.abort();
    dispatch({ type: "reset" });
    setFile(f);
  }, []);

  const handleRun = useCallback(async () => {
    if (!file) return;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    dispatch({ type: "start" });

    // On narrow screens the results sit below the form.
    if (window.innerWidth <= 1100) {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    try {
      for await (const ev of runMockDiligence(scenario, ac.signal)) dispatch(ev);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        dispatch({ type: "error", message: String(err) });
      }
    }
  }, [file, scenario]);

  const showChecks = state.phase !== "idle";
  const showIdentity = state.profile?.document_suitable;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Due diligence</h1>
          <p>
            Upload a company profile or letterhead. Sparrow reads the company identity and screens it against
            VAT, entity, sanctions and registry sources.
          </p>
        </div>
      </div>

      <div className="dd-grid">
        {/* LEFT — input */}
        <div className="stack">
          <UploadCard file={file} onFile={handleFile} locked={running} />

          <div className="card">
            <div className="card-body stack-sm">
              <button className="btn btn-primary" onClick={handleRun} disabled={!file || running}>
                {running ? <span className="spinner" /> : <Play size={14} fill="currentColor" stroke="none" />}
                {running ? "Running…" : state.phase === "idle" ? "Run due diligence" : "Run again"}
              </button>
              <div className="hint">
                Checks run one after another, and each result appears as soon as it is ready.
              </div>

              {USE_MOCK && (
                <div className="dd-mock">
                  <label className="label">Demo scenario <span className="dd-mock-tag">mock data</span></label>
                  <select
                    className="select"
                    value={scenario}
                    onChange={(e) => setScenario(e.target.value)}
                    disabled={running}
                  >
                    {MOCK_SCENARIOS.map((s) => (
                      <option key={s.id} value={s.id}>{s.label}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {showIdentity && state.profile && <IdentityCard profile={state.profile} />}

          <div className="tip">
            <div className="tip-icon"><ShieldCheck size={14} /></div>
            <div>
              <div className="tip-title">Privacy by default</div>
              <div className="tip-body">
                Documents are never stored — the upload is removed as soon as processing completes.
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT — results */}
        <div className="stack" ref={resultsRef} style={{ scrollMarginTop: 76 }}>
          <VerdictCard state={state} />

          {showChecks && (
            <div className="card dd-appear">
              <div className="card-header">
                <div>
                  <div className="card-title">Checks</div>
                  <div className="card-desc">Results appear as each check completes</div>
                </div>
              </div>
              <div className="dd-rows">
                <ExtractionRow state={state} />
                {/* If the document was not assessable no check ran, so list none. */}
                {(state.planned || !state.verdict) &&
                  CHECK_ORDER.map((id) => (
                    <CheckRow key={id} id={id} row={state.rows[id]} />
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}