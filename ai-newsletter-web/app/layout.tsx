import type { Metadata } from "next";
import "./globals.css";

// ── Font choices ────────────────────────────────────────────────────────────
// Change the `fontStack` value below to switch fonts site-wide.
// No import needed for system fonts (options 1–3).
// For Inter (option 4), uncomment the two Inter lines and the variable below.
//
//  1. Helvetica / Arial  →  "Helvetica Neue, Helvetica, Arial, sans-serif"
//  2. System UI          →  "system-ui, -apple-system, sans-serif"   (SF Pro on Mac, Segoe UI on Windows)
//  3. Georgia (serif)    →  "Georgia, 'Times New Roman', serif"
//  4. Inter (previous)   →  uncomment: import { Inter } from "next/font/google"
//                                       const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })
//                           then set:  fontStack = "var(--font-inter), sans-serif"
//                           and add:   className={inter.variable} to <html>
// ────────────────────────────────────────────────────────────────────────────

const fontStack = "Helvetica Neue, Helvetica, Arial, sans-serif";

export const metadata: Metadata = {
  title: "AI Daily — Your Daily AI Intelligence Digest",
  description: "The top AI news, tools, and insights — curated daily.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        className="bg-[#fcfcfc] text-black min-h-screen"
        style={{ fontFamily: fontStack }}
      >

        {/* ── Top nav bar ─────────────────────────────────────── */}
        <div className="border-b border-[#e0e0e0] bg-[#fcfcfc]">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 py-2 flex items-center justify-center
                          gap-1 text-[11px] text-black">
            <a href="/#subscribe" className="hover:underline px-2">Subscribe</a>
            <span className="text-[#ccc]">|</span>
            <a href="/" className="hover:underline px-2">Home</a>
            <span className="text-[#ccc]">|</span>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline px-2"
            >
              Follow on X
            </a>
          </div>
        </div>

        {/* ── Black header ────────────────────────────────────── */}
        <header className="bg-black border-b border-black">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 py-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-[22px] font-black text-white tracking-tight leading-none mb-1">
                  AI Daily
                </h1>
                <p className="text-[11px] font-bold tracking-[0.1em] uppercase text-[#666]">
                  Intelligence Digest
                </p>
              </div>
              <time className="text-[12px] text-[#888] pt-1 text-right shrink-0">
                {new Date().toLocaleDateString("en-US", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </time>
            </div>
          </div>
        </header>

        {/* ── Page content ───────────────────────────────────── */}
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          {children}
        </main>

        {/* ── Footer ─────────────────────────────────────────── */}
        <footer className="border-t border-[#e0e0e0] mt-8 py-6">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 text-center text-[11px] text-[#999]">
            <p>AI Daily — powered by OpenAI &amp; GitHub Trending · Refreshed daily at 7 AM</p>
          </div>
        </footer>

      </body>
    </html>
  );
}
