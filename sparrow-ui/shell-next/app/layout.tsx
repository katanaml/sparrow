import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Navbar } from "@/components/navbar";
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

export const metadata: Metadata = {
  title: "Sparrow",
  description: "Structured data extraction with local Vision AI",
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