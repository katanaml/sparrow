// MOCK DATA SOURCE — used until the page is wired to the diligence API.
//
// `runMockDiligence` yields the same `DiligenceEvent`s a real API stream will
// yield, with short fake delays. The scenario data is copied from real runs of
// the agent, so messages and shapes match what the backend returns.
//
// When the API is added, replace the call in components/diligence-client.tsx and delete
// this file (and the "demo scenario" select).

import {
  CHECK_ORDER,
  type CheckId,
  type CheckResult,
  type DiligenceEvent,
  type ExtractedProfile,
  type RiskLevel,
  type WebRegistry,
} from "./diligence-types";

interface Scenario {
  id: string;
  label: string;
  profile: ExtractedProfile;
  not_applicable: Partial<Record<CheckId, string>>;
  results: CheckResult[]; // in run order
  verdict: RiskLevel;
  reason?: string;
  narrative: string;
  extraction_sec: number;
  narrative_sec: number;
}

const NO_VAT = "No VAT number on the document.";
const NOT_UK = "Applies to UK companies only.";

const OFAC_OK =
  "No name matches were found on the US Consolidated Screening List (OFAC SDN and other US lists) (data downloaded 2026-10-16).";
const EU_OK =
  "No name matches were found on the EU Consolidated Financial Sanctions List (list published 2026-10-15, data downloaded 2026-10-16).";

const ok = (id: CheckId, duration_sec: number, message: string): CheckResult => ({
  id, status: "success", level: "ok", duration_sec, message,
});

const web = (duration_sec: number, registry: WebRegistry): CheckResult => ({
  id: "web_research_check",
  status: "success",
  level: "info",
  duration_sec,
  message: "Company details from web sources (unverified).",
  registry,
});

const SAP_URL = "https://www.sap.com/about/legal/impressum-se.html";
const SAP_REG_URL = "https://www.online-handelsregister.de/handelsregisterauszug/bw/Mannheim/HRB/719915/SAP-SE";
const ALROSA_NOTICE = "https://alrosa.ru/upload/iblock/d4b/1148-Notice-of-amending-correcting-the-information-in-the-notice-published-earlier-in-the-Newsline1.pdf";
const ALROSA_REPORT = "https://www.alrosa.ru/upload/iblock/bf4/ALROSA-6M2021-ENG.pdf";
const CBONDS = "https://cbonds.com/company/18";
const CH_URL = "https://find-and-update.company-information.service.gov.uk/company/00041424";

