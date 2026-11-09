import { OG_SIZE, renderOgImage } from "@/lib/og-image";

export const alt = "Sparrow due diligence: screen a company from a document";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return renderOgImage(
    "Due diligence from a document",
    "Upload an invoice or company profile. Sparrow checks sanctions lists, VAT, LEI and company registers.",
  );
}