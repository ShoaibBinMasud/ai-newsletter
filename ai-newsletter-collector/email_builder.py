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
from config import TOP_STORY_COUNT, OPENER_MODEL, OPENER_TEMPERATURE

SPONSOR_NAME    = os.getenv("SPONSOR_NAME", "")
SPONSOR_TEXT    = os.getenv("SPONSOR_TEXT", "")
SPONSOR_URL     = os.getenv("SPONSOR_URL", "")
UNSUBSCRIBE_URL = os.getenv("UNSUBSCRIBE_URL", "")
SITE_URL        = os.getenv("SITE_URL", "")

# Keep CATEGORY_ORDER and CATEGORY_META for backward compatibility (used by main.py)
CATEGORY_META = {
    "Model Releases":            {"label": "Model Releases",            "emoji": "\U0001f680", "color": "#2563eb"},
    "Products & Features":       {"label": "Products & Features",       "emoji": "\u26a1",     "color": "#7c3aed"},
    "RAG, Agents & Techniques":  {"label": "RAG, Agents & Techniques",  "emoji": "\U0001f527", "color": "#0891b2"},
    "Research & Open Source":    {"label": "Research & Open Source",    "emoji": "\U0001f52c", "color": "#059669"},
    "Chips & Infrastructure":    {"label": "Chips & Infrastructure",    "emoji": "\U0001f4bb", "color": "#d97706"},
    "AI Applications":           {"label": "AI Applications",           "emoji": "\U0001f310", "color": "#6b7280"},
    "Productivity & Efficiency": {"label": "Productivity & Efficiency", "emoji": "\U0001f4c8", "color": "#0d9488"},
    "Policy & Governance":       {"label": "Policy & Governance",       "emoji": "\U0001f3db\ufe0f", "color": "#4f46e5"},
    "Security & Threats":        {"label": "Security & Threats",        "emoji": "\U0001f510", "color": "#dc2626"},
    "Business & Funding":        {"label": "Business & Funding",        "emoji": "\U0001f4bc", "color": "#15803d"},
    "Tutorials & Guides":        {"label": "Tutorials & Guides",        "emoji": "\U0001f4d6", "color": "#0369a1"},
    "Trending Repos & Papers":   {"label": "Trending Repos & Papers",   "emoji": "\U0001f419", "color": "#334155"},
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
ACCENT      = "#2563eb"


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


def get_featured_articles(conn: sqlite3.Connection, date_str: str) -> tuple[list[dict], list[dict]]:
    """Fetch featured articles for the given edition date, split into (top_stories, quick_hits)."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT * FROM articles
        WHERE is_featured = 1
          AND COALESCE(edition_date, DATE(fetched_at)) = ?
        ORDER BY COALESCE(score, 0) DESC
        """,
        (date_str,),
    ).fetchall()

    all_articles = [dict(row) for row in rows]

    # Split by is_top_story flag if available, else fall back to score-based split
    top_stories = [a for a in all_articles if a.get("is_top_story")]
    quick_hits  = [a for a in all_articles if not a.get("is_top_story")]

    # Backward compat: if no articles have is_top_story set, split by score rank
    if not top_stories and all_articles:
        top_stories = all_articles[:TOP_STORY_COUNT]
        quick_hits  = all_articles[TOP_STORY_COUNT:]

    return top_stories, quick_hits


# =============================================================================
# LLM opener generation
# =============================================================================

def generate_opener(top_stories: list[dict]) -> str:
    """Call LLM to generate a 2-3 sentence editorial opener based on today's top stories."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not top_stories:
        return _fallback_opener(top_stories)

    from openai import OpenAI
    from collector.prompts import OPENER_PROMPT

    story_lines = "\n".join(
        f"- {a.get('ai_title') or a.get('title', '')}"
        for a in top_stories
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENER_MODEL,
            messages=[{"role": "user", "content": OPENER_PROMPT.format(top_stories=story_lines)}],
            temperature=OPENER_TEMPERATURE,
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        data = json.loads(response.choices[0].message.content)
        opener = data.get("opener", "")
        if opener:
            return opener
    except Exception as exc:
        print(f"  [!] Opener generation failed: {exc}")

    return _fallback_opener(top_stories)


def _fallback_opener(top_stories: list[dict]) -> str:
    """Simple fallback opener when LLM is unavailable."""
    if top_stories:
        lead = top_stories[0].get("ai_title") or top_stories[0].get("title", "")
        return f"Good morning. Today's lead: {lead}. Here's everything you need to know."
    return "Good morning. Here are today's most important AI stories — curated and summarized."


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


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _divider(color: str = LIGHT_GRAY) -> str:
    return (
        f'<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%">'
        f'<tbody><tr><td style="border-top:1px solid {color};height:1px;"></td></tr></tbody></table>'
    )


def _section_divider() -> str:
    """Full-width divider between major sections."""
    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto;" width="100%">
      <tbody><tr>
        <td style="padding:8px 0;">{_divider("#374151")}</td>
      </tr></tbody>
    </table>"""