const SCENARIOS: Scenario[] = [
  {
    id: "sap",
    label: "SAP SE — clean",
    profile: {
      company_name: "SAP SE", street: "Dietmar-Hopp-Allee 16", postal_code: "69190", city: "Walldorf",
      country: "Germany", registration_number: "HRB 719915", vat_id: "DE143454214", document_suitable: true,
    },
    not_applicable: { companies_house_check: NOT_UK },
    results: [
      ok("vies_check", 0.6, "VAT number DE143454214 is valid according to VIES."),
      ok("gleif_check", 0.4, "A matching LEI record was found by registration number: SAP SE, entity status ACTIVE."),
      ok("ofac_check", 0.3, OFAC_OK),
      ok("eu_sanctions_check", 0.2, EU_OK),
      web(93.4, {
        company_name: { value: "SAP SE", source_url: SAP_URL },
        registration_number: { value: "HRB 719915", source_url: SAP_URL },
        vat_number: { value: "DE 143454214", source_url: SAP_URL },
        status: { value: "active", source_url: SAP_REG_URL },
        registered: { value: "07.07.2014", source_url: SAP_REG_URL },
        address: { value: "Dietmar-Hopp-Allee 16, 69190 Walldorf", source_url: SAP_REG_URL },
      }),
    ],
    verdict: "clean",
    narrative:
      "The overall risk level for SAP SE is clean. All primary screening checks returned clean results, indicating no issues were found. The GLEIF legal entity registry confirmed an active LEI record matching the registration number. The EU VIES system validated the VAT number DE143454214. No name matches were found on the US Consolidated Screening List, which was downloaded on 2026-10-16. No name matches were found on the EU Consolidated Financial Sanctions List, which was published on 2026-10-15 and downloaded on 2026-10-16. Web research provided unverified details including the company name, registration number, VAT number, active status, registration date of 07.07.2014, and address. The UK Companies House check was not run.",
    extraction_sec: 32.0,
    narrative_sec: 40.9,
  },
  {
    id: "unilever",
    label: "Unilever PLC — clean (UK)",
    profile: {
      company_name: "Unilever PLC", street: "100 Victoria Embankment", postal_code: "EC4Y 0DY", city: "London",
      country: "United Kingdom", registration_number: "00041424", vat_id: null, document_suitable: true,
    },
    not_applicable: { vies_check: NO_VAT },
    results: [
      ok("gleif_check", 1.1, "A matching LEI record was found by registration number: UNILEVER PLC, entity status ACTIVE."),
      ok("companies_house_check", 1.7, "UK Companies House confirms company number 00041424 is UNILEVER PLC, status active."),
      ok("ofac_check", 0.2, OFAC_OK),
      ok("eu_sanctions_check", 0.1, EU_OK),
      web(73.5, {
        company_name: { value: "UNILEVER PLC", source_url: CH_URL },
        registration_number: { value: "00041424", source_url: CH_URL },
        status: { value: "active", source_url: CH_URL },
        registered: { value: "21 June 1894", source_url: CH_URL },
        address: { value: "Port Sunlight, Wirral, Merseyside, CH62 4ZD", source_url: CH_URL },
        activity: { value: "70100 - Activities of head offices", source_url: CH_URL },
      }),
    ],
    verdict: "clean",
    narrative:
      "The overall risk level for Unilever PLC is clean. The GLEIF legal entity registry and UK Companies House both confirm the company is active with registration number 00041424. No name matches were found on the US Consolidated Screening List, which was downloaded on 2026-10-16. Similarly, no matches were found on the EU Consolidated Financial Sanctions List, published on 2026-10-15 and downloaded on 2026-10-16. Unverified web research indicates the company is active, registered in 1894, and located in Port Sunlight, though these details are not confirmed by official records. The EU VIES VAT number validation check was not run.",
    extraction_sec: 31.4,
    narrative_sec: 38.3,
  },
  {
    id: "alrosa",
    label: "PJSC Alrosa — sanctions matches",
    profile: {
      company_name: "PJSC ALROSA", street: "Lenin Street 6", postal_code: "678174", city: "Mirny",
      country: "Russia", registration_number: "OGRN 1021400967092", vat_id: null, document_suitable: true,
    },
    not_applicable: { vies_check: NO_VAT, companies_house_check: NOT_UK },
    results: [
      ok("gleif_check", 1.2, 'A matching LEI record was found by registration number: АКЦИОНЕРНАЯ КОМПАНИЯ "АЛРОСА" (ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО), entity status ACTIVE.'),
      {
        id: "ofac_check", status: "success", level: "review", duration_sec: 0.2,
        message: "1 potential name match on the US Consolidated Screening List (OFAC SDN and other US lists) (data downloaded 2026-10-16), highest score 1.0.",
        matches: [{ name: "PUBLIC JOINT STOCK COMPANY ALROSA", kind: "Entity", score: 1.0, list: "Specially Designated Nationals (SDN) - Treasury Department" }],
      },
      {
        id: "eu_sanctions_check", status: "success", level: "review", duration_sec: 0.1,
        message: "1 potential name match on the EU Consolidated Financial Sanctions List (list published 2026-10-15, data downloaded 2026-10-16), highest score 1.0.",
        matches: [{ name: "PJSC Alrosa", kind: "enterprise", score: 1.0, list: "EU Consolidated Financial Sanctions List (FSF) - European Commission" }],
      },
      web(85.9, {
        company_name: { value: "Public Joint Stock Company ALROSA", source_url: ALROSA_NOTICE },
        registration_number: { value: "1021400967092", source_url: ALROSA_NOTICE },
        status: { value: "active", source_url: CBONDS },
        registered: { value: "17 July 2002", source_url: ALROSA_REPORT },
        address: { value: "6, Lenina St., Mirny, Republic of Sakha (Yakutia), Russian Federation", source_url: ALROSA_NOTICE },
        activity: { value: "diamond mining", source_url: CBONDS },
      }),
    ],
    verdict: "review_required",
    narrative:
      "The overall risk level for PJSC ALROSA is review_required. A potential name match was found on the US Consolidated Screening List, which includes the OFAC SDN list, using data downloaded on 2026-10-16. Additionally, a potential name match appeared on the EU Consolidated Financial Sanctions List, which was published on 2026-10-15 and downloaded on 2026-10-16. These matches are potential name hits that require human review and do not confirm any wrongdoing. The GLEIF legal entity registry check was clean, confirming an active entity status. Unverified web research indicates the company is active and engaged in diamond mining, though these details are not established facts. The EU VIES VAT number validation and UK Companies House checks were not run.",
    extraction_sec: 31.4,
    narrative_sec: 41.7,
  },
  {
    id: "nordlicht",
    label: "Nordlicht GmbH — invalid VAT",
    profile: {
      company_name: "Nordlicht Handels GmbH", street: "Friedrichstrasse 112", postal_code: "10117", city: "Berlin",
      country: "Germany", registration_number: "HRB 187342", vat_id: "DE123456788", document_suitable: true,
    },
    not_applicable: { companies_house_check: NOT_UK },
    results: [
      {
        id: "vies_check", status: "success", level: "review", duration_sec: 0.5,
        message: "VIES reports VAT number DE123456788 as not valid or not registered.",
      },
      {
        id: "gleif_check", status: "success", level: "info", duration_sec: 1.9,
        message: "No confident LEI record was found. This is common, since many companies have no LEI, and is not itself a warning sign.",
      },
      ok("ofac_check", 0.2, OFAC_OK),
      ok("eu_sanctions_check", 0.1, EU_OK),
      {
        id: "web_research_check", status: "success", level: "info", duration_sec: 30.8,
        message: "The web search found no usable company details.",
        registry: {},
      },
    ],
    verdict: "review_required",
    narrative:
      "The overall risk level for Nordlicht Handels GmbH is review_required. The EU VIES check reports that VAT number DE123456788 is not valid or not registered, which requires human review. No name matches were found on the US Consolidated Screening List, with data downloaded on 2026-10-16. No name matches were found on the EU Consolidated Financial Sanctions List, which was published on 2026-10-15 and downloaded on 2026-10-16. The GLEIF registry check found no confident LEI record, which is informational and common for companies without an LEI. Web research yielded no usable company details, which is also informational. The UK Companies House check was not run.",
    extraction_sec: 31.4,
    narrative_sec: 37.8,
  },
  {
    id: "siemens",
    label: "Siemens AG — bad VAT, web skipped",
    profile: {
      company_name: "Siemens AG", street: "Werner-von-Siemens-Strasse 1", postal_code: "80333", city: "Muenchen",
      country: "Germany", registration_number: null, vat_id: "DE12345", document_suitable: true,
    },
    not_applicable: { companies_house_check: NOT_UK },
    results: [
      {
        id: "vies_check", status: "success", level: "review", duration_sec: 0.3,
        message: "VIES reports VAT number DE12345 as not valid or not registered.",
      },
      ok("gleif_check", 1.3, "A matching LEI record was found: Siemens Aktiengesellschaft (confidence 0.9933), entity status ACTIVE."),
      ok("ofac_check", 0.2, OFAC_OK),
      ok("eu_sanctions_check", 0.1, EU_OK),
      {
        id: "web_research_check", status: "skipped", duration_sec: 0.1,
        message: "The document has no usable registration or VAT number to search for.",
      },
    ],
    verdict: "review_required",
    narrative:
      "The overall risk level for Siemens AG is review_required. The EU VIES check reports that VAT number DE12345 is not valid or not registered, which requires human review. The GLEIF legal entity registry check is clean, identifying a matching active record for Siemens Aktiengesellschaft. No name matches were found on the US Consolidated Screening List, which was downloaded on 2026-10-16. No name matches were found on the EU Consolidated Financial Sanctions List, which was published on 2026-10-15 and downloaded on 2026-10-16. Web research was not applicable because the document lacked a usable registration or VAT number to search for. The UK Companies House check was not run.",
    extraction_sec: 30.7,
    narrative_sec: 37.6,
  },
  {
    id: "invoice",
    label: "Invoice — not assessable",
    profile: {
      company_name: "DBB DATA Steuerberatung GmbH", street: "Hessenring 99B", postal_code: "61348",
      city: "Bad Homburg vor der Höhe", country: "Germany", registration_number: null,
      vat_id: "DE153707874", document_suitable: false,
    },
    not_applicable: {},
    results: [],
    verdict: "not_assessable",
    reason: "The uploaded document does not appear to be a company profile that identifies a specific company.",
    narrative:
      "The uploaded document could not be assessed. The uploaded document does not appear to be a company profile that identifies a specific company.",
    extraction_sec: 29.4,
    narrative_sec: 0.1,
  },
];

