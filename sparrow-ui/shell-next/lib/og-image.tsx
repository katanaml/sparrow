import { ImageResponse } from "next/og";

// Shared look for the link-preview images (LinkedIn, Slack, X, ...).
// Plain inline styles only: the image renderer does not read CSS files.
export const OG_SIZE = { width: 1200, height: 630 };

export function renderOgImage(title: string, subtitle: string) {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 72,
          background: "#0b0b0c",
          color: "#ffffff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 34, fontWeight: 600 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 10,
              background: "#22c55e",
              display: "flex",
            }}
          />
          Sparrow
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ fontSize: 68, fontWeight: 700, lineHeight: 1.1, letterSpacing: -1 }}>{title}</div>
          <div style={{ fontSize: 32, color: "#a1a1aa", lineHeight: 1.35 }}>{subtitle}</div>
        </div>
        <div style={{ fontSize: 26, color: "#71717a" }}>sparrow.katanaml.io</div>
      </div>
    ),
    { ...OG_SIZE },
  );
}