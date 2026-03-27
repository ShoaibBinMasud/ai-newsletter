export type Category =
  | "Model Releases"
  | "Products & Features"
  | "RAG, Agents & Techniques"
  | "Research & Open Source"
  | "Chips & Infrastructure"
  | "AI Applications"
  | "Policy & Governance"
  | "Security & Threats"
  | "Business & Funding"
  | "Tutorials & Guides"
  | "Trending Repos & Papers";

// Backward compat alias — sector column now stores category string
export type Sector = Category;

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  sector: string;  // stores category string (e.g. "Model Releases")
  summary: string | null;
  ai_title: string | null;
  ai_summary: string | null;
  published_at: string | null;
  fetched_at: string;
  is_github: 0 | 1;
  is_featured: 0 | 1;
  stars: number | null;
  subcategory: string | null;
  score: number | null;
  edition_date: string | null;
  github_url: string | null;
}

export interface GroupedArticles {
  "Model Releases": Article[];
  "Products & Features": Article[];
  "RAG, Agents & Techniques": Article[];
  "Research & Open Source": Article[];
  "Chips & Infrastructure": Article[];
  "AI Applications": Article[];
  "Policy & Governance": Article[];
  "Security & Threats": Article[];
  "Business & Funding": Article[];
  "Tutorials & Guides": Article[];
  "Trending Repos & Papers": Article[];
}
