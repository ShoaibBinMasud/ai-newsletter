import { getArticlesByDate, getLatestDate, getTotalCount, CATEGORY_ORDER } from "@/lib/db";
import SectorCard from "@/components/SectorCard";
import SubscribeForm from "@/components/SubscribeForm";

export const revalidate = 600;

export default function HomePage() {
  let grouped;
  let date: string | null = null;
  let total = 0;

  try {
    date = getLatestDate();
    grouped = getArticlesByDate(date ?? undefined);
    total = getTotalCount();
  } catch {
    grouped = Object.fromEntries(CATEGORY_ORDER.map((c) => [c, []])) as ReturnType<typeof getArticlesByDate>;
  }

  const displayDate = date
    ? new Date(date + "T00:00:00Z").toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        timeZone: "UTC",
      })
    : null;

  const todayCount = CATEGORY_ORDER.reduce((n, c) => n + (grouped[c]?.length ?? 0), 0);

  return (
    <div>
      {/* ── Hero ───────────────────────────────────────────── */}
      <div className="border border-black bg-white px-6 py-8 mb-8 text-center">
        <h2 className="text-[28px] sm:text-[34px] font-black text-black leading-tight
                       tracking-tight mb-2">
          The AI news briefing<br />that gets to the point.
        </h2>
        <p className="text-[14px] text-[#555] mb-6 leading-relaxed">
          Curated daily across AI research, business, dev tools, and security —
          <br className="hidden sm:inline" /> delivered at 7 AM. No noise, no hype.
        </p>

        {/* Subscribe form */}
        <div className="max-w-md mx-auto">
          <SubscribeForm />
          <p className="text-[11px] text-[#aaa] mt-2">
            Free forever. Unsubscribe any time.
          </p>
        </div>
      </div>

      {/* ── Today's edition header ─────────────────────────── */}
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <p className="text-[11px] font-bold tracking-[0.12em] uppercase text-[#999] mb-0.5">
            Today&rsquo;s Edition
          </p>
          <h3 className="text-[16px] font-black text-black">
            {displayDate ?? "Latest AI News"}
          </h3>
        </div>
        {total > 0 && (
          <span className="text-[11px] text-[#aaa]">
            {total.toLocaleString()} in archive
          </span>
        )}
      </div>

      {/* ── Sector cards ───────────────────────────────────── */}
      {todayCount === 0 ? (
        <div className="border border-[#f74904] bg-[#fff8f5] p-5">
          <p className="text-[13px] font-bold text-black mb-1">No articles yet</p>
          <p className="text-[13px] text-[#555] mb-3">
            Run the Python collector to populate today&rsquo;s edition.
          </p>
          <pre className="bg-[#f3f3f3] text-black border border-[#e0e0e0] px-4 py-3
                           text-[11px] font-mono overflow-x-auto leading-relaxed">
{`cd ai-newsletter-collector
python main.py`}
          </pre>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {CATEGORY_ORDER.map((category) => (
            <SectorCard key={category} sector={category} articles={grouped[category] ?? []} />
          ))}
        </div>
      )}
    </div>
  );
}
