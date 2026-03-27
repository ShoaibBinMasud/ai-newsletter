"""
Builds the HTML email from the latest edition's featured articles.
Saves a preview to data/email_YYYY-MM-DD.html and optionally sends via SMTP
or creates a draft in Beehiiv.

Usage:
    python email_builder.py              # save preview for latest edition
    python email_builder.py --send       # save preview + send via Gmail
    python email_builder.py --beehiiv    # save preview + create Beehiiv draft
    python email_builder.py --date 2026-03-24   # specific edition date

Optional sponsor block — set in .env:
    SPONSOR_NAME=Acme Corp
    SPONSOR_TEXT=One-line pitch for the sponsor.
    SPONSOR_URL=https://example.com

Beehiiv API — set in .env (Enterprise plan required):
    BEEHIIV_API_KEY=...
    BEEHIIV_PUBLICATION_ID=pub_...
"""

import json
import os
import sqlite3
import smtplib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

from db.storage import get_db_path

SPONSOR_NAME = os.getenv("SPONSOR_NAME", "")
SPONSOR_TEXT = os.getenv("SPONSOR_TEXT", "")
SPONSOR_URL  = os.getenv("SPONSOR_URL", "")

CATEGORY_META = {
    "Model Releases":            {"label": "Model Releases",            "emoji": "🚀", "color": "#2563eb"},
    "Products & Features":       {"label": "Products & Features",       "emoji": "⚡", "color": "#7c3aed"},
    "RAG, Agents & Techniques":  {"label": "RAG, Agents & Techniques",  "emoji": "🔧", "color": "#0891b2"},
    "Research & Open Source":    {"label": "Research & Open Source",    "emoji": "🔬", "color": "#059669"},
    "Chips & Infrastructure":    {"label": "Chips & Infrastructure",    "emoji": "💻", "color": "#d97706"},
    "AI Applications":           {"label": "AI Applications",           "emoji": "🌐", "color": "#6b7280"},
    "Productivity & Efficiency": {"label": "Productivity & Efficiency", "emoji": "📈", "color": "#0d9488"},
    "Policy & Governance":       {"label": "Policy & Governance",       "emoji": "🏛️", "color": "#4f46e5"},
    "Security & Threats":        {"label": "Security & Threats",        "emoji": "🔐", "color": "#dc2626"},
    "Business & Funding":        {"label": "Business & Funding",        "emoji": "💼", "color": "#15803d"},
    "Tutorials & Guides":        {"label": "Tutorials & Guides",        "emoji": "📖", "color": "#0369a1"},
    "Trending Repos & Papers":   {"label": "Trending Repos & Papers",   "emoji": "🐙", "color": "#334155"},
}

CATEGORY_ORDER = [
    "Model Releases",
    "Products & Features",
    "RAG, Agents & Techniques",
    "Research & Open Source",
    "Chips & Infrastructure",
    "AI Applications",
    "Productivity & Efficiency",
    "Policy & Governance",
    "Security & Threats",
    "Business & Funding",
    "Tutorials & Guides",
    "Trending Repos & Papers",
]

# Backward compatibility alias
SECTOR_ORDER = CATEGORY_ORDER

ORANGE      = "#f74904"
BLACK       = "#0a0a0a"
DARK_GRAY   = "#374151"
GRAY        = "#6b7280"
LIGHT_GRAY  = "#e5e7eb"
BG          = "#f1f5f9"
WHITE       = "#ffffff"


# =============================================================================
# Database helpers
# =============================================================================

def get_latest_edition_date(conn: sqlite3.Connection) -> str | None:
    """Return the most recent edition date that has featured articles."""
    row = conn.execute(
        "SELECT COALESCE(edition_date, DATE(fetched_at)) as d "
        "FROM articles WHERE is_featured = 1 "
        "ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def get_featured_articles(conn: sqlite3.Connection, date_str: str) -> dict[str, list[dict]]:
    """Fetch featured articles for the given edition date, grouped by sector."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT * FROM articles
        WHERE is_featured = 1
          AND COALESCE(edition_date, DATE(fetched_at)) = ?
        ORDER BY sector, COALESCE(score, 0) DESC
        """,
        (date_str,),
    ).fetchall()

    grouped: dict[str, list[dict]] = {c: [] for c in CATEGORY_ORDER}
    for row in rows:
        category = row["sector"]  # sector column stores category string
        if category in grouped:
            grouped[category].append(dict(row))
    return grouped


