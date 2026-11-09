import type { Metadata } from "next";

// Internal page: keep it out of search results.
export const metadata: Metadata = {
  title: "Feedback",
  robots: { index: false, follow: false },
};

export default function FeedbackLayout({ children }: { children: React.ReactNode }) {
  return children;
}