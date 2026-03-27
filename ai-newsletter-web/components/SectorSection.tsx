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

export default function SectorSection({
  sector,
  articles,
}: {
  sector: string;
  articles: Article[];
}) {
  const config = CATEGORY_CONFIG[sector] ?? { label: sector, emoji: "📰" };

  return (
    <section className="mb-10">

      {/* Section header */}
      <div className="flex items-center gap-3 mb-4 pb-2 border-b-2 border-black">
        <h2 className="text-[13px] font-black tracking-widest uppercase text-black">
          {config.emoji} {config.label}
        </h2>
        <span className="ml-auto text-[11px] text-[#999] font-medium shrink-0">
          {articles.length} {articles.length === 1 ? "story" : "stories"}
        </span>
      </div>

      {articles.length === 0 ? (
        <p className="text-sm text-[#999] italic">
          No articles yet — run the collector first.
        </p>
      ) : (
        <div>
          {articles.map((article) => (
            <ArticleRow key={article.id} article={article} />
          ))}
        </div>
      )}
    </section>
  );
}
