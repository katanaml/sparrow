"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { InputDocumentCard } from "@/components/input-document-card";
import { ResponseCard, type ResponseState } from "@/components/response-card";
import { run_inference, summarize_result } from "@/app/actions/inference";
import { log_example_selected, log_file_upload } from "@/app/actions/logging";
import { EXAMPLE_DATA, type ExampleId } from "@/lib/examples";
const EXAMPLES = [
  {
    id: "bonds_table.png",
    label: "Bonds Table",
    icon: (
      <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/>
      </svg>
    ),
  },
  {
    id: "lab_results.png",
    label: "Lab Result",
    icon: (
      <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v11"/><path d="M3 9v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9"/><line x1="3" y1="9" x2="21" y2="9"/>
      </svg>
    ),
  },
  {
    id: "bank_statement.png",
    label: "Bank Statement",
    icon: (
      <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    ),
  },
];

export default function ProcessPage() {
  const [activeExample, setActiveExample] = useState<ExampleId>("bonds_table.png");
  const [exampleFile, setExampleFile] = useState<File | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isPdf, setIsPdf] = useState(false);
  const [pageCount, setPageCount] = useState(1);
  const [query, setQuery] = useState(`[\n  {\n    "instrument_name": "str",\n    "valuation": "int"\n  }\n]`);
  const [sparrowKey, setSparrowKey] = useState("");
  const [tableExtraction, setTableExtraction] = useState(false);
  const [validationOff, setValidationOff] = useState(false);
  const savedQuery = useRef<string | null>(null);
  const savedValidationOff = useRef<boolean>(false);

  const handleTableExtraction = (enabled: boolean) => {
    if (enabled) {
      savedQuery.current = query;
      savedValidationOff.current = validationOff;
      setQuery("*");
      setValidationOff(true);
    } else {
      if (savedQuery.current !== null) setQuery(savedQuery.current);
      setValidationOff(savedValidationOff.current);
    }
    setTableExtraction(enabled);
  };
  const [modelName, setModelName] = useState("Standard model (reliable & versatile)");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [inferenceRan, setInferenceRan] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryData, setSummaryData] = useState<string | null>(null);
  const [summarizeError, setSummarizeError] = useState<string | null>(null);
  const [responseState, setResponseState] = useState<ResponseState>("empty");
  const [resultData, setResultData] = useState<object | null>(null);
  const [durationSec, setDurationSec] = useState<number | undefined>(undefined);

  const isLoadingExample = useRef(false);

  const hasUploadedBefore = useRef(false);

  const handleFileChange = useCallback((f: File | null, pages: number) => {
    setFile(f);
    setIsPdf(f?.type === "application/pdf" || false);
    setPageCount(pages);
    if (!isLoadingExample.current) {
      setExampleFile(null);
      setResponseState("empty");
      setResultData(null);
      setDurationSec(undefined);
      setSummaryData(null);
      setSummarizeError(null);
      setSubmitError(null);
      setInferenceRan(false);
      if (f && !hasUploadedBefore.current) {
        setQuery("*");
        hasUploadedBefore.current = true;
      }
      if (f) log_file_upload(f.name, `${(f.size / 1024).toFixed(1)} KB`);
    }
  }, []);

  const handleSummarize = async () => {
    setSummarizing(true);
    setSummaryData(null);
    setSummarizeError(null);
    const result = await summarize_result(resultData, sparrowKey, modelName);
    if ("error" in result) {
      setSummarizeError(result.error);
    } else {
      setSummaryData(result.summary);
    }
    setSummarizing(false);
  };

  const loadExample = async (id: ExampleId) => {
    log_example_selected(id);
    const example = EXAMPLE_DATA[id];
    const isTableExample = id === "bank_statement.png";
    setActiveExample(id);
    setQuery(example.schema);
    setResultData(example.json as object);
    setResponseState("results");
    setDurationSec(undefined);
    setSummaryData(null);
    setSummarizeError(null);
    setSubmitError(null);
    setInferenceRan(false);

    // Bank statement uses table-only extraction
    if (isTableExample) {
      savedQuery.current = example.schema;
      savedValidationOff.current = false;
      setTableExtraction(true);
      setValidationOff(true);
    } else {
      setTableExtraction(false);
      setValidationOff(false);
    }

    isLoadingExample.current = true;
    hasUploadedBefore.current = false;
    const res = await fetch(`/examples/${id}`);
    const blob = await res.blob();
    const f = new File([blob], id, { type: blob.type });
    setExampleFile(f);
    setTimeout(() => { isLoadingExample.current = false; }, 100);
  };

  useEffect(() => {
    loadExample("bonds_table.png");
  }, []);

  const handleRunInference = async () => {
    setSubmitError(null);
    setRunning(true);
    setResponseState("running");
    setResultData(null);

    const formData = new FormData();
    formData.append("file",            file!);
    formData.append("query",           query);
    formData.append("sparrowKey",      sparrowKey);
    formData.append("isPdf",           String(isPdf));
    formData.append("pageCount",       String(pageCount));
    formData.append("tableExtraction", String(tableExtraction));
    formData.append("validationOff",   String(validationOff));
    formData.append("modelName",       modelName);

    console.log("Sending request to Sparrow backend...");

    const result = await run_inference(formData);

    if ("error" in result) {
      setSubmitError(result.error);
      setResponseState("empty");
    } else {
      setResultData(result.data);
      setDurationSec(result.durationSec);
      setResponseState("results");
      setInferenceRan(true);
    }

    setRunning(false);
  };

  return (
    <>
      {/* Page heading */}
      <div className="page-head">
        <div>
          <h1>Document Extraction</h1>
          <p>Upload a document, define a schema, and extract structured data with Sparrow.</p>
        </div>
      </div>

      {/* Two-column grid */}
      <div className="grid-2">
        {/* LEFT column */}
        <div className="stack">
          {/* Input document card */}
          <InputDocumentCard
            onFileChange={handleFileChange}
            loadFile={exampleFile}
            onClear={() => setExampleFile(null)}
          />

          {/* Extraction schema card */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
                  </svg>
                  Extraction schema
                </div>
                <div className="card-desc">JSON describing the fields to extract</div>
              </div>
            </div>
            <div className="card-body" style={{ opacity: tableExtraction ? 0.45 : 1, transition: "opacity .15s" }}>
              <textarea
                className="textarea mono schema-textarea"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                spellCheck={false}
                rows={5}
                disabled={tableExtraction}
              />
              <div className="hint" style={{ marginTop: 8 }}>
                Provide a JSON array of fields with their expected types. Sparrow returns a matching JSON document.
              </div>
            </div>
          </div>

          {/* Processing options card */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.36.13.66.36.88.65"/>
                  </svg>
                  Processing options
                </div>
                <div className="card-desc">Control how the model interprets your document</div>
              </div>
            </div>
            <div className="card-body stack-sm">
              <div className="toggle-row">
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>Table-only extraction</div>
                  <div className="hint">Focus on tabular content — best for dense tables, financial reports, lab results, portfolio statements.</div>
                </div>
                <label className="switch">
                  <input type="checkbox" checked={tableExtraction} onChange={(e) => handleTableExtraction(e.target.checked)} />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <div className="toggle-row" style={{ opacity: tableExtraction ? 0.45 : 1, transition: "opacity .15s", pointerEvents: tableExtraction ? "none" : "auto" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>Schema validation</div>
                  <div className="hint">Validate extracted values against the schema types before returning.</div>
                </div>
                <label className="switch">
                  <input type="checkbox" checked={!validationOff} onChange={(e) => setValidationOff(!e.target.checked)} disabled={tableExtraction} />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <div className="stack-sm" style={{ marginTop: 6, opacity: tableExtraction ? 0.45 : 1, transition: "opacity .15s" }}>
                <div>
                  <label className="label">Vision LLM model</label>
                  <select className="select" value={modelName} onChange={(e) => setModelName(e.target.value)} disabled={tableExtraction}>
                    <option value="Standard model (reliable &amp; versatile)">Standard — reliable &amp; versatile</option>
                    <option value="Advanced model (optimized for complex documents)">Advanced — slower, higher accuracy</option>
                  </select>
                  <div className="hint" style={{ marginTop: 6 }}>
                    Standard works well for most documents. Advanced is recommended for complex forms.
                  </div>
                </div>
              </div>
              <div className="stack-sm" style={{ marginTop: 6 }}>
                <div>
                  <label className="label">Sparrow key <span style={{ color: "hsl(var(--muted-foreground))", fontWeight: 400 }}>· optional</span></label>
                  <input
                    type="password"
                    className="input"
                    placeholder="Enter your Sparrow key for extended access"
                    value={sparrowKey}
                    onChange={(e) => setSparrowKey(e.target.value)}
                  />
                  <div className="hint" style={{ marginTop: 6 }}>
                    Without a key, usage is limited to 30 calls per 6 hours and 3-page documents.{" "}
                    <a href="mailto:abaranovskis@redsamuraiconsulting.com" style={{ color: "hsl(var(--foreground))", textDecoration: "underline", textUnderlineOffset: 2 }}>
                      Contact us
                    </a>{" "}
                    for a key.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Try an example + Run extraction */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  </svg>
                  Try an example
                </div>
                <div className="card-desc">Pre-loaded sample documents</div>
              </div>
            </div>
            <div className="card-body stack-sm">
              <div className="examples">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.id}
                    className="example"
                    data-active={activeExample === ex.id ? "true" : undefined}                    onClick={() => loadExample(ex.id as ExampleId)}
                  >
                    <div className="example-name">
                      <span className="radio" data-on={activeExample === ex.id ? "true" : undefined} />                      <span style={{ color: "hsl(var(--muted-foreground))" }}>{ex.icon}</span>
                      {ex.label}
                    </div>
                  </button>
                ))}
              </div>
              <div className="submit-wrap" style={{ marginTop: 4 }}>
                <button className="btn btn-primary" onClick={handleRunInference} disabled={running}>
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" stroke="none">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  {running ? "Running…" : "Run extraction"}
                </button>
              </div>
              {submitError && (
                <div className="file-error" style={{ marginTop: 8 }}>
                  <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  {submitError}
                </div>
              )}
            </div>
          </div>

          {/* Privacy tip */}
          <div className="tip">
            <div className="tip-icon">
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div>
              <div className="tip-title">Privacy by default</div>
              <div className="tip-body">
                Documents are never stored — the upload is removed as soon as inference completes.
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT column — response */}
        <div className="stack" style={{ position: "sticky", top: 76 }}>
          <ResponseCard
            state={responseState}
            data={resultData}
            durationSec={durationSec}
            inferenceRan={inferenceRan}
            hasSummary={!!summaryData && summaryData.length > 0}
          />
          {responseState === "results" && inferenceRan && (!summaryData || summaryData.length === 0) && (
            <div className="tip" style={{ alignItems: "center" }}>
              <div className="tip-icon">
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/>
                  <path d="m5.6 5.6 2.1 2.1"/><path d="m16.3 16.3 2.1 2.1"/>
                  <path d="m5.6 18.4 2.1-2.1"/><path d="m16.3 7.7 2.1-2.1"/>
                </svg>
              </div>
              <div style={{ flex: 1 }}>
                <div className="tip-title">Summarize this result</div>
                <div className="tip-body">
                  Turn the JSON into a plain-language summary of what&apos;s in the document.
                </div>
              </div>
              <button className="btn btn-outline btn-sm" onClick={handleSummarize} disabled={summarizing} style={{ flexShrink: 0 }}>
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/>
                  <path d="m5.6 5.6 2.1 2.1"/><path d="m16.3 16.3 2.1 2.1"/>
                  <path d="m5.6 18.4 2.1-2.1"/><path d="m16.3 7.7 2.1-2.1"/>
                </svg>
                {summarizing ? "Summarizing…" : "Summarize results"}
              </button>
            </div>
          )}
          {summarizeError && (
            <div className="tip" style={{ borderColor: "hsl(var(--destructive) / 0.25)", background: "hsl(var(--destructive) / 0.05)" }}>
              <div className="tip-icon" style={{ color: "hsl(var(--destructive))" }}>
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
              </div>
              <div>
                <div className="tip-title" style={{ color: "hsl(var(--destructive))" }}>Summary failed</div>
                <div className="tip-body">{summarizeError}</div>
              </div>
            </div>
          )}
          {summaryData && (
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">
                    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/>
                      <path d="m5.6 5.6 2.1 2.1"/><path d="m16.3 16.3 2.1 2.1"/>
                      <path d="m5.6 18.4 2.1-2.1"/><path d="m16.3 7.7 2.1-2.1"/>
                    </svg>
                    Summary
                  </div>
                  <div className="card-desc">Plain-language interpretation of the extracted JSON</div>
                </div>
              </div>
              <div className="card-body">
                <div className="summary-markdown">
                  <ReactMarkdown>{summaryData}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Features footer */}
      <div className="features" style={{ marginTop: 32 }}>
        {[
          {
            icon: (
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
              </svg>
            ),
            title: "Document Extraction",
            body: "Structured data from invoices, receipts, statements, and tables — multi-page PDF, page classification, bounding-box annotation, and schema validation. No cloud dependencies.",
          },
          {
            icon: (
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
            ),
            title: "Business Rules",
            body: "Push formatting, derived fields, classification, and transformations to the LLM itself — no post-processing code, just typed schema fields with optional defaults.",
          },
          {
            icon: (
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/>
              </svg>
            ),
            title: "Sparrow Agent",
            body: "Orchestrate Vision LLM extraction with Text LLM reasoning — chain classification, extraction, and field validation with visual monitoring and error handling.",
          },
        ].map((f) => (
          <div className="card" key={f.title}>
            <div className="card-body">
              <div className="feature-icon">{f.icon}</div>
              <h4>{f.title}</h4>
              <p>{f.body}</p>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}