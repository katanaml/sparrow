import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/process", "/diligence"],
        // API routes and the internal pages stay out of search results.
        disallow: ["/api/", "/dashboard", "/feedback"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}