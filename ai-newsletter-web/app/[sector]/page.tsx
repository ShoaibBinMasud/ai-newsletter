import { notFound } from "next/navigation";
import Link from "next/link";
import { getArticlesByDate, getLatestDate, CATEGORY_SLUGS } from "@/lib/db";
import SubcategoryFilter from "@/components/SubcategoryFilter";

export const revalidate = 600;

export function generateStaticParams() {
  return Object.keys(CATEGORY_SLUGS).map((slug) => ({ sector: slug }));
}

export default function SectorPage({
  params,
}: {
  params: { sector: string };
}) {
  const category = CATEGORY_SLUGS[params.sector];
  if (!category) notFound();

  let articles: import("@/types/article").Article[] = [];
  let date: string | null = null;

  try {
    date = getLatestDate();
    const grouped = getArticlesByDate(date ?? undefined);
    articles = (grouped as Record<string, typeof articles>)[category] ?? [];
  } catch {
    articles = [];
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

  return (
    <div>
      {/* Back nav */}
      <div className="mb-6">
        <Link
          href="/"
          className="text-[12px] font-bold uppercase tracking-widest text-[#999]
                     hover:text-black transition-colors duration-150"
        >
          ← Back to Today&rsquo;s Edition
        </Link>
      </div>

      {/* Date line */}
      {displayDate && (
        <p className="text-[11px] font-bold tracking-[0.12em] uppercase text-[#999] mb-4">
          {displayDate}
        </p>
      )}

      {/* Full category with subcategory filter */}
      <SubcategoryFilter sector={category} articles={articles} />

      {/* Bottom back link */}
      <div className="mt-6 pt-4 border-t border-[#e0e0e0]">
        <Link
          href="/"
          className="text-[12px] font-bold uppercase tracking-widest text-[#999]
                     hover:text-black transition-colors duration-150"
        >
          ← Back to Today&rsquo;s Edition
        </Link>
      </div>
    </div>
  );
}
