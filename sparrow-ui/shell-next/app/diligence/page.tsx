import type { Metadata } from "next";
import "./diligence.css";
import { DiligenceClient } from "@/components/diligence-client";
import { JsonLd } from "@/components/json-ld";
import { PUBLISHER_URL, SITE_NAME, SITE_URL } from "@/lib/site";

const TITLE = "Company Due Diligence Check: Sanctions, VAT, LEI";
const DESCRIPTION =
  "Upload an invoice, order confirmation, purchase order or company profile. Sparrow reads the company and screens it against OFAC and EU sanctions lists, VAT (VIES), LEI (GLEIF), UK Companies House and public web sources.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "customer due diligence",
    "supplier due diligence",
    "vendor screening",
    "sanctions screening",
    "OFAC sanctions check",
    "EU sanctions list check",
    "VAT number validation",
    "VIES check",
    "LEI lookup",
    "GLEIF",
    "UK Companies House check",
    "company verification",
    "know your business",
    "KYB check",
    "counterparty check",
    "check company from invoice",
  ],
  alternates: { canonical: "/diligence" },
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: `${TITLE} | ${SITE_NAME}`,
    description: DESCRIPTION,
    url: "/diligence",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image", title: `${TITLE} | ${SITE_NAME}`, description: DESCRIPTION },
};

export default function DiligencePage() {
  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "WebApplication",
          name: "Sparrow Due Diligence",
          url: `${SITE_URL}/diligence`,
          description: DESCRIPTION,
          applicationCategory: "BusinessApplication",
          operatingSystem: "Web",
          featureList: [
            "Reads the company identity from an invoice, order confirmation, purchase order, receipt or company profile",
            "Screens against the US Consolidated Screening List (OFAC SDN and other US lists)",
            "Screens against the EU Consolidated Financial Sanctions List",
            "Validates EU VAT numbers with VIES",
            "Looks up the legal entity identifier (LEI) in GLEIF",
            "Checks UK companies at Companies House",
            "Collects unverified company details from public web pages",
          ],
          publisher: { "@type": "Organization", name: "Katana ML", url: PUBLISHER_URL },
        }}
      />
      <DiligenceClient />
    </>
  );
}