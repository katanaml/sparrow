import type { Metadata } from "next";
import "./diligence.css";
import { DiligenceClient } from "@/components/diligence-client";

export const metadata: Metadata = {
  title: "Due diligence",
  description:
    "Upload an invoice, order confirmation, purchase order or company profile and screen the company against VAT, legal entity, sanctions and registry sources.",
};

export default function DiligencePage() {
  return <DiligenceClient />;
}