export const MOCK_SCENARIOS = SCENARIOS.map(({ id, label }) => ({ id, label }));
export const DEFAULT_MOCK_SCENARIO = SCENARIOS[0].id;

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) return reject(new DOMException("Aborted", "AbortError"));
    const t = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => { clearTimeout(t); reject(new DOMException("Aborted", "AbortError")); },
      { once: true },
    );
  });
}

export async function* runMockDiligence(
  scenarioId: string,
  signal: AbortSignal,
): AsyncGenerator<DiligenceEvent> {
  const s = SCENARIOS.find((x) => x.id === scenarioId) ?? SCENARIOS[0];

  await sleep(1800, signal);
  yield { type: "extraction", duration_sec: s.extraction_sec, profile: s.profile };

  if (!s.profile.document_suitable) {
    await sleep(300, signal);
    yield { type: "verdict", risk_level: s.verdict, reason: s.reason };
    yield { type: "narrative", text: s.narrative, duration_sec: s.narrative_sec };
    return;
  }

  const run = CHECK_ORDER.filter((id) => s.results.some((r) => r.id === id));
  yield { type: "plan", run, not_applicable: s.not_applicable };

  for (const id of run) {
    const result = s.results.find((r) => r.id === id)!;
    yield { type: "check_started", id };
    await sleep(id === "web_research_check" ? 2600 : 700, signal);
    yield { type: "check", result };
  }

  yield { type: "verdict", risk_level: s.verdict };
  await sleep(2200, signal);
  yield { type: "narrative", text: s.narrative, duration_sec: s.narrative_sec };
}