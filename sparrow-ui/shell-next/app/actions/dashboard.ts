"use server";

import { get_inference_logs, get_unique_users_by_country, type InferenceLog } from "@/lib/db_pool";

// ─── Types ────────────────────────────────────────────────────────────────
export interface KpiData {
  totalCount:        number;
  successCount:      number;
  failureCount:      number;
  successPct:        number;
  avgDuration:       number;
  topModel:          string;
  topModelCount:     number;
  topModelSharePct:  number;
}

export interface ScatterPoint {
  t:    number;   // timestamp ms
  y:    number;   // duration seconds
  size: number;   // page count
}

export interface BarItem {
  name:  string;
  value: number;
}

export interface SparkData {
  total:    number[];
  success:  number[];
  duration: number[];
  model:    number[];
}

export interface DashboardData {
  kpi:              KpiData;
  scatterEvents:    ScatterPoint[];
  docSizeBars:      BarItem[];
  modelUsageBars:   BarItem[];
  requestsByCountry: BarItem[];
  usersByCountry:   BarItem[];
  spark:            SparkData;
  dateRange:        string;
  isEmpty:          boolean;
}

// ─── Model name normalisation (matches Python dashboard.py) ───────────────
function friendlyModel(name: string): string {
  if (!name) return name;
  if (name.includes("Mistral") || name.includes("Ministral")) return "Standard model";
  if (name.includes("Qwen") || name.includes("gemma"))        return "Advanced model";
  if (name.includes("Dots"))                                   return "Table model";
  return name;
}

// ─── Date range label ─────────────────────────────────────────────────────
function dateRangeLabel(logs: InferenceLog[]): string {
  if (!logs.length) return "";
  const dates = logs.map((l) => new Date(l.log_date).getTime());
  const min = new Date(Math.min(...dates));
  const max = new Date(Math.max(...dates));
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `${fmt(min)} – ${fmt(max)}`;
}

// ─── Spark series helpers ─────────────────────────────────────────────────
function dailySpark(logs: InferenceLog[], key: "count" | "duration" | "model", modelName?: string): number[] {
  if (!logs.length) return Array(7).fill(0);
  const byDay: Record<string, number[]> = {};
  logs.forEach((l) => {
    const day = new Date(l.log_date).toISOString().slice(0, 10);
    if (!byDay[day]) byDay[day] = [];
    if (key === "count")    byDay[day].push(1);
    if (key === "duration") byDay[day].push(l.inference_duration ?? 0);
    if (key === "model")    byDay[day].push(friendlyModel(l.model_name) === modelName ? 1 : 0);
  });
  const days = Object.keys(byDay).sort();
  return days.map((d) => {
    const vals = byDay[d];
    if (key === "duration") return vals.reduce((a, b) => a + b, 0) / vals.length;
    return vals.reduce((a, b) => a + b, 0);
  });
}

