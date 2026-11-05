// Example results shown by the "See an example" buttons.
//
// The data comes from real runs of the diligence flow on sample company
// profiles, so an example looks exactly like what a user gets for their own
// document. Examples never call the backend (no quota is used); they are
// replayed through the same `DiligenceEvent` stream the page uses for a real
// run, with short pauses so results appear one by one.

import type { CheckId, CheckResult, DiligenceEvent, ExtractedProfile, RiskLevel, WebRegistry } from "./diligence-types";

export interface DiligenceExample {
  id: string;
  label: string;
  description: string;
  // One line shown on the example card: what the user will see.
  highlight: string;
  profile: ExtractedProfile;
  extraction_sec: number;
  not_applicable: Partial<Record<CheckId, string>>;
  // Checks that finish before web research, in run order.
  fast_checks: CheckResult[];
  web_check: CheckResult;
  risk_level: RiskLevel;
  narrative: string;
  narrative_sec: number;
}

const NO_VAT = "No EU VAT ID on the document.";
const NOT_UK = "Not a UK company.";

const SAP_REGISTRY: WebRegistry = {
  company_name: { value: "SAP SE", source_url: "https://www.sap.com/about/legal/impressum-se.html" },
  registration_number: { value: "HRB 719915", source_url: "https://www.sap.com/about/legal/impressum-se.html" },
  vat_number: { value: "DE 143454214", source_url: "https://www.sap.com/about/legal/impressum-se.html" },
  status: { value: "active", source_url: "https://www.online-handelsregister.de/handelsregisterauszug/bw/Mannheim/HRB/719915/SAP-SE" },
  registered: { value: "07.07.2014", source_url: "https://www.online-handelsregister.de/handelsregisterauszug/bw/Mannheim/HRB/719915/SAP-SE" },
  address: { value: "Dietmar-Hopp-Allee 16, 69190 Walldorf", source_url: "https://www.online-handelsregister.de/handelsregisterauszug/bw/Mannheim/HRB/719915/SAP-SE" },
  activity: {
    value: "Organisations- und Einsatzberatung sowie Schulungen der Anwender von Software und Cloud-Lösungen",
    source_url: "https://handelsregister.online/Deutschland/Handelsregisterinformation/3998640",
  },
};

const ALROSA_REGISTRY: WebRegistry = {
  company_name: { value: "PJSC ALROSA", source_url: "https://cbonds.com/company/18" },
  registration_number: { value: "1021400967092", source_url: "https://www.opensanctions.org/entities/NK-JDEoxEMoEQHGnYeJqt9qox" },
  status: { value: "active", source_url: "https://cbonds.com/company/18" },
  registered: { value: "17 July 2002", source_url: "https://www.alrosa.ru/upload/iblock/bf4/ALROSA-6M2021-ENG.pdf" },
  address: { value: "115184, Moskva, Ozerkovskaia nab., 24", source_url: "https://cbonds.com/company/18" },
};

const SHOPIFY_REGISTRY: WebRegistry = {
  company_name: {
    value: "SHOPIFY INC.",
    source_url: "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html?Open=1&p=&corpId=4261607&wbdisable=true",
  },
  registration_number: {
    value: "4261607",
    source_url: "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html?Open=1&p=&corpId=4261607&wbdisable=true",
  },
  registered: {
    value: "2004-09-28",
    source_url: "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html?Open=1&p=&corpId=4261607&wbdisable=true",
  },
};

