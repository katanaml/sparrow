"use client";

import { useState, useEffect, useRef, useLayoutEffect } from "react";
import { get_dashboard_data, type DashboardData, type BarItem, type ScatterPoint } from "@/app/actions/dashboard";

// ─── Icons ────────────────────────────────────────────────────────────────
const BarChartIcon  = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>;
const CheckIcon     = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
const CpuIcon       = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>;
const SparklesIcon  = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/><path d="m5.6 5.6 2.1 2.1"/><path d="m16.3 16.3 2.1 2.1"/><path d="m5.6 18.4 2.1-2.1"/><path d="m16.3 7.7 2.1-2.1"/></svg>;
const FileIcon      = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>;
const BotIcon       = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
const MaximizeIcon  = ({ w = 14 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>;
const LayersIcon    = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>;
const CodeIcon      = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>;
const LoaderIcon    = ({ w = 16 }: { w?: number }) => <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>;

// ─── Sparkline ────────────────────────────────────────────────────────────
function Sparkline({ data, color = "hsl(var(--primary))", height = 36 }: { data: number[]; color?: string; height?: number }) {
  const W = 240, H = height;
  const dataMax = Math.max(...data), dataMin = Math.min(...data);
  const flat = dataMax === dataMin;
  const span = Math.max(flat ? 1 : dataMax - Math.min(dataMin, 0), 1);
  const min  = flat ? dataMin : Math.min(dataMin, 0);
  const step = W / Math.max(data.length - 1, 1);
  const pts  = data.map((v, i) => [i * step, flat ? H / 2 : H - ((v - min) / span) * (H - 6) - 3] as [number, number]);
  const path = pts.map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`)).join(" ");
  const area = `${path} L ${W} ${H} L 0 ${H} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height, width: "100%", display: "block" }}>
      {!flat && <path d={area} fill={color} fillOpacity="0.12" />}
      <path d={path} fill="none" stroke={color} strokeWidth={flat ? 1 : 1.5}
        strokeLinejoin="round" strokeLinecap="round"
        strokeDasharray={flat ? "3 3" : ""} strokeOpacity={flat ? 0.5 : 1} />
    </svg>
  );
}

