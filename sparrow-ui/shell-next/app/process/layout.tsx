import type { Metadata } from "next";
import { JsonLd } from "@/components/json-ld";
import { GITHUB_URL, PUBLISHER_URL, SITE_NAME, SITE_URL } from "@/lib/site";

const TITLE = "Document Data Extraction to JSON with Local AI";
const DESCRIPTION =
  "Extract structured data as JSON from invoices, bank statements, lab results and tables with local vision AI. Open source and privacy-first: documents stay on your own infrastructure.";

// This page is a client component, so its metadata lives in the layout.
export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "document data extraction",
    "invoice data extraction",
    "PDF to JSON",
    "extract data from PDF",
    "bank statement parser",
    "lab results extraction",
    "table extraction",
    "document AI",
    "OCR alternative",
    "vision LLM",
    "local LLM",
    "open source",
    "privacy-first",
  ],
  alternates: { canonical: "/process" },
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: `${TITLE} | ${SITE_NAME}`,
    description: DESCRIPTION,
    url: "/process",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image", title: `${TITLE} | ${SITE_NAME}`, description: DESCRIPTION },
};

export default function ProcessLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: SITE_NAME,
          url: `${SITE_URL}/process`,
          description: DESCRIPTION,
          applicationCategory: "BusinessApplication",
          operatingSystem: "Web",
          isAccessibleForFree: true,
          codeRepository: GITHUB_URL,
          license: `${GITHUB_URL}/blob/main/LICENSE`,
          publisher: { "@type": "Organization", name: "Katana ML", url: PUBLISHER_URL },
        }}
      />
      {children}
    </>
  );
}