export const DILIGENCE_EXAMPLES: DiligenceExample[] = [
  {
    id: "sap",
    label: "SAP SE",
    description: "Germany · clean",
    highlight: "All checks clear: VAT number valid in VIES, LEI found, no sanctions matches.",
    profile: {
      company_name: "SAP SE",
      street: "Dietmar-Hopp-Allee 16",
      postal_code: "69190",
      city: "Walldorf",
      country: "Germany",
      registration_number: "HRB 719915",
      vat_id: "DE143454214",
      document_suitable: true,
    },
    extraction_sec: 33.9,
    not_applicable: { companies_house_check: NOT_UK },
    fast_checks: [
      { id: "vies_check", status: "success", duration_sec: 1.1, level: "ok", message: "VAT number DE143454214 is valid according to VIES." },
      { id: "gleif_check", status: "success", duration_sec: 0.6, level: "ok", message: "A matching LEI record was found by registration number: SAP SE, entity status ACTIVE." },
      { id: "ofac_check", status: "success", duration_sec: 0.2, level: "ok", message: "No name matches were found on the US Consolidated Screening List (OFAC SDN and other US lists) (data downloaded 2026-10-28)." },
      { id: "eu_sanctions_check", status: "success", duration_sec: 0.1, level: "ok", message: "No name matches were found on the EU Consolidated Financial Sanctions List (list published 2026-10-23, data downloaded 2026-10-28)." },
    ],
    web_check: { id: "web_research_check", status: "success", duration_sec: 79.1, level: "info", message: "Company details (web, unverified)", registry: SAP_REGISTRY },
    risk_level: "clean",
    narrative:
      "The overall risk level for SAP SE is clean. The GLEIF legal entity registry check confirmed a matching LEI record with an active status. The EU VIES validation confirmed that the VAT number is valid. No name matches were found on the US Consolidated Screening List, using data downloaded on 2026-10-28. No name matches were found on the EU Consolidated Financial Sanctions List, which was published on 2026-10-23 and downloaded on 2026-10-28. Web research provided unverified details including the registration number, VAT number, and active status, which are informational only.",
    narrative_sec: 37.6,
  },
  {
    id: "alrosa",
    label: "PJSC ALROSA",
    description: "Russia · review required",
    highlight: "Potential name matches on the US and EU sanctions lists, shown for human review.",
    profile: {
      company_name: "PJSC ALROSA",
      street: "Lenin Street 6",
      postal_code: "678174",
      city: "Mirny",
      country: "Russia",
      registration_number: "OGRN 1021400967092",
      vat_id: null,
      document_suitable: true,
    },
    extraction_sec: 34.3,
    not_applicable: { vies_check: NO_VAT, companies_house_check: NOT_UK },
    fast_checks: [
      {
        id: "gleif_check", status: "success", duration_sec: 0.7, level: "ok",
        message: "A matching LEI record was found by registration number: АКЦИОНЕРНАЯ КОМПАНИЯ \"АЛРОСА\" (ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО), entity status ACTIVE.",
      },
      {
        id: "ofac_check", status: "success", duration_sec: 0.2, level: "review",
        message: "1 potential name match on the US Consolidated Screening List (OFAC SDN and other US lists) (data downloaded 2026-10-28).",
        matches: [{ name: "PUBLIC JOINT STOCK COMPANY ALROSA", kind: "Entity", score: 1.0, list: "Specially Designated Nationals (SDN) - Treasury Department" }],
      },
      {
        id: "eu_sanctions_check", status: "success", duration_sec: 0.1, level: "review",
        message: "1 potential name match on the EU Consolidated Financial Sanctions List (list published 2026-10-23, data downloaded 2026-10-28).",
        matches: [{ name: "PJSC Alrosa", kind: "enterprise", score: 1.0, list: "EU Consolidated Financial Sanctions List (FSF) - European Commission" }],
      },
    ],
    web_check: { id: "web_research_check", status: "success", duration_sec: 86.2, level: "info", message: "Company details (web, unverified)", registry: ALROSA_REGISTRY },
    risk_level: "review_required",
    narrative:
      "The screening for PJSC ALROSA resulted in a review required status due to potential name matches on international sanctions lists. A potential name match was identified on the US Consolidated Screening List, which includes the OFAC SDN list, using data downloaded on 2026-10-28. Additionally, a potential name match was found on the EU Consolidated Financial Sanctions List, which was published on 2026-10-23 and downloaded on 2026-10-28. These matches are potential only and require human review to determine if they are relevant to the company. The GLEIF legal entity registry check was clean, confirming an active LEI record for the company. Web research provided unverified information indicating the company is active and registered in 2002, with an address in Moscow, but these details are not confirmed facts.",
    narrative_sec: 43.8,
  },
  {
    id: "shopify",
    label: "Shopify Inc.",
    description: "Canada · clean",
    highlight: "Non-EU company: LEI found by name, no sanctions matches, web details to compare.",
    profile: {
      company_name: "Shopify Inc.",
      street: "151 O'Connor Street, Ground floor",
      postal_code: "K2P 2L8",
      city: "Ottawa",
      country: "Canada",
      registration_number: "4261607",
      vat_id: null,
      document_suitable: true,
    },
    extraction_sec: 33.4,
    not_applicable: { vies_check: NO_VAT, companies_house_check: NOT_UK },
    fast_checks: [
      { id: "gleif_check", status: "success", duration_sec: 1.0, level: "ok", message: "A matching LEI record was found: SHOPIFY INC. (confidence 0.9), entity status ACTIVE." },
      { id: "ofac_check", status: "success", duration_sec: 0.2, level: "ok", message: "No name matches were found on the US Consolidated Screening List (OFAC SDN and other US lists) (data downloaded 2026-10-28)." },
      { id: "eu_sanctions_check", status: "success", duration_sec: 0.1, level: "ok", message: "No name matches were found on the EU Consolidated Financial Sanctions List (list published 2026-10-23, data downloaded 2026-10-28)." },
    ],
    web_check: { id: "web_research_check", status: "success", duration_sec: 58.0, level: "info", message: "Company details (web, unverified)", registry: SHOPIFY_REGISTRY },
    risk_level: "clean",
    narrative:
      "The overall risk level for Shopify Inc. is clean. The GLEIF legal entity registry check confirmed a matching LEI record with an active status. No name matches were found on the US Consolidated Screening List, which was downloaded on 2026-10-28. Similarly, no name matches were found on the EU Consolidated Financial Sanctions List, published on 2026-10-23 and downloaded on 2026-10-28. Unverified web research indicates the company was registered on 2004-09-28 and lists the registration number 4261607.",
    narrative_sec: 36.8,
  },
];

function pause(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) return reject(new DOMException("Aborted", "AbortError"));
    const t = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

/** Replays an example as the event stream a real run would produce. */
export async function* runExample(id: string, signal: AbortSignal): AsyncGenerator<DiligenceEvent> {
  const ex = DILIGENCE_EXAMPLES.find((e) => e.id === id);
  if (!ex) {
    yield { type: "error", message: "Unknown example." };
    return;
  }

  await pause(1200, signal);
  yield { type: "extraction", duration_sec: ex.extraction_sec, profile: ex.profile };

  const run: CheckId[] = [...ex.fast_checks.map((c) => c.id), ex.web_check.id];
  yield { type: "plan", run, not_applicable: ex.not_applicable };

  for (const check of ex.fast_checks) {
    await pause(250, signal);
    yield { type: "check_started", id: check.id };
    await pause(600, signal);
    yield { type: "check", result: check };
  }

  // The verdict is already known from the fast checks; web research, which
  // takes the longest, only confirms it (or, rarely, escalates it).
  await pause(250, signal);
  yield { type: "check_started", id: ex.web_check.id };
  yield { type: "verdict", risk_level: ex.risk_level };
  await pause(2000, signal);
  yield { type: "check", result: ex.web_check };
  yield { type: "verdict", risk_level: ex.risk_level };

  await pause(1500, signal);
  yield { type: "narrative", text: ex.narrative, duration_sec: ex.narrative_sec };
}