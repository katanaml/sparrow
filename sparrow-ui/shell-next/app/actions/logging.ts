"use server";

import { headers } from "next/headers";
import { fetch_geolocation } from "@/lib/geoip";
import { timestamp } from "@/lib/timestamp";

// ─── Helpers ──────────────────────────────────────────────────────────────
async function getClientInfo(): Promise<{ ip: string; country: string }> {
  const headersList = await headers();
  const raw = headersList.get("x-forwarded-for")?.split(",")[0].trim()
    ?? headersList.get("x-real-ip")
    ?? "unknown";
  const ip = raw === "::1" ? "127.0.0.1" : raw;
  const country = await fetch_geolocation(ip);
  return { ip, country };
}

// ─── Log events ───────────────────────────────────────────────────────────
export async function log_page_load(page: string): Promise<void> {
  const { ip, country } = await getClientInfo();
  console.log(`[${timestamp()}] Page load - Page: ${page}, IP: ${ip}, Country: ${country}`);
}

export async function log_example_selected(example: string): Promise<void> {
  const { ip, country } = await getClientInfo();
  console.log(`[${timestamp()}] Example selected - Example: ${example}, IP: ${ip}, Country: ${country}`);
}

export async function log_file_upload(fileName: string, fileSize: string): Promise<void> {
  const { ip, country } = await getClientInfo();
  console.log(`[${timestamp()}] File uploaded - File: ${fileName}, Size: ${fileSize}, IP: ${ip}, Country: ${country}`);
}

export async function log_navigation(from: string, to: string): Promise<void> {
  const { ip, country } = await getClientInfo();
  console.log(`[${timestamp()}] Navigation - From: ${from}, To: ${to}, IP: ${ip}, Country: ${country}`);
}