# =============================================================================
# HTML building blocks
# =============================================================================

def read_time(text: str) -> str:
    words = len(text.split())
    total_secs = max(30, round(words / 200 * 60))
    mins, secs = divmod(total_secs, 60)
    if mins == 0:
        return f"{secs} sec"
    return f"{mins} min {secs} sec" if secs else f"{mins} min"


def _divider(color: str = LIGHT_GRAY) -> str:
    return (
        f'<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%">'
        f'<tbody><tr><td style="border-top:1px solid {color};height:1px;"></td></tr></tbody></table>'
    )


def _badge(text: str, bg_color: str) -> str:
    """Render a small pill badge with text."""
    return (
        f'<span style="display:inline-block;background-color:{bg_color};color:#ffffff;'
        f'font-family:Helvetica,Arial,sans-serif;font-size:10px;font-weight:700;'
        f'letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;'
        f'border-radius:3px;line-height:1.4;">{text}</span>'
    )


def _sector_header(meta: dict) -> str:
    """Full-width sector heading between article groups."""
    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 12px auto;" width="100%">
      <tbody><tr>
        <td style="padding:24px 0 4px 0;">
          <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                    color:{meta['color']};letter-spacing:1.5px;text-transform:uppercase;
                    margin:0;padding:0;">{meta['emoji']} {meta['label']}</p>
        </td>
      </tr><tr>
        <td>{_divider(meta['color'])}</td>
      </tr></tbody>
    </table>"""


def _article_card(a: dict) -> str:
    """Render a single featured article as a bordered card."""
    category     = a.get("category") or a.get("sector", "")
    meta         = CATEGORY_META.get(category, {"color": DARK_GRAY, "label": ""})
    sector_color = meta["color"]

    title     = (a.get("ai_title") or a.get("title", "")).strip()
    url       = a.get("url", "#")
    source    = a.get("source") or ""
    summary   = (a.get("ai_summary") or a.get("summary") or "").replace("<", "&lt;").replace(">", "&gt;")
    subcategory = a.get("subcategory") or ""

    # Stars row (GitHub only)
    stars_html = ""
    if a.get("is_github") and a.get("stars"):
        stars_html = f"""
        <tr>
          <td style="padding:0 20px 6px 20px;">
            <span style="font-family:Helvetica,Arial,sans-serif;font-size:13px;
                         color:{ORANGE};font-weight:600;">★ {a['stars']:,} stars</span>
          </td>
        </tr>"""

    summary_html = ""
    if summary:
        summary_html = f"""
        <tr>
          <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:22px;
                     color:{DARK_GRAY};padding:10px 20px 0 20px;">{summary}</td>
        </tr>"""

    source_html = (
        f'<span style="font-family:Helvetica,Arial,sans-serif;font-size:11px;color:{GRAY};">'
        f'{source}</span>'
        if source else ""
    )

    # GitHub repo link — shown for HF papers that have an associated repo
    github_url = a.get("github_url") or ""
    github_link_html = (
        f'<a href="{github_url}" style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
        f'color:{GRAY};text-decoration:none;margin-left:12px;" target="_blank">⬡ GitHub →</a>'
        if github_url else ""
    )

    footer_html = f'<td style="padding:8px 20px 14px 20px;" align="right">{source_html}{github_link_html}</td>'

    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 20px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-top:3px solid {sector_color};" width="100%">
      <tbody>
        {stars_html}
        <tr>
          <td style="padding:16px 20px 0 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:17px;font-weight:700;
                      line-height:24px;color:{BLACK};margin:0;">
              <a href="{url}" style="color:{BLACK};text-decoration:none;" target="_blank">{title}</a>
            </p>
          </td>
        </tr>
        {summary_html}
        <tr>{footer_html}</tr>
      </tbody>
    </table>"""


# =============================================================================
# Full email renderer
# =============================================================================

