"use client";

import { useState } from "react";
import { Article } from "@/types/article";
import ArticleRow from "./ArticleRow";

const CATEGORY_CONFIG: Record<string, { label: string; emoji: string }> = {
  "Model Releases":           { label: "Model Releases",           emoji: "🚀" },
  "Products & Features":      { label: "Products & Features",      emoji: "⚡️" },
  "RAG, Agents & Techniques": { label: "RAG, Agents & Techniques", emoji: "🔧" },
  "Research & Open Source":   { label: "Research & Open Source",   emoji: "🔬" },
  "Chips & Infrastructure":   { label: "Chips & Infrastructure",   emoji: "💻" },
  "AI Applications":          { label: "AI Applications",          emoji: "🌐" },
  "Policy & Governance":      { label: "Policy & Governance",      emoji: "🏛️" },
  "Security & Threats":       { label: "Security & Threats",       emoji: "🔐" },
  "Business & Funding":       { label: "Business & Funding",       emoji: "💼" },
  "Tutorials & Guides":       { label: "Tutorials & Guides",       emoji: "📖" },
  "Trending Repos & Papers":     { label: "Trending Repos & Papers",     emoji: "🐙" },
};

export default function SubcategoryFilter({
  sector,
  articles,
}: {
  sector: string;
  articles: Article[];
}) {
  const [active, setActive] = useState<string | null>(null);
  const config = CATEGORY_CONFIG[sector] ?? { label: sector, emoji: "📰" };

  // Collect unique subcategories present in the articles (preserve insertion order)
  const subcategories = Array.from(
    new Set(articles.map((a) => a.subcategory).filter((s): s is string => s != null))
  );

  const filtered = active ? articles.filter((a) => a.subcategory === active) : articles;

  return (
    <section className="mb-10">

      {/* Section header */}
      <div className="flex items-center gap-3 mb-4 pb-2 border-b-2 border-black">
        <h2 className="text-[13px] font-black tracking-widest uppercase text-black">
          {config.emoji} {config.label}
        </h2>
        <span className="ml-auto text-[11px] text-[#999] font-medium shrink-0">
          {filtered.length} {filtered.length === 1 ? "story" : "stories"}
        </span>
      </div>

      {/* Subcategory filter buttons */}
      {subcategories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={() => setActive(null)}
            className={`text-[11px] font-bold uppercase tracking-wide px-3 py-1 border transition-colors ${
              active === null
                ? "bg-black text-white border-black"
                : "bg-white text-[#666] border-[#ccc] hover:border-black hover:text-black"
            }`}
          >
            All
          </button>
          {subcategories.map((sub) => (
            <button
              key={sub}
              onClick={() => setActive(active === sub ? null : sub)}
              className={`text-[11px] font-bold uppercase tracking-wide px-3 py-1 border transition-colors ${
                active === sub
                  ? "bg-[#f74904] text-white border-[#f74904]"
                  : "bg-white text-[#666] border-[#ccc] hover:border-[#f74904] hover:text-[#f74904]"
              }`}
            >
              {sub}
            </button>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <p className="text-sm text-[#999] italic">No articles yet — run the collector first.</p>
      ) : (
        <div>
          {filtered.map((article) => (
            <ArticleRow key={article.id} article={article} />
          ))}
        </div>
      )}
    </section>
  );
}
