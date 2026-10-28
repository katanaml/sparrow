// Contract between the diligence page and its data source.
//
// The page only consumes a stream of `DiligenceEvent`s. Today the stream comes
// from `mock.ts`; later the same events can be produced by an API route that
// forwards the agent results as NDJSON, and the page does not change.

export type RiskLevel =
  | "clean"
  | "review_required"
  | "incomplete"
  | "not_assessable";

export type CheckId =
  | "vies_check"
  | "gleif_check"
  | "companies_house_check"
  | "ofac_check"
  | "eu_sanctions_check"
  | "web_research_check";

// Fixed display order of the checks.
export const CHECK_ORDER: CheckId[] = [
  "vies_check",
  "gleif_check",
  "companies_house_check",
  "ofac_check",
  "eu_sanctions_check",
  "web_research_check",
];

export const CHECK_META: Record<CheckId, { title: string; subtitle: string }> = {
  vies_check: { title: "EU VIES", subtitle: "VAT number validation" },
  gleif_check: { title: "GLEIF", subtitle: "Legal entity identifier" },
  companies_house_check: { title: "UK Companies House", subtitle: "UK company register" },
  ofac_check: { title: "US lists (OFAC)", subtitle: "US consolidated screening list" },
  eu_sanctions_check: { title: "EU sanctions list", subtitle: "EU consolidated financial sanctions" },
  web_research_check: { title: "Web research", subtitle: "Company details from public web pages" },
};

export interface ExtractedProfile {
  company_name: string | null;
  street: string | null;
  postal_code: string | null;
  city: string | null;
  country: string | null;
  registration_number: string | null;
  vat_id: string | null;
  document_suitable: boolean;
}

export type FindingLevel = "ok" | "review" | "info";

export interface SanctionsMatch {
  name: string;
  kind: string; // e.g. "Entity", "enterprise"
  score: number;
  list: string;
}

export interface WebRegistryValue {
  value: string;
  source_url: string;
}

export type WebRegistryField =
  | "company_name"
  | "registration_number"
  | "vat_number"
  | "status"
  | "registered"
  | "deregistered"
  | "address"
  | "activity";

export type WebRegistry = Partial<Record<WebRegistryField, WebRegistryValue | null>>;

export interface CheckResult {
  id: CheckId;
  status: "success" | "skipped" | "failed";
  duration_sec: number;
  level?: FindingLevel; // set for success
  message: string;
  matches?: SanctionsMatch[];
  registry?: WebRegistry;
}

export type DiligenceEvent =
  // Document extraction finished.
  | { type: "extraction"; duration_sec: number; profile: ExtractedProfile }
  // Which checks will run. Everything else is shown as "not applicable".
  | { type: "plan"; run: CheckId[]; not_applicable: Partial<Record<CheckId, string>> }
  // A check has started (checks run one after another).
  | { type: "check_started"; id: CheckId }
  // A check has finished.
  | { type: "check"; result: CheckResult }
  // The deterministic verdict is known.
  | { type: "verdict"; risk_level: RiskLevel; reason?: string }
  // The LLM-written narrative is ready (usually arrives after the verdict).
  | { type: "narrative"; text: string; duration_sec: number }
  | { type: "error"; message: string };