def build_html(grouped: dict[str, list[dict]], date_str: str) -> str:
    """Render the full HTML email."""
    dt           = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = dt.strftime("%B %d, %Y")
    day_name     = dt.strftime("%A")

    all_articles = [a for c in CATEGORY_ORDER for a in grouped.get(c, [])]
    total        = len(all_articles)

    all_text = " ".join((a.get("ai_summary") or a.get("summary") or "") for a in all_articles)
    rt = read_time(all_text) if all_text.strip() else "5 min"

    # ── Sponsor block ─────────────────────────────────────────────────────────
    sponsor_html = ""
    if SPONSOR_NAME:
        sponsor_body = (
            f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            f'line-height:21px;color:{DARK_GRAY};margin:8px 0 0;">{SPONSOR_TEXT}</p>'
            if SPONSOR_TEXT else ""
        )
        cta = (
            f'<tr><td align="center" style="padding:12px 0 0;">'
            f'<a href="{SPONSOR_URL}" style="font-family:Helvetica,Arial,sans-serif;'
            f'font-size:13px;color:{ORANGE};font-weight:700;text-decoration:none;">Learn more →</a>'
            f'</td></tr>'
            if SPONSOR_URL else ""
        )
        sponsor_html = f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 24px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-left:3px solid {ORANGE};" width="100%">
      <tbody>
        <tr>
          <td style="padding:14px 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                      color:{GRAY};text-transform:uppercase;letter-spacing:1px;margin:0 0 4px 0;">
              Sponsored by
            </p>
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;
                      color:{BLACK};margin:0;">{SPONSOR_NAME}</p>
            {sponsor_body}
          </td>
        </tr>
        {cta}
      </tbody>
    </table>"""

    # ── Article cards grouped by sector ──────────────────────────────────────
    article_boxes = ""
    for category in CATEGORY_ORDER:
        articles = grouped.get(category, [])
        if not articles:
            continue
        article_boxes += _sector_header(CATEGORY_META[category])
        for a in articles:
            article_boxes += _article_card(a)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta content="IE=edge" http-equiv="X-UA-Compatible">
  <meta content="width=device-width, initial-scale=1.0" name="viewport">
  <title>AI Daily — {display_date}</title>
</head>
<body style="margin:0;padding:0;background-color:{BG};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<table bgcolor="{BG}" border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%">
<tbody><tr>
<td align="center" style="padding:24px 12px;">

  <!-- HEADER -->
  <table border="0" cellpadding="0" cellspacing="0" role="presentation"
         style="max-width:600px;margin:0 auto 24px auto;background-color:{BLACK};" width="100%">
    <tbody><tr>
      <td style="padding:28px 24px 24px 24px;">
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                  letter-spacing:2px;text-transform:uppercase;color:{ORANGE};margin:0 0 12px 0;">
          Daily Newsletter
        </p>
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:28px;font-weight:900;
                  letter-spacing:-0.5px;color:{WHITE};margin:0 0 4px 0;line-height:1.1;">
          AI Daily
        </p>
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;color:#9ca3af;
                  margin:0 0 20px 0;">{day_name}, {display_date}</p>
        {_divider("#374151")}
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:23px;
                  color:#d1d5db;margin:16px 0 0 0;">
          Good morning. Here are today's <strong style="color:{WHITE};">{total} most important AI stories</strong>
          — curated and summarized. {rt} read.
        </p>
      </td>
    </tr></tbody>
  </table>

  {sponsor_html}

  <!-- ARTICLES -->
  {article_boxes}

  <!-- FOOTER -->
  <table border="0" cellpadding="0" cellspacing="0" role="presentation"
         style="max-width:600px;margin:0 auto 16px auto;" width="100%">
    <tbody><tr>
      <td align="center" style="padding:20px 0;font-family:Helvetica,Arial,sans-serif;
                                font-size:12px;line-height:18px;color:{GRAY};">
        You're receiving this because you subscribed to AI Daily.<br>
        <a href="#" style="color:{GRAY};text-decoration:underline;">Unsubscribe</a>
      </td>
    </tr></tbody>
  </table>

</td>
</tr></tbody>
</table>
</body>
</html>"""


