"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState, useRef } from "react";
import { log_navigation, log_page_load } from "@/app/actions/logging";

// ─── Icons ────────────────────────────────────────────────────────────────
const SparrowMark = () => (
  <svg width={16} height={16} viewBox="0 0 122.88 98.83" fill="currentColor">
    <path fillRule="evenodd" clipRule="evenodd" d="M110.18,6.26l10.9,4.72c1.97,0.89,2.82,1.07-0.07,1.94l-9.56,2.87c-0.45,2.36-1.03,4.89-1.01,7.71c0.02,2.25,0.37,4.44,0.89,6.61c1.29,23.23-11.12,36.41-34.63,41.43c0.05,0.14,0.09,0.29,0.11,0.44l1.94,11.52h8.19c1.41,0,2.56,1.15,2.56,2.56c0,1.41-1.15,2.56-2.56,2.56H70.02c-1.41,0-2.56-1.15-2.56-2.56c0-1.41,1.15-2.56,2.56-2.56h3.55l-1.8-10.68c-0.05-0.31-0.05-0.61,0.01-0.89c-9.89-0.2-18.75,0.76-26.53,2.94c-14.24,4-20.9,10.76-29.92,19.86c-3.52,3.55-3.57,5.16-8.69,3.33C5.21,97.56,4.03,96.86,3.09,96c-2.1-1.92-3.02-4.66-3.09-7.97c10.98-5.69,20.77-12.96,29.35-21.84c9.81-0.47,22.76-0.91,31.21-5.63c9.69-5.41,15.2-14.62,22.79-24.92c0.89-1.84,1.07-2.82,0.7-3.13c-1.54-1.27-6.94,5.31-7.91,6.45c-6.25,7.43-12.63,15.79-21.27,19.22c-5.15,2.04-14.72,2.9-21.14,3.22c0.57-0.66,1.13-1.32,1.69-2c13.13-17.06,40.78-36.37,47.93-49.25C87.7-3.44,104.38-1.97,110.18,6.26L110.18,6.26z" />
    <circle cx="99.8" cy="9.74" r="3" fill="hsl(var(--background))" />
  </svg>
);

const WandIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/>
    <path d="M17.8 11.8 19 13"/><path d="M15 9h0"/><path d="M17.8 6.2 19 5"/>
    <path d="m3 21 9-9"/><path d="M12.2 6.2 11 5"/>
  </svg>
);

const BarChartIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="20" x2="12" y2="10"/>
    <line x1="18" y1="20" x2="18" y2="4"/>
    <line x1="6"  y1="20" x2="6"  y2="16"/>
  </svg>
);

const MessageIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);

const SunIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4"/>
    <line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);

const MoonIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

// ─── Props from server ────────────────────────────────────────────────────
interface NavbarProps {
  version: string;
}

// ─── Navbar ───────────────────────────────────────────────────────────────
export function Navbar({ version }: NavbarProps) {
  const pathname = usePathname();
  const active = (path: string) =>
    pathname === path || pathname.startsWith(path + "/");

  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const prevPathname = useRef<string | null>(null);

  useEffect(() => setMounted(true), []);

  // Log page load on first mount
  useEffect(() => {
    log_page_load(pathname);
  }, []);

  // Log navigation when pathname changes
  useEffect(() => {
    if (prevPathname.current !== null && prevPathname.current !== pathname) {
      log_navigation(prevPathname.current, pathname);
    }
    prevPathname.current = pathname;
  }, [pathname]);

  const isDark = resolvedTheme === "dark";

  return (
    <header className="topbar">
      <div className="topbar-inner">

        {/* Brand */}
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "inherit" }}>
          <div className="brand-mark">
            <SparrowMark />
          </div>
          <div>
            <span className="brand-name">Sparrow</span>
            <span className="brand-sub">v{version}</span>
          </div>
        </Link>

        {/* Nav tabs — centered */}
        <nav className="nav" role="tablist">
          <Link href="/process"   data-active={active("/process")   ? "true" : undefined}><WandIcon />    <span className="nav-label">Process</span></Link>
          <Link href="/dashboard" data-active={active("/dashboard") ? "true" : undefined}><BarChartIcon /><span className="nav-label">Dashboard</span></Link>
          <Link href="/feedback"  data-active={active("/feedback")  ? "true" : undefined}><MessageIcon /> <span className="nav-label">Feedback</span></Link>
        </nav>

        {/* Theme toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {mounted && (
            <button
              className="btn btn-ghost btn-icon btn-sm"
              onClick={() => setTheme(isDark ? "light" : "dark")}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>
          )}
        </div>

      </div>
    </header>
  );
}