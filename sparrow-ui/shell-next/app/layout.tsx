import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Navbar } from "@/components/navbar";
import { JsonLd } from "@/components/json-ld";
import { GITHUB_URL, PUBLISHER_URL, SITE_NAME, SITE_URL } from "@/lib/site";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const version = process.env.VERSION ?? "0.5.0";

const DESCRIPTION =
  "Open-source, privacy-first platform for structured data extraction from invoices, statements, lab results and other documents, powered by local vision AI.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Sparrow: Document Data Extraction with Local AI", template: "%s | Sparrow" },
  description: DESCRIPTION,
  applicationName: SITE_NAME,
  publisher: "Katana ML",
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: "Sparrow: Document Data Extraction with Local AI",
    description: DESCRIPTION,
    locale: "en_US",
  },
  twitter: { card: "summary_large_image" },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`} suppressHydrationWarning>
      <body>
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: SITE_NAME,
            url: SITE_URL,
            publisher: { "@type": "Organization", name: "Katana ML", url: PUBLISHER_URL, sameAs: [GITHUB_URL] },
          }}
        />
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <Navbar version={version} />
          <main className="app">{children}</main>
          <footer className="site">
            <div className="row">
              <span>Sparrow v{version}</span>
              <span className="footer-desktop">·</span>
              <a href="mailto:abaranovskis@redsamuraiconsulting.com" className="footer-desktop">abaranovskis@redsamuraiconsulting.com</a>
              <a href="mailto:abaranovskis@redsamuraiconsulting.com" className="footer-mobile">abaranovskis@redsamuraiconsulting.com</a>
              <span className="footer-desktop">·</span>
              <a href="https://katanaml.io" target="_blank" rel="noopener" className="footer-desktop">Katana ML</a>
            </div>
            <div className="row">
              <a href="https://katanaml.io" target="_blank" rel="noopener" className="footer-mobile">Katana ML</a>
              <span className="footer-desktop" style={{ marginLeft: "auto" }}>
                <a href="https://github.com/katanaml/sparrow" target="_blank" rel="noopener">GitHub</a>
              </span>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}