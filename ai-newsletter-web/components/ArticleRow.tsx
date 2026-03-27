import { Article } from "@/types/article";

function decodeEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/&[a-z]+;/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function readTime(text: string): string {
  const words = text.trim().split(/\s+/).length;
  return `${Math.max(1, Math.round(words / 200))} min read`;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  try {
    const diff = Math.max(0, Date.now() - new Date(iso).getTime());
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  } catch {
    return "";
  }
}

export default function ArticleRow({ article }: { article: Article }) {
  const summary = decodeEntities(article.ai_summary ?? article.summary ?? "");
  const ago = timeAgo(article.published_at ?? article.fetched_at);

  return (
    <div className="border border-[#6B6B6B] bg-white mb-5 p-4 sm:p-5">
      {/* Badges row */}
      {(article.subcategory != null || article.is_featured === 1 || (article.is_github === 1 && article.stars != null)) && (
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            {article.subcategory && (
              <span className="text-[10px] font-bold uppercase tracking-wide
                               border border-[#ccc] text-[#666] px-2 py-0.5">
                {article.subcategory}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {article.is_github === 1 && article.stars != null && (
              <span className="text-[12px] font-semibold text-[#f74904]">
                ★ {article.stars.toLocaleString()}
              </span>
            )}
            {article.is_featured === 1 && (
              <span className="text-[10px] font-bold uppercase tracking-wide
                               bg-[#f74904] text-white px-2 py-0.5">
                Top Pick
              </span>
            )}
          </div>
        </div>
      )}

      {/* Divider */}
      <div className="border-t border-[#6B6B6B] mb-3" />

      {/* Title — the only clickable link */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="group"
      >
        <h3 className="text-[15px] sm:text-[16px] font-bold text-black leading-snug
                        group-hover:text-[#f74904] transition-colors duration-150 mb-2 inline">
          {article.ai_title ?? article.title}
        </h3>
      </a>

      {/* Summary */}
      {summary && (
        <p className="text-[14px] text-[#333] leading-[1.65] mt-2 mb-3">
          {summary}
        </p>
      )}

      {/* Footer */}
      <span className="text-[11px] text-[#999]">
        {[summary ? readTime(summary) : "", ago].filter(Boolean).join(" · ")}
      </span>
    </div>
  );
}
