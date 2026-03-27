/**
 * SQLite reader for the shared articles database.
 * Uses better-sqlite3 which is synchronous — perfect for Next.js server components.
 */

import Database from "better-sqlite3";
import path from "path";
import { Article, GroupedArticles } from "@/types/article";

const CATEGORY_ORDER = [
  "Model Releases",
  "Products & Features",
  "RAG, Agents & Techniques",
  "Research & Open Source",
  "Chips & Infrastructure",
  "AI Applications",
  "Policy & Governance",
  "Security & Threats",
  "Business & Funding",
  "Tutorials & Guides",
  "Trending Repos & Papers",
] as const;

function getDbPath(): string {
  const envPath = process.env.DB_PATH ?? "../data/articles.db";
  if (path.isAbsolute(envPath)) return envPath;
  return path.resolve(process.cwd(), envPath);
}

function openDb(): Database.Database {
  const dbPath = getDbPath();
  return new Database(dbPath, { readonly: true });
}

/** Fetch articles for a given date, split by category. */
export function getArticlesByDate(date?: string): GroupedArticles {
  const db = openDb();

  const targetDate = date ?? new Date().toISOString().slice(0, 10);

  const rows = db
    .prepare(
      `SELECT * FROM articles
       WHERE COALESCE(edition_date, DATE(fetched_at)) = ?
         AND is_featured = 1
       ORDER BY sector, COALESCE(score, 0) DESC, COALESCE(published_at, fetched_at) DESC`
    )
    .all(targetDate) as Article[];

  db.close();

  const grouped = Object.fromEntries(
    CATEGORY_ORDER.map((c) => [c, [] as Article[]])
  ) as unknown as GroupedArticles;

  const g = grouped as unknown as Record<string, Article[]>;
  for (const row of rows) {
    const cat = row.sector;
    if (cat in g) {
      g[cat].push(row);
    }
  }

  return grouped;
}

/** Return the most recent date that has articles. */
export function getLatestDate(): string | null {
  const db = openDb();
  const row = db
    .prepare(
      `SELECT COALESCE(edition_date, DATE(fetched_at)) as d
       FROM articles
       ORDER BY fetched_at DESC
       LIMIT 1`
    )
    .get() as { d: string } | undefined;
  db.close();
  return row?.d ?? null;
}

/** Total article count in the database. */
export function getTotalCount(): number {
  const db = openDb();
  const row = db.prepare("SELECT COUNT(*) as n FROM articles").get() as { n: number };
  db.close();
  return row.n;
}

export { CATEGORY_ORDER };

/** Slug ↔ category mapping for URL routing */
export const CATEGORY_SLUGS: Record<string, string> = {
  "model-releases":           "Model Releases",
  "products-and-features":    "Products & Features",
  "rag-agents-and-techniques":"RAG, Agents & Techniques",
  "research-and-open-source": "Research & Open Source",
  "chips-and-infrastructure": "Chips & Infrastructure",
  "ai-applications":          "AI Applications",
  "policy-and-governance":    "Policy & Governance",
  "security-and-threats":     "Security & Threats",
  "business-and-funding":     "Business & Funding",
  "tutorials-and-guides":     "Tutorials & Guides",
  "github-trending":          "Trending Repos & Papers",
};

export function categoryToSlug(category: string): string {
  return (
    Object.entries(CATEGORY_SLUGS).find(([, v]) => v === category)?.[0] ??
    category.toLowerCase().replace(/[^a-z0-9]+/g, "-")
  );
}