# =============================================================================
# Output helpers
# =============================================================================

def save_preview(html: str, date_str: str) -> str:
    db_path  = get_db_path()
    data_dir = os.path.dirname(db_path)
    os.makedirs(data_dir, exist_ok=True)
    preview_path = os.path.join(data_dir, f"email_{date_str}.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    return preview_path


def send_email(html: str, date_str: str) -> None:
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    email_to   = os.getenv("EMAIL_TO")

    if not all([gmail_user, gmail_pass, email_to]):
        print("  [!] Email not sent — set GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_TO in .env")
        return

    dt           = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = dt.strftime("%B %d, %Y")

    msg            = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Daily — {display_date}"
    msg["From"]    = gmail_user
    msg["To"]      = email_to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, email_to, msg.as_string())
        print(f"  ✓ Email sent to {email_to}")
    except Exception as e:
        print(f"  [!] Failed to send email: {e}")


def send_to_beehiiv(html: str, date_str: str) -> None:
    """
    Create a draft post in Beehiiv via their Send API.

    Requires:
      BEEHIIV_API_KEY         — API key from Beehiiv dashboard
      BEEHIIV_PUBLICATION_ID  — Publication ID (e.g. pub_xxxxxxxx)

    Note: Beehiiv's Send API is an Enterprise-plan feature.
    Request access at https://app.beehiiv.com/settings/integrations/api
    """
    api_key = os.getenv("BEEHIIV_API_KEY")
    pub_id  = os.getenv("BEEHIIV_PUBLICATION_ID")

    if not api_key or not pub_id:
        print(
            "  [!] Beehiiv not configured — set BEEHIIV_API_KEY and "
            "BEEHIIV_PUBLICATION_ID in .env\n"
            "      Note: Beehiiv Send API requires an Enterprise plan."
        )
        return

    dt           = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = dt.strftime("%B %d, %Y")

    payload = json.dumps({
        "title":        f"AI Daily — {display_date}",
        "body_content": html,
        "status":       "draft",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.beehiiv.com/v2/publications/{pub_id}/posts",
        data=payload,
        headers={
            "Authorization":  f"Bearer {api_key}",
            "Content-Type":   "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result  = json.loads(resp.read().decode("utf-8"))
            post_id = result.get("data", {}).get("id", "unknown")
            print(f"  ✓ Beehiiv draft created — post ID: {post_id}")
            print(f"    Review it at: https://app.beehiiv.com/posts/{post_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  [!] Beehiiv API error {e.code}: {body[:300]}")
    except Exception as e:
        print(f"  [!] Beehiiv request failed: {e}")


# =============================================================================
# Entry point
# =============================================================================

def main() -> None:
    # Parse --date YYYY-MM-DD flag
    date_override: str | None = None
    args = sys.argv[1:]
    if "--date" in args:
        idx = args.index("--date")
        if idx + 1 < len(args):
            date_override = args[idx + 1]

    db_path = get_db_path()
    conn    = sqlite3.connect(db_path)

    # Determine target edition date
    if date_override:
        edition_date = date_override
    else:
        edition_date = get_latest_edition_date(conn)

    if not edition_date:
        print("  [!] No featured articles found in the database. Run main.py first.")
        conn.close()
        return

    print(f"Building email for edition: {edition_date}")

    grouped = get_featured_articles(conn, edition_date)
    conn.close()

    total = sum(len(v) for v in grouped.values())
    if total == 0:
        print(f"  [!] No featured articles found for edition {edition_date}. Run main.py first.")
        return

    active_categories = [c for c in CATEGORY_ORDER if grouped[c]]
    print(f"  → {total} articles across {len(active_categories)} categories: {', '.join(active_categories)}")

    html = build_html(grouped, edition_date)

    preview_path = save_preview(html, edition_date)
    print(f"  ✓ Preview saved: {preview_path}")

    if "--send" in args:
        print("Sending email via Gmail...")
        send_email(html, edition_date)

    if "--beehiiv" in args:
        print("Creating Beehiiv draft...")
        send_to_beehiiv(html, edition_date)


if __name__ == "__main__":
    main()
