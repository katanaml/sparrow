// Single place for the public site address, used by metadata, robots and sitemap.
// Set SITE_URL in the environment for a different domain (no trailing slash needed).
export const SITE_URL = (process.env.SITE_URL ?? "https://sparrow.katanaml.io").replace(/\/+$/, "");

export const SITE_NAME = "Sparrow";
export const GITHUB_URL = "https://github.com/katanaml/sparrow";
export const PUBLISHER_URL = "https://katanaml.io";