def _company_tag_badge(tag: str) -> str:
    """Render a small uppercase company tag label."""
    if not tag:
        return ""
    return (
        f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;'
        f'letter-spacing:1.5px;text-transform:uppercase;color:{GRAY};margin:0 0 8px 0;">'
        f'{_esc(tag)}</p>'
    )


def _category_badge(category: str) -> str:
    """Render a colored category badge."""
    if not category or category not in CATEGORY_META:
        return ""
    meta = CATEGORY_META[category]
    return (
        f'<span style="display:inline-block;background-color:{meta["color"]};color:white;'
        f'padding:3px 8px;border-radius:3px;font-family:Helvetica,Arial,sans-serif;'
        f'font-size:10px;font-weight:700;margin-left:4px;">'
        f'{meta["emoji"]} {_esc(meta["label"])}</span>'
    )


def _top_story_card(a: dict) -> str:
    """Render a top story with full treatment."""
    title       = (a.get("ai_title") or a.get("title", "")).strip()
    url         = a.get("url", "#")
    company_tag = a.get("company_tag", "")
    category    = a.get("category", "")
    overview    = _esc(a.get("overview") or a.get("ai_summary") or a.get("summary") or "")
    why_matters = _esc(a.get("why_it_matters", ""))
    og_image    = a.get("og_image", "")
    source      = a.get("source", "")

    # Parse details from JSON string
    details_raw = a.get("details", "[]")
    try:
        details = json.loads(details_raw) if isinstance(details_raw, str) else details_raw
    except (json.JSONDecodeError, TypeError):
        details = []

    # OG image block
    image_html = ""
    if og_image:
        image_html = f"""
        <tr>
          <td style="padding:12px 20px 0 20px;">
            <img src="{og_image}" alt="" width="560" style="display:block;width:100%;max-width:560px;
                 height:auto;border-radius:6px;border:1px solid {LIGHT_GRAY};" />
          </td>
        </tr>"""

    # Details bullets
    details_html = ""
    if details:
        bullets = "".join(
            f'<li style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:22px;'
            f'color:{DARK_GRAY};margin:0 0 6px 0;">{_esc(str(d))}</li>'
            for d in details[:4]
        )
        details_html = f"""
        <tr>
          <td style="padding:12px 20px 0 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;
                      color:{BLACK};margin:0 0 8px 0;">The details:</p>
            <ul style="margin:0;padding:0 0 0 20px;">{bullets}</ul>
          </td>
        </tr>"""

    # Why it matters
    why_html = ""
    if why_matters:
        why_html = f"""
        <tr>
          <td style="padding:12px 20px 0 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;
                      color:{BLACK};margin:0 0 4px 0;">Why it matters:</p>
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:22px;
                      color:{DARK_GRAY};margin:0;">{why_matters}</p>
          </td>
        </tr>"""

    # Source attribution
    source_html = ""
    if source:
        source_html = (
            f'<span style="font-family:Helvetica,Arial,sans-serif;font-size:11px;color:{GRAY};">'
            f'Source: {_esc(source)}</span>'
        )

    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 24px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-radius:8px;" width="100%">
      <tbody>
        <tr>
          <td style="padding:20px 20px 0 20px;">
            {_company_tag_badge(company_tag)}{_category_badge(category)}
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:19px;font-weight:800;
                      line-height:26px;color:{BLACK};margin:0;">
              <a href="{url}" style="color:{BLACK};text-decoration:none;" target="_blank">{_esc(title)}</a>
            </p>
          </td>
        </tr>
        {image_html}
        <tr>
          <td style="padding:12px 20px 0 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;
                      color:{BLACK};margin:0 0 4px 0;">What happened:</p>
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:22px;
                      color:{DARK_GRAY};margin:0;">{overview}</p>
          </td>
        </tr>
        {details_html}
        {why_html}
        <tr>
          <td style="padding:12px 20px 16px 20px;" align="right">{source_html}</td>
        </tr>
      </tbody>
    </table>"""


def _quick_hits_section(articles: list[dict]) -> str:
    """Render the quick hits section with compact one-liner items."""
    if not articles:
        return ""

    items_html = ""
    for a in articles:
        company  = a.get("company_tag", "")
        one_liner = _esc(a.get("one_liner") or a.get("ai_summary") or a.get("summary") or "")
        title    = (a.get("ai_title") or a.get("title", "")).strip()
        url      = a.get("url", "#")

        company_bold = (
            f'<strong style="color:{BLACK};">{_esc(company)}</strong> '
            if company else ""
        )

        # Stars badge for GitHub repos
        stars_html = ""
        if a.get("is_github") and a.get("stars"):
            stars_html = (
                f' <span style="color:{ORANGE};font-weight:600;">'
                f'\u2605 {a["stars"]:,}</span>'
            )

        items_html += f"""
        <tr>
          <td style="padding:12px 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:22px;
                      color:{DARK_GRAY};margin:0;">
              {company_bold}<a href="{url}" style="color:{ACCENT};font-weight:600;
              text-decoration:none;" target="_blank">{_esc(title)}</a>{stars_html}
            </p>
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;line-height:20px;
                      color:{GRAY};margin:4px 0 0 0;">{one_liner}</p>
          </td>
        </tr>
        <tr><td style="padding:0 20px;">{_divider(LIGHT_GRAY)}</td></tr>"""

    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 24px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-radius:8px;" width="100%">
      <tbody>
        <tr>
          <td style="padding:20px 20px 4px 20px;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                      letter-spacing:1.5px;text-transform:uppercase;color:{ACCENT};
                      margin:0;">EVERYTHING ELSE IN AI TODAY</p>
          </td>
        </tr>
        <tr><td style="padding:4px 20px 0 20px;">{_divider(ACCENT)}</td></tr>
        {items_html}
      </tbody>
    </table>"""