// ─── get_dashboard_data ───────────────────────────────────────────────────
export async function get_dashboard_data(period = "1week"): Promise<DashboardData> {
  const [logs, uniqueUsers] = await Promise.all([
    get_inference_logs(period),
    get_unique_users_by_country(period),
  ]);

  if (!logs.length) {
    return {
      kpi: { totalCount: 0, successCount: 0, failureCount: 0, successPct: 0, avgDuration: 0, topModel: "No data", topModelCount: 0, topModelSharePct: 0 },
      scatterEvents: [], docSizeBars: [], modelUsageBars: [],
      requestsByCountry: [], usersByCountry: [],
      spark: { total: Array(7).fill(0), success: Array(7).fill(100), duration: Array(7).fill(0), model: Array(7).fill(0) },
      dateRange: "", isEmpty: true,
    };
  }

  // ── KPIs ──────────────────────────────────────────────────────────────
  const totalCount    = logs.length;
  const successCount  = logs.filter((l) => l.inference_duration != null).length;
  const failureCount  = totalCount - successCount;
  const successPct    = totalCount > 0 ? (successCount / totalCount) * 100 : 0;
  const avgDuration   = successCount > 0
    ? logs.reduce((s, l) => s + (l.inference_duration ?? 0), 0) / successCount
    : 0;

  // Top model by friendly name
  const modelCounts: Record<string, number> = {};
  logs.forEach((l) => {
    const name = friendlyModel(l.model_name);
    modelCounts[name] = (modelCounts[name] ?? 0) + 1;
  });
  const sortedModels = Object.entries(modelCounts).sort((a, b) => b[1] - a[1]);
  const topModel      = sortedModels[0]?.[0] ?? "No data";
  const topModelCount = sortedModels[0]?.[1] ?? 0;
  const topModelSharePct = totalCount > 0 ? (topModelCount / totalCount) * 100 : 0;

  // ── Scatter events ────────────────────────────────────────────────────
  const scatterEvents: ScatterPoint[] = logs
    .filter((l) => l.inference_duration != null && l.page_count != null)
    .map((l) => ({
      t:    new Date(l.log_date).getTime(),
      y:    l.inference_duration,
      size: l.page_count,
    }));

  // ── Duration by doc size ──────────────────────────────────────────────
  const durationByPage: Record<number, number[]> = {};
  logs.filter((l) => l.inference_duration != null).forEach((l) => {
    const p = l.page_count ?? 1;
    if (!durationByPage[p]) durationByPage[p] = [];
    durationByPage[p].push(l.inference_duration);
  });
  const docSizeBars: BarItem[] = Object.entries(durationByPage)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([pages, durations]) => ({
      name:  `${pages} page${Number(pages) > 1 ? "s" : ""}`,
      value: Math.round((durations.reduce((a, b) => a + b, 0) / durations.length) * 100) / 100,
    }));

  // ── Model usage ───────────────────────────────────────────────────────
  const modelUsageBars: BarItem[] = sortedModels.map(([name, count]) => ({ name, value: count }));

  // ── Country bars ──────────────────────────────────────────────────────
  const countryCounts: Record<string, number> = {};
  logs.forEach((l) => {
    if (l.country_name) countryCounts[l.country_name] = (countryCounts[l.country_name] ?? 0) + 1;
  });
  const requestsByCountry: BarItem[] = Object.entries(countryCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));

  const usersByCountry: BarItem[] = uniqueUsers.map((u) => ({
    name:  u.country_name,
    value: u.unique_users,
  }));

  // ── Sparklines ────────────────────────────────────────────────────────
  const byDaySuccess: Record<string, { total: number; success: number }> = {};
  logs.forEach((l) => {
    const day = new Date(l.log_date).toISOString().slice(0, 10);
    if (!byDaySuccess[day]) byDaySuccess[day] = { total: 0, success: 0 };
    byDaySuccess[day].total++;
    if (l.inference_duration != null) byDaySuccess[day].success++;
  });
  const successSpark = Object.keys(byDaySuccess).sort().map((d) =>
    Math.round((byDaySuccess[d].success / byDaySuccess[d].total) * 100)
  );

  const byDayModel: Record<string, { total: number; topModel: number }> = {};
  logs.forEach((l) => {
    const day = new Date(l.log_date).toISOString().slice(0, 10);
    if (!byDayModel[day]) byDayModel[day] = { total: 0, topModel: 0 };
    byDayModel[day].total++;
    if (friendlyModel(l.model_name) === topModel) byDayModel[day].topModel++;
  });
  const modelSpark = Object.keys(byDayModel).sort().map((d) =>
    Math.round((byDayModel[d].topModel / byDayModel[d].total) * 100)
  );

  const spark: SparkData = {
    total:    dailySpark(logs, "count"),
    success:  successSpark,
    duration: dailySpark(logs, "duration"),
    model:    modelSpark,
  };

  return {
    kpi: { totalCount, successCount, failureCount, successPct, avgDuration, topModel, topModelCount, topModelSharePct },
    scatterEvents, docSizeBars, modelUsageBars,
    requestsByCountry, usersByCountry,
    spark, dateRange: dateRangeLabel(logs), isEmpty: false,
  };
}