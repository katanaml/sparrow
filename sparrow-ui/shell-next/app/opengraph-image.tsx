import { OG_SIZE, renderOgImage } from "@/lib/og-image";

export const alt = "Sparrow: structured data extraction from documents with local AI";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return renderOgImage(
    "Structured data from your documents",
    "Extract JSON from invoices, statements and lab results with local vision AI. Open source and privacy-first.",
  );
}