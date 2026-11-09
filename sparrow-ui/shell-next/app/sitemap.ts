import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// "/" redirects to /process, so only the real pages are listed.
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: `${SITE_URL}/process`, changeFrequency: "monthly" },
    { url: `${SITE_URL}/diligence`, changeFrequency: "monthly" },
  ];
}