def _forward_cta() -> str:
    """Render a forward-to-friend CTA block."""
    if not SITE_URL:
        return ""

    forward_url = f"{SITE_URL}?utm_source=forward&utm_medium=email"
    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 24px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-radius:8px;" width="100%">
      <tbody>
        <tr>
          <td style="padding:16px 20px;text-align:center;">
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;
                      color:{DARK_GRAY};margin:0 0 8px 0;">
              Enjoying this? Forward it to one person who builds with AI.
            </p>
            <a href="{forward_url}" style="font-family:Helvetica,Arial,sans-serif;
               font-size:13px;color:{ORANGE};font-weight:700;text-decoration:none;">
              They can subscribe free \u2192
            </a>
          </td>
        </tr>
      </tbody>
    </table>"""


def _sponsor_block() -> str:
    """Render the sponsor block if configured."""
    if not SPONSOR_NAME:
        return ""

    sponsor_body = ""
    if SPONSOR_TEXT:
        sponsor_body = (
            f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            f'line-height:21px;color:{DARK_GRAY};margin:8px 0 0;">{SPONSOR_TEXT}</p>'
        )

    cta = ""
    if SPONSOR_URL:
        cta = (
            f'<tr><td align="center" style="padding:12px 0 0;">'
            f'<a href="{SPONSOR_URL}" style="font-family:Helvetica,Arial,sans-serif;'
            f'font-size:13px;color:{ORANGE};font-weight:700;text-decoration:none;">'
            f'Learn more \u2192</a></td></tr>'
        )

    return f"""
    <table border="0" cellpadding="0" cellspacing="0" role="presentation"
           style="max-width:600px;margin:0 auto 24px auto;background-color:{WHITE};
                  border:1px solid {LIGHT_GRAY};border-left:3px solid {ORANGE};
                  border-radius:8px;" width="100%">
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


# =============================================================================
# Full email renderer
# =============================================================================

