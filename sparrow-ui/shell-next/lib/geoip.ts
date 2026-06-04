/**
 * geoip.ts — Country lookup from IP using GeoLite2-Country.mmdb
 * Server-side only. Equivalent of fetch_geolocation() in Gradio app.
 * Requires: npm install maxmind
 * Place GeoLite2-Country.mmdb in the project root (same as Gradio app).
 */

import * as maxmind from "maxmind";
import path from "path";
import type { CountryResponse } from "maxmind";

let reader: maxmind.Reader<CountryResponse> | null = null;

async function getReader(): Promise<maxmind.Reader<CountryResponse> | null> {
  if (reader) return reader;
  try {
    const dbPath = path.join(process.cwd(), "GeoLite2-Country.mmdb");
    reader = await maxmind.open<CountryResponse>(dbPath);
    return reader;
  } catch (err) {
    console.warn("GeoLite2-Country.mmdb not found or could not be opened:", err);
    return null;
  }
}

export async function fetch_geolocation(ip: string): Promise<string> {
  try {
    const r = await getReader();
    if (!r) return "Unknown";

    const result = r.get(ip);
    return result?.country?.names?.en ?? "Unknown";
  } catch {
    return "Unknown";
  }
}