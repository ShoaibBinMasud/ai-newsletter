/**
 * GET /api/articles?date=YYYY-MM-DD
 * Returns articles grouped by sector for the given date.
 */

import { NextRequest, NextResponse } from "next/server";
import { getArticlesByDate, getLatestDate } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const date = searchParams.get("date") ?? getLatestDate() ?? undefined;
    const grouped = getArticlesByDate(date ?? undefined);
    return NextResponse.json({ date, articles: grouped });
  } catch (err) {
    console.error(err);
    return NextResponse.json(
      { error: "Failed to read database. Did you run the collector yet?" },
      { status: 500 }
    );
  }
}