def build_html(top_stories: list[dict], quick_hits: list[dict], date_str: str) -> str:
    """Render the full HTML email in Rundown-style format."""
    dt           = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = dt.strftime("%B %d, %Y")
    day_name     = dt.strftime("%A")

    all_articles = top_stories + quick_hits
    total        = len(all_articles)

    all_text = " ".join(
        (a.get("overview") or a.get("ai_summary") or a.get("summary") or "")
        for a in all_articles
    )
    rt = read_time(all_text) if all_text.strip() else "5 min"

    # ── Generate editorial opener ────────────────────────────────────────────
    opener = generate_opener(top_stories)

    # ── Table of Contents ────────────────────────────────────────────────────
    toc_items = ""
    for a in top_stories:
        title = (a.get("ai_title") or a.get("title", "")).strip()
        toc_items += (
            f'<li style="font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            f'line-height:24px;color:#d1d5db;margin:0 0 2px 0;">{_esc(title)}</li>'
        )

    toc_html = ""
    if toc_items:
        toc_html = f"""
        {_divider("#374151")}
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;font-weight:700;
                  color:{WHITE};margin:16px 0 8px 0;">In today's AI rundown:</p>
        <ul style="margin:0;padding:0 0 0 20px;">{toc_items}</ul>"""

    # ── Top story cards with sponsor inserted after story 2 ──────────────────
    stories_html = ""
    sponsor = _sponsor_block()
    for i, a in enumerate(top_stories):
        # Section divider between stories
        if i > 0:
            stories_html += _section_divider()
        stories_html += _top_story_card(a)
        # Insert sponsor after the 2nd story
        if i == 1 and sponsor:
            stories_html += sponsor

    # If fewer than 2 top stories, place sponsor after all stories
    if len(top_stories) < 2 and sponsor:
        stories_html += sponsor

    # ── Quick hits ───────────────────────────────────────────────────────────
    quick_html = _quick_hits_section(quick_hits)

    # ── Forward CTA ──────────────────────────────────────────────────────────
    forward_html = _forward_cta()

    # ── Web version link ─────────────────────────────────────────────────────
    web_version = ""
    if SITE_URL:
        web_version = (
            f'<p style="text-align:center;margin:0 0 16px 0;">'
            f'<a href="{SITE_URL}" style="font-family:Helvetica,Arial,sans-serif;'
            f'font-size:12px;color:{ACCENT};text-decoration:none;">View in browser \u2192</a></p>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta content="IE=edge" http-equiv="X-UA-Compatible">
  <meta content="width=device-width, initial-scale=1.0" name="viewport">
  <title>AI Daily \u2014 {display_date}</title>
</head>
<body style="margin:0;padding:0;background-color:{BG};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<table bgcolor="{BG}" border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%">
<tbody><tr>
<td align="center" style="padding:24px 12px;">

  {web_version}

  <!-- HEADER -->
  <table border="0" cellpadding="0" cellspacing="0" role="presentation"
         style="max-width:600px;margin:0 auto 24px auto;background-color:{BLACK};border-radius:8px 8px 0 0;" width="100%">
    <tbody><tr>
      <td style="padding:28px 24px 24px 24px;">
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                  letter-spacing:2px;text-transform:uppercase;color:{ORANGE};margin:0 0 12px 0;">
          Built for AI builders
        </p>
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:28px;font-weight:900;
                  letter-spacing:-0.5px;color:{WHITE};margin:0 0 4px 0;line-height:1.1;">
          AI Daily
        </p>
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;color:#9ca3af;
                  margin:0 0 20px 0;">{day_name}, {display_date} \u00b7 {rt} read</p>
        {_divider("#374151")}
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:23px;
                  color:#d1d5db;margin:16px 0 0 0;">
          {_esc(opener)}
        </p>
        {toc_html}
      </td>
    </tr></tbody>
  </table>

  <!-- SECTION LABEL -->
  <table border="0" cellpadding="0" cellspacing="0" role="presentation"
         style="max-width:600px;margin:0 auto 16px auto;" width="100%">
    <tbody><tr>
      <td style="padding:8px 0 0 0;">
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;
                  letter-spacing:1.5px;text-transform:uppercase;color:{DARK_GRAY};margin:0;">
          TOP STORIES
        </p>
      </td>
    </tr><tr>
      <td style="padding:4px 0 0 0;">{_divider(DARK_GRAY)}</td>
    </tr></tbody>
  </table>

  <!-- TOP STORIES -->
  {stories_html}

  <!-- QUICK HITS -->
  {quick_html}

  <!-- FORWARD CTA -->
  {forward_html}

  <!-- FOOTER -->
  <table border="0" cellpadding="0" cellspacing="0" role="presentation"
         style="max-width:600px;margin:0 auto 16px auto;" width="100%">
    <tbody><tr>
      <td align="center" style="padding:20px 0;">
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:20px;
                  color:{DARK_GRAY};margin:0 0 12px 0;">
          That's a wrap for today. See you tomorrow.
        </p>
        <p style="font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:18px;color:{GRAY};margin:0;">
          You're receiving this because you subscribed to AI Daily.<br>
          Hit reply to share feedback or a story tip.<br>
          <a href="{UNSUBSCRIBE_URL or '#'}" style="color:{GRAY};text-decoration:underline;">Unsubscribe</a>
        </p>
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
    msg["Subject"] = f"AI Daily \u2014 {display_date}"
    msg["From"]    = gmail_user
    msg["To"]      = email_to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, email_to, msg.as_string())
        print(f"  \u2713 Email sent to {email_to}")
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
        "title":        f"AI Daily \u2014 {display_date}",
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
            print(f"  \u2713 Beehiiv draft created \u2014 post ID: {post_id}")
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

    top_stories, quick_hits = get_featured_articles(conn, edition_date)
    conn.close()

    total = len(top_stories) + len(quick_hits)
    if total == 0:
        print(f"  [!] No featured articles found for edition {edition_date}. Run main.py first.")
        return

    print(f"  \u2192 {len(top_stories)} top stories + {len(quick_hits)} quick hits")

    html = build_html(top_stories, quick_hits, edition_date)

    preview_path = save_preview(html, edition_date)
    print(f"  \u2713 Preview saved: {preview_path}")

    if "--send" in args:
        print("Sending email via Gmail...")
        send_email(html, edition_date)

    if "--beehiiv" in args:
        print("Creating Beehiiv draft...")
        send_to_beehiiv(html, edition_date)


if __name__ == "__main__":
    main()
