import Link from "next/link";
import { Article } from "@/types/article";
import { categoryToSlug } from "@/lib/db";

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

export default function SectorCard({
  sector,
  articles,
}: {
  sector: string;
  articles: Article[];
}) {
  const config = CATEGORY_CONFIG[sector] ?? { label: sector, emoji: "📰" };
  const slug   = categoryToSlug(sector);
  const count  = articles.length;
  const topPick = articles.find((a) => a.is_featured === 1) ?? articles[0] ?? null;

  return (
    <Link
      href={`/${slug}`}
      className="block border border-[#e0e0e0] bg-white hover:border-black
                 transition-colors duration-150 group"
    >
      {/* Card header */}
      <div className="border-b border-[#e0e0e0] group-hover:border-black px-5 py-3
                      flex items-center justify-between transition-colors duration-150">
        <span className="text-[12px] font-black tracking-widest uppercase text-black">
          {config.emoji} {config.label}
        </span>
        <span className="text-[11px] text-[#999] font-medium">
          {count} {count === 1 ? "story" : "stories"}
        </span>
      </div>

      {/* Top headline */}
      <div className="px-5 py-4 min-h-[72px] flex items-start">
        {topPick ? (
          <p className="text-[14px] font-semibold text-black leading-snug
                        group-hover:text-[#f74904] transition-colors duration-150
                        line-clamp-2">
            {topPick.ai_title ?? topPick.title}
          </p>
        ) : (
          <p className="text-[13px] text-[#999] italic">No stories yet today.</p>
        )}
      </div>

      {/* Footer CTA */}
      <div className="px-5 pb-4">
        <span className="text-[11px] font-bold uppercase tracking-widest text-[#f74904]
                         group-hover:underline">
          Read all {count} stories →
        </span>
      </div>
    </Link>
  );
}