// ─── BarList ──────────────────────────────────────────────────────────────
function BarList({ data, color = "hsl(var(--primary))", valueFormatter, showPercent = true }: {
  data: BarItem[];
  color?: string;
  valueFormatter?: (v: number) => string;
  showPercent?: boolean;
}) {
  const max   = Math.max(...data.map((d) => d.value), 1);
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="barlist">
      {data.map((d, i) => {
        const w   = Math.max((d.value / max) * 100, 1);
        const pct = total ? ((d.value / total) * 100).toFixed(1) : "0";
        return (
          <div className="barlist-row" key={i}>
            <span className="bg" style={{ width: `${w}%`, background: `color-mix(in srgb, ${color} 22%, transparent)` }} />
            <span className="label">{d.name}</span>
            <span className="value">
              {valueFormatter ? valueFormatter(d.value) : d.value}
              {showPercent && <span className="pct">{pct}%</span>}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─── ScatterChart ─────────────────────────────────────────────────────────
const PAGE_COLORS = [
  "hsl(142 71% 45%)",   // 1 page  — primary green
  "hsl(200 80% 48%)",   // 2 pages — blue
  "hsl(262 83% 58%)",   // 3 pages — purple
  "hsl(38 92% 50%)",    // 4 pages — amber
  "hsl(0 72% 55%)",     // 5+ pages — red
];

function pageColor(size: number): string {
  return PAGE_COLORS[Math.min(size - 1, PAGE_COLORS.length - 1)];
}

function ScatterChart({ data, height = 340 }: {
  data: ScatterPoint[];
  height?: number;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(0);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; d: ScatterPoint } | null>(null);

  useLayoutEffect(() => {
    if (!wrapRef.current) return;
    const update = () => { if (wrapRef.current) setW(wrapRef.current.clientWidth); };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  if (!data.length) return (
    <div ref={wrapRef} style={{ height, display: "grid", placeItems: "center" }}>
      <span className="hint">No events to display</span>
    </div>
  );

  if (!W) return <div ref={wrapRef} style={{ width: "100%", height }} />;

  const H = height;
  const padL = 56, padR = 24, padT = 16, padB = 36;
  const xs   = data.map((d) => d.t);
  const ys   = data.map((d) => d.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const rawMax = Math.max(...ys, 50);
  const yStep = rawMax <= 100 ? 25 : rawMax <= 300 ? 50 : rawMax <= 600 ? 100 : rawMax <= 1200 ? 200 : 300;
  const yMax = Math.ceil(rawMax / yStep) * yStep;
  const xSpan = Math.max(xMax - xMin, 1);
  const sx = (t: number) => padL + ((t - xMin) / xSpan) * (W - padL - padR);
  const sy = (v: number) => padT + (1 - v / yMax) * (H - padT - padB);
  const yTicks: number[] = [];
  for (let v = 0; v <= yMax; v += yStep) yTicks.push(v);
  const xTicks: number[] = [];
  const dayMs = 24 * 3600 * 1000;
  const startDay = Math.ceil(xMin / dayMs) * dayMs;
  const allDays: number[] = [];
  for (let t = startDay; t <= xMax; t += dayMs) allDays.push(t);
  // Show fewer ticks on narrow screens — aim for max ~6 ticks
  const tickEvery = Math.max(1, Math.ceil(allDays.length / 6));
  allDays.forEach((t, i) => { if (i % tickEvery === 0) xTicks.push(t); });
  const sizeFor = (p: number) => 6 + Math.min(p, 5) * 3.5;
  const fmtDate = (t: number) => { const d = new Date(t); return `${String(d.getMonth()+1).padStart(2,"0")}/${String(d.getDate()).padStart(2,"0")}`; };

  return (
    <div ref={wrapRef} style={{ width: "100%", position: "relative" }}>
      <svg width={W} height={H} style={{ display: "block" }}>
        {yTicks.map((v, i) => (
          <g key={`y${i}`}>
            <line className="grid-line-dash" x1={padL} y1={sy(v)} x2={W - padR} y2={sy(v)} />
            <text className="axis-text" x={padL - 10} y={sy(v) + 3} textAnchor="end">{v}</text>
          </g>
        ))}
        {xTicks.map((t, i) => (
          <g key={`x${i}`}>
            <line className="grid-line" x1={sx(t)} y1={H - padB} x2={sx(t)} y2={H - padB + 4} />
            <text className="axis-text" x={sx(t)} y={H - padB + 18} textAnchor="middle">{fmtDate(t)}</text>
          </g>
        ))}
        <line className="grid-line" x1={padL} y1={H - padB} x2={W - padR} y2={H - padB} />
        <text className="axis-text" x={14} y={(H - padB + padT) / 2} textAnchor="middle"
          transform={`rotate(-90 14 ${(H - padB + padT) / 2})`}>Duration (s)</text>
        {data.map((d, i) => {
          const color = pageColor(d.size);
          return (
            <circle key={i} cx={sx(d.t)} cy={sy(d.y)} r={sizeFor(d.size)}
              fill={color} fillOpacity="0.25" stroke={color} strokeWidth="1.5"
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setTooltip({ x: sx(d.t), y: sy(d.y), d })}
              onMouseLeave={() => setTooltip(null)}
            />
          );
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && (() => {
        const date = new Date(tooltip.d.t).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        const tipW = 160;
        const left = tooltip.x + tipW + 12 > W ? tooltip.x - tipW - 8 : tooltip.x + 12;
        const top  = Math.max(0, tooltip.y - 36);
        return (
          <div style={{
            position: "absolute", left, top, width: tipW, pointerEvents: "none",
            background: "hsl(var(--card))", border: "1px solid hsl(var(--border))",
            borderRadius: "var(--radius)", padding: "8px 10px", zIndex: 10,
            boxShadow: "0 4px 12px rgb(0 0 0 / 0.12)",
          }}>
            <div style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", marginBottom: 4 }}>{date}</div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{tooltip.d.y.toFixed(1)} s</div>
            <div style={{ fontSize: 12, color: "hsl(var(--muted-foreground))", marginTop: 2 }}>
              {tooltip.d.size} page{tooltip.d.size > 1 ? "s" : ""}
            </div>
          </div>
        );
      })()}

      {/* Legend */}
      <div style={{ display: "flex", gap: 16, padding: "8px 56px 4px", flexWrap: "wrap" }}>
        {Array.from(new Set(data.map((d) => d.size))).sort().map((size) => (
          <div key={size} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "hsl(var(--muted-foreground))" }}>
            <svg width={14} height={14}><circle cx={7} cy={7} r={5} fill={pageColor(size)} fillOpacity="0.3" stroke={pageColor(size)} strokeWidth="1.5" /></svg>
            {size} page{size > 1 ? "s" : ""}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div style={{ padding: "48px 0", display: "grid", placeItems: "center", color: "hsl(var(--muted-foreground))", textAlign: "center", gap: 8 }}>
      <BarChartIcon w={28} />
      <p style={{ margin: 0, fontSize: 14 }}>No data available for the selected period</p>
    </div>
  );
}

// ─── Constants ────────────────────────────────────────────────────────────
const PERIODS = [
  { id: "1week",   label: "1 week"   },
  { id: "2weeks",  label: "2 weeks"  },
  { id: "1month",  label: "1 month"  },
  { id: "6months", label: "6 months" },
  { id: "all",     label: "All time" },
];

// ─── Page ─────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [period, setPeriod]   = useState("1week");
  const [data, setData]       = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    get_dashboard_data(period).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [period]);

  const kpi  = data?.kpi;
  const empty = data?.isEmpty ?? false;

  return (
    <>
      {/* Page heading */}
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p>Sparrow usage patterns — processing volume, model distribution, latency, and geographical reach.</p>
        </div>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="filter-bar-left">
          <span className="filter-label">Time period</span>
          <div className="seg">
            {PERIODS.map((p) => (
              <button key={p.id} data-active={period === p.id ? "true" : undefined}
                onClick={() => setPeriod(p.id)} disabled={loading}>
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          {loading
            ? <span className="hint" style={{ display: "flex", alignItems: "center", gap: 6 }}><LoaderIcon w={12} /> Loading…</span>
            : data?.dateRange ? <span className="hint mono">{data.dateRange}</span> : null
          }
        </div>
      </div>

      <div className="stack">
        {/* KPI row */}
        <div className="kpi-grid">
          {[
            {
              label: "Total Inferences",
              value: kpi ? String(kpi.totalCount) : "—",
              sub:   kpi ? `last period` : "",
              icon:  BarChartIcon,
              spark: data?.spark.total,
              color: "hsl(var(--primary))",
            },
            {
              label: "Success Rate",
              value: kpi ? `${kpi.successPct.toFixed(1)}%` : "—",
              sub:   kpi ? `${kpi.successCount} OK · ${kpi.failureCount} failed` : "",
              icon:  CheckIcon,
              spark: data?.spark.success,
              color: "hsl(142 70% 32%)",
            },
            {
              label: "Avg. Duration",
              value: kpi ? `${kpi.avgDuration.toFixed(2)}s` : "—",
              sub:   "per inference",
              icon:  CpuIcon,
              spark: data?.spark.duration,
              color: "hsl(38 92% 50%)",
            },
            {
              label: "Top Model",
              value: kpi ? kpi.topModel.replace(" model", "") : "—",
              sub:   kpi ? `${kpi.topModelCount} uses · ${kpi.topModelSharePct.toFixed(0)}% share` : "",
              icon:  SparklesIcon,
              spark: data?.spark.model,
              color: "hsl(262 83% 58%)",
            },
          ].map((k) => (
            <div className="card kpi" key={k.label}>
              <div className="kpi-head">
                <span>{k.label}</span>
                <span className="icon"><k.icon w={14} /></span>
              </div>
              <div className="kpi-value">{k.value}</div>
              <div className="kpi-foot"><span>{k.sub}</span></div>
              <div className="kpi-spark">
                {k.spark
                  ? <Sparkline data={k.spark} color={k.color} height={36} />
                  : <div style={{ height: 36, background: "hsl(var(--muted) / 0.4)", borderRadius: 4 }} />
                }
              </div>
            </div>
          ))}
        </div>

        {/* Duration + Model usage */}
        {empty ? <EmptyState /> : (
          <>
            <div className="grid-2-eq">
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title"><FileIcon w={14} /> Avg Duration by Page Count</div>
                    <div className="card-desc">Average seconds per inference, grouped by page count</div>
                  </div>
                </div>
                <div className="card-body">
                  {data?.docSizeBars.length
                    ? <BarList data={data.docSizeBars} color="hsl(var(--primary))"
                        valueFormatter={(v) => `${v.toFixed(2)} s`} showPercent={false} />
                    : <span className="hint">No data</span>
                  }
                  {data && <div className="hint" style={{ marginTop: 12 }}>Based on {data.kpi.successCount} successful inferences</div>}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title"><CpuIcon w={14} /> Inference by Model</div>
                    <div className="card-desc">Share of inferences by Vision LLM model</div>
                  </div>
                </div>
                <div className="card-body">
                  {data?.modelUsageBars.length
                    ? <BarList data={data.modelUsageBars} color="hsl(262 83% 58%)"
                        valueFormatter={(v) => `${v} ${v === 1 ? "use" : "uses"}`} showPercent />
                    : <span className="hint">No data</span>
                  }
                  {data && <div className="hint" style={{ marginTop: 12 }}>Based on {data.kpi.totalCount} total inferences</div>}
                </div>
              </div>
            </div>

            {/* Scatter chart */}
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title"><BarChartIcon w={14} /> Inference Events</div>
                  <div className="card-desc">Duration vs time — bubble size encodes page count</div>
                </div>
                <div className="row" style={{ gap: 6 }}>
                  <span className="hint mono">
                    <span className="footer-desktop">{data?.scatterEvents.length ?? 0} events</span>
                    <span className="footer-mobile">{data?.scatterEvents.length ?? 0} ev.</span>
                  </span>
                </div>
              </div>
              <div className="card-body chart">
                <ScatterChart data={data?.scatterEvents ?? []} height={340} />
              </div>
            </div>

            {/* Country bars */}
            <div className="grid-2-eq">
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title"><BarChartIcon w={14} /> Inference Requests by Country</div>
                    <div className="card-desc">Distribution of total calls</div>
                  </div>
                </div>
                <div className="card-body">
                  {data?.requestsByCountry.length ? (
                    <div style={{ maxHeight: data.requestsByCountry.length > 10 ? 320 : "none", overflowY: data.requestsByCountry.length > 10 ? "auto" : "visible" }}>
                      <BarList data={data.requestsByCountry} color="hsl(var(--primary))" showPercent />
                    </div>
                  ) : <span className="hint">No data</span>}
                  {data && (
                    <div className="hint" style={{ marginTop: 12, display: "flex", justifyContent: "space-between" }}>
                      <span>Based on {data.kpi.totalCount} total inferences</span>
                      <span>{data.requestsByCountry.length} countries</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title"><BotIcon w={14} /> Unique Users by Country</div>
                    <div className="card-desc">Distribution by IP address</div>
                  </div>
                </div>
                <div className="card-body">
                  {data?.usersByCountry.length ? (
                    <div style={{ maxHeight: data.usersByCountry.length > 10 ? 320 : "none", overflowY: data.usersByCountry.length > 10 ? "auto" : "visible" }}>
                      <BarList data={data.usersByCountry} color="hsl(262 83% 58%)" showPercent />
                    </div>
                  ) : <span className="hint">No data</span>}
                  {data && (
                    <div className="hint" style={{ marginTop: 12, display: "flex", justifyContent: "space-between" }}>
                      <span>Based on {data.usersByCountry.reduce((s, d) => s + d.value, 0)} distinct IPs</span>
                      <span>{data.usersByCountry.length} countries</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Features footer */}
      <div className="features" style={{ marginTop: 32 }}>
        {[
          { icon: <LayersIcon />, title: "Document Extraction", body: "Structured data from invoices, receipts, statements, and tables — multi-page PDF, page classification, bounding-box annotation, and schema validation. No cloud dependencies." },
          { icon: <CodeIcon />,   title: "Business Rules",      body: "Push formatting, derived fields, classification, and transformations to the LLM itself — no post-processing code, just typed schema fields with optional defaults." },
          { icon: <BotIcon w={16} />, title: "Sparrow Agent",  body: "Orchestrate Vision LLM extraction with Text LLM reasoning — chain classification, extraction, and field validation with visual monitoring and error handling." },
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