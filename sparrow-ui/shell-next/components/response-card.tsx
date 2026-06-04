"use client";

import { useState } from "react";

// ─── Icons ────────────────────────────────────────────────────────────────
const CodeIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
  </svg>
);
const CpuIcon = ({ w = 20 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
    <line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/>
    <line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/>
    <line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/>
    <line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>
  </svg>
);
const CheckIcon = ({ w = 11 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const CopyIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);
const DownloadIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);
const SparklesIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/>
    <path d="m5.6 5.6 2.1 2.1"/><path d="m16.3 16.3 2.1 2.1"/>
    <path d="m5.6 18.4 2.1-2.1"/><path d="m16.3 7.7 2.1-2.1"/>
  </svg>
);

// ─── JSON tokeniser ───────────────────────────────────────────────────────
interface JsonLine {
  lead: string;
  key: string | null;
  val: string;
}

function tokeniseJson(obj: unknown, indent = 2): JsonLine[] {
  const raw = JSON.stringify(obj, null, indent);
  return raw.split("\n").map((line) => {
    const lead = line.match(/^(\s*)/)![0];
    const rest = line.slice(lead.length);
    const m = rest.match(/^"([^"]+)":\s*(.*)$/);
    if (m) return { lead, key: m[1], val: m[2] };
    return { lead, key: null, val: rest };
  });
}

function renderValue(v: string) {
  if (!v) return null;
  if (v.startsWith('"')) {
    const hasTrail = v.endsWith(",") || v.endsWith("]") || v.endsWith("}");
    const trail = hasTrail ? v.slice(-1) : "";
    const body = hasTrail ? v.slice(0, -1) : v;
    return <><span className="jv-s">{body}</span>{trail && <span>{trail}</span>}</>;
  }
  if (/^(true|false)/.test(v)) return <span className="jv-b">{v}</span>;
  if (/^-?\d/.test(v))         return <span className="jv-n">{v}</span>;
  return <span>{v}</span>;
}

function JsonView({ data }: { data: unknown }) {
  const lines = tokeniseJson(data);
  return (
    <div className="json-body">
      {lines.map((l, i) => (
        <div className="json-line" key={i}>
          <span className="ln">{i + 1}</span>
          <span style={{ whiteSpace: "pre" }}>
            <span>{l.lead}</span>
            {l.key && <><span className="jk">&quot;{l.key}&quot;</span><span>: </span></>}
            {renderValue(l.val)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────
function countRecords(data: unknown): string {
  if (Array.isArray(data)) return `${data.length} records`;
  if (data && typeof data === "object") {
    const arr = Object.values(data as object).find(Array.isArray);
    if (arr) return `${(arr as unknown[]).length} records`;
  }
  return "1 record";
}

function downloadJson(data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sparrow_result.json";
  a.click();
  URL.revokeObjectURL(url);
}

function extractValid(data: unknown): boolean | null {
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const v = (data as Record<string, unknown>).valid;
    if (v === "true" || v === true)  return true;
    if (v === "false" || v === false) return false;
    if (typeof v === "string" && v.length > 0) return false; // error message string
  }
  return null; // field absent — validation was off
}

function estimateTokens(data: unknown): number {
  return Math.round(JSON.stringify(data).length / 4);
}

// ─── Props ────────────────────────────────────────────────────────────────
export type ResponseState = "empty" | "running" | "results";

interface ResponseCardProps {
  state: ResponseState;
  data?: unknown;
  durationSec?: number;
  inferenceRan?: boolean;
  hasSummary?: boolean;
}

// ─── Component ────────────────────────────────────────────────────────────
export function ResponseCard({ state, data, durationSec, inferenceRan, hasSummary }: ResponseCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const validResult = state === "results" ? extractValid(data) : null;

  return (
    <div className="card json-shell">
      {/* Header */}
      <div className="card-header">
        <div>
          <div className="card-title"><CodeIcon w={14} /> Response</div>
          <div className="card-desc">JSON output from Sparrow</div>
        </div>
        {state === "results" && (
          <div className="row" style={{ gap: 6 }}>
            {validResult === true  && <span className="badge badge-success"><CheckIcon /> Valid</span>}
            {validResult === false && <span className="badge" style={{ background: "hsl(var(--destructive) / 0.1)", borderColor: "hsl(var(--destructive) / 0.25)", color: "hsl(var(--destructive))" }}>Invalid</span>}
            {durationSec !== undefined && (
              <span className="badge badge-mono">{durationSec.toFixed(2)} s · ~{estimateTokens(data).toLocaleString()} tok</span>
            )}
          </div>
        )}
      </div>

      {/* Empty state */}
      {state === "empty" && (
        <div className="empty">
          <div className="empty-icon"><CodeIcon w={20} /></div>
          <h3>No results yet</h3>
          <p>Upload a document and define a schema, then run extraction to see structured output here.</p>
        </div>
      )}

      {/* Running state */}
      {state === "running" && (
        <div className="empty">
          <div className="empty-icon" style={{ background: "hsl(var(--primary) / 0.1)", color: "hsl(var(--primary))" }}>
            <CpuIcon w={20} />
          </div>
          <h3>Extracting…</h3>
          <p>Running Sparrow on your document.</p>
        </div>
      )}

      {/* Results state */}
      {state === "results" && data && (
        <>
          <div className="json-toolbar">
            <div className="row" style={{ gap: 4, marginLeft: "auto" }}>
              <button className="btn btn-ghost btn-icon btn-sm" title={copied ? "Copied!" : "Copy"} onClick={handleCopy}>
                <CopyIcon w={14} />
              </button>
              <button className="btn btn-ghost btn-icon btn-sm" title="Download" onClick={() => downloadJson(data)}>
                <DownloadIcon w={14} />
              </button>
            </div>
          </div>
          <JsonView data={data} />
          <div className="card-foot row between" style={{ borderTop: "1px solid hsl(var(--border))" }}>
            <span className="hint">{countRecords(data)}</span>
          </div>
        </>
      )}
    </div>
  );
}