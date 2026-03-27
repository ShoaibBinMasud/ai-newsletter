/**
 * Subscriber management — stores emails in the shared articles.db.
 * Uses better-sqlite3 (synchronous) — server-side only.
 */

import Database from "better-sqlite3";
import path from "path";

function getDbPath(): string {
  const envPath = process.env.DB_PATH ?? "../data/articles.db";
  if (path.isAbsolute(envPath)) return envPath;
  return path.resolve(process.cwd(), envPath);
}

function openDb(): Database.Database {
  return new Database(getDbPath());
}

/** Ensure the subscribers table exists (idempotent). */
export function initSubscribersTable(): void {
  const db = openDb();
  db.exec(`
    CREATE TABLE IF NOT EXISTS subscribers (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      email         TEXT    UNIQUE NOT NULL,
      subscribed_at TEXT    NOT NULL DEFAULT (datetime('now'))
    )
  `);
  db.close();
}

export type SubscribeResult = "ok" | "duplicate";

/** Insert a new subscriber. Returns "duplicate" if the email already exists. */
export function addSubscriber(email: string): SubscribeResult {
  initSubscribersTable();
  const db = openDb();
  try {
    db.prepare("INSERT INTO subscribers (email) VALUES (?)").run(email);
    return "ok";
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "";
    if (msg.includes("UNIQUE constraint failed")) return "duplicate";
    throw err;
  } finally {
    db.close();
  }
}

/** Return all subscribers (for admin use). */
export function listSubscribers(): { id: number; email: string; subscribed_at: string }[] {
  initSubscribersTable();
  const db = openDb();
  const rows = db
    .prepare("SELECT id, email, subscribed_at FROM subscribers ORDER BY subscribed_at DESC")
    .all() as { id: number; email: string; subscribed_at: string }[];
  db.close();
  return rows;
}
