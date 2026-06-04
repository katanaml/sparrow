"use client";

import { useState } from "react";
import { save_feedback } from "@/app/actions/feedback";

const MAX_CHARS = 1000;

const MessageIcon = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
const ShieldIcon  = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
const CheckIcon   = ({ w = 26 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
const WandIcon    = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/><path d="M17.8 11.8 19 13"/><path d="M15 9h0"/><path d="M17.8 6.2 19 5"/><path d="m3 21 9-9"/><path d="M12.2 6.2 11 5"/></svg>;
const GithubIcon  = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>;
const LayersIcon  = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>;
const CodeIcon    = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>;
const BotIcon     = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
const PlusIcon    = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const SendIcon    = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>;

function SuccessCard({ onReset }: { onReset: () => void }) {
  return (
    <div className="card success-card">
      <div className="success-icon"><CheckIcon w={26} /></div>
      <h2>Thanks for the feedback</h2>
      <p>We read every submission. If your note needs a reply, we'll be in touch within a couple of business days.</p>
      <div className="row" style={{ justifyContent: "center", gap: 8, marginTop: 24 }}>
        <button className="btn btn-outline btn-sm" onClick={onReset}><PlusIcon w={14} /> Send another</button>
        <a href="/process" className="btn btn-primary btn-sm" style={{ textDecoration: "none" }}>
          <WandIcon w={14} /> Back to Sparrow
        </a>
      </div>
    </div>
  );
}

export default function FeedbackPage() {
  const [email, setEmail] = useState("");
  const [body, setBody]   = useState("");
  const [state, setState] = useState<"form" | "sending" | "success">("form");
  const [error, setError] = useState<string | null>(null);

  const len       = body.length;
  const overLimit = len > MAX_CHARS;
  const nearLimit = len > MAX_CHARS * 0.9;
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  const canSubmit = body.trim().length >= 5 && !overLimit && emailValid && state !== "sending";

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setState("sending");
    setError(null);
    try {
      const ok = await save_feedback(email.trim(), body.trim());
      if (ok) { setState("success"); }
      else { setError("Failed to submit feedback. Please try again or email us directly."); setState("form"); }
    } catch {
      setError("Something went wrong. Please try again.");
      setState("form");
    }
  };

  const handleReset = () => { setEmail(""); setBody(""); setError(null); setState("form"); };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Feedback</h1>
          <p>Tell us what's working and what isn't. Every note goes to the engineering team.</p>
        </div>
      </div>

      {state === "success" ? <SuccessCard onReset={handleReset} /> : (
        <div className="grid-2" style={{ alignItems: "start" }}>

          {/* LEFT — form */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title"><MessageIcon w={14} /> Your feedback</div>
                <div className="card-desc">Specifics help most — what happened, what you expected, what would make Sparrow better</div>
              </div>
            </div>
            <div className="card-body stack-sm">
              <div>
                <label className="label">Message</label>
                <textarea className="textarea" placeholder="Tell us what you think about Sparrow…"
                  rows={7} value={body} maxLength={MAX_CHARS + 100}
                  onChange={(e) => setBody(e.target.value)} />
                <div className="row between" style={{ marginTop: 6 }}>
                  <span className="hint">{body.trim().length < 5 ? "Min 5 characters" : "Markdown is supported"}</span>
                  <span className={overLimit ? "char-count bad" : nearLimit ? "char-count warn" : "char-count"}>{len} / {MAX_CHARS}</span>
                </div>
              </div>
              <div>
                <label className="label">Email address</label>
                <input className="input" type="email" placeholder="you@example.com"
                  value={email} onChange={(e) => setEmail(e.target.value)} />
                <div className="hint" style={{ marginTop: 6, color: email.length > 0 && !emailValid ? "hsl(var(--destructive))" : undefined }}>
                  {email.length > 0 && !emailValid ? "Please enter a valid email address." : "Required — we'll only use this to follow up on your feedback, never for marketing."}
                </div>
              </div>
              {error && (
                <div className="file-error">
                  <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  {error}
                </div>
              )}
            </div>
            <div className="card-foot row between" style={{ flexWrap: "wrap", gap: 8 }}>
              <div className="privacy footer-desktop">
                <ShieldIcon w={14} />
                <span>Stored in our self-hosted DB · GDPR friendly</span>
              </div>
              <div className="row" style={{ gap: 8, marginLeft: "auto" }}>
                <button className="btn btn-outline btn-sm" onClick={() => { setBody(""); setEmail(""); setError(null); }}>Clear</button>
                <button className="btn btn-primary btn-sm" disabled={!canSubmit} onClick={handleSubmit}>
                  {state === "sending" ? <><span className="spinner" /> Sending…</> : <><SendIcon w={14} /> Submit feedback</>}
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT — info */}
          <div className="stack">
            <div className="card">
              <div className="card-body">
                <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                  <div className="feature-icon" style={{ marginTop: 2, flexShrink: 0 }}><GithubIcon w={16} /></div>
                  <div>
                    <h4 style={{ margin: "0 0 6px" }}>Your feedback shapes Sparrow</h4>
                    <p style={{ margin: "0 0 10px", fontSize: 13.5, color: "hsl(var(--muted-foreground))", lineHeight: 1.6 }}>
                      Sparrow is open source and actively developed. Feature requests and bug reports directly influence the roadmap. The most-requested items ship first.
                    </p>
                    <p style={{ margin: 0, fontSize: 13.5, color: "hsl(var(--muted-foreground))", lineHeight: 1.6 }}>
                      For bug reports with reproduction steps,{" "}
                      <a href="https://github.com/katanaml/sparrow/issues" target="_blank" rel="noopener"
                        style={{ color: "hsl(var(--foreground))", textDecoration: "underline", textUnderlineOffset: 2 }}>
                        open a GitHub issue
                      </a>{" "}— it gives the full context needed to fix things fast.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="tip">
              <div className="tip-icon"><ShieldIcon w={14} /></div>
              <div>
                <div className="tip-title">Privacy by default</div>
                <div className="tip-body">Your feedback is stored on our self-hosted infrastructure. Email is never shared or used for marketing.</div>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Features footer */}
      <div className="features" style={{ marginTop: 32 }}>
        {[
          { icon: <LayersIcon />, title: "Document Extraction", body: "Structured data from invoices, receipts, statements, and tables — multi-page PDF, page classification, bounding-box annotation, and schema validation. No cloud dependencies." },
          { icon: <CodeIcon />,   title: "Business Rules",      body: "Push formatting, derived fields, classification, and transformations to the LLM itself — no post-processing code, just typed schema fields with optional defaults." },
          { icon: <BotIcon />,    title: "Sparrow Agent",       body: "Orchestrate Vision LLM extraction with Text LLM reasoning — chain classification, extraction, and field validation with visual monitoring and error handling." },
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