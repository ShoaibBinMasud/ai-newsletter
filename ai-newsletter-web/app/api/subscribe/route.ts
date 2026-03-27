import { NextRequest, NextResponse } from "next/server";
import nodemailer from "nodemailer";
import { addSubscriber } from "@/lib/subscribers";

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function welcomeHtml(email: string): string {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Helvetica Neue,Helvetica,Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr><td align="center" style="padding:32px 16px">
      <table width="560" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;width:100%">

        <!-- Top bar -->
        <tr><td style="background:#f3f4f6;text-align:center;padding:8px;font-size:11px;color:#9ca3af">
          AI Daily · Your Daily Intelligence Digest
        </td></tr>

        <!-- Header -->
        <tr><td style="background:#000;padding:24px 32px">
          <span style="font-size:22px;font-weight:900;color:#fff;letter-spacing:-0.5px">AI Daily</span><br>
          <span style="font-size:11px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.12em">Intelligence Digest</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="background:#fff;padding:32px;border:1px solid #e5e7eb;border-top:none">
          <p style="font-size:22px;font-weight:800;color:#111;margin:0 0 16px;letter-spacing:-0.3px">
            You&rsquo;re subscribed! 🎉
          </p>
          <p style="font-size:15px;color:#444;line-height:1.75;margin:0 0 16px">
            Welcome to <strong>AI Daily</strong> — a curated daily briefing on the most important AI news, model releases, business moves, developer tools, and security stories.
          </p>
          <p style="font-size:15px;color:#444;line-height:1.75;margin:0 0 28px">
            Every morning at <strong>7 AM</strong> we send a fresh edition across four sections:
          </p>

          <!-- Sector list -->
          <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin-bottom:28px">
            <tr>
              <td style="padding:10px 14px;border:1px solid #e5e7eb;font-size:14px;color:#111;font-weight:600">⚡️ Top AI News</td>
            </tr>
            <tr>
              <td style="padding:10px 14px;border:1px solid #e5e7eb;border-top:none;font-size:14px;color:#111;font-weight:600">💼 AI Business</td>
            </tr>
            <tr>
              <td style="padding:10px 14px;border:1px solid #e5e7eb;border-top:none;font-size:14px;color:#111;font-weight:600">🛠️ Dev &amp; Repos</td>
            </tr>
            <tr>
              <td style="padding:10px 14px;border:1px solid #e5e7eb;border-top:none;font-size:14px;color:#111;font-weight:600">🔐 Security</td>
            </tr>
          </table>

          <!-- CTA -->
          <table cellpadding="0" cellspacing="0" role="presentation">
            <tr><td style="background:#f74904">
              <a href="${siteUrl}" style="display:inline-block;padding:13px 26px;color:#fff;font-size:14px;font-weight:700;text-decoration:none">
                Read Today&rsquo;s Edition &rarr;
              </a>
            </td></tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:20px 32px;text-align:center">
          <p style="font-size:11px;color:#9ca3af;margin:0">
            You subscribed with ${email}.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

async function sendWelcomeEmail(to: string): Promise<void> {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) return; // email creds are optional locally

  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: { user, pass },
  });

  await transporter.sendMail({
    from: `"AI Daily" <${user}>`,
    to,
    subject: "Welcome to AI Daily — you're subscribed!",
    html: welcomeHtml(to),
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const email =
    typeof body.email === "string" ? body.email.trim().toLowerCase() : "";

  if (!isValidEmail(email)) {
    return NextResponse.json({ error: "Please enter a valid email address." }, { status: 400 });
  }

  const result = addSubscriber(email);

  if (result === "duplicate") {
    return NextResponse.json(
      { error: "This email is already subscribed." },
      { status: 409 }
    );
  }

  // Fire-and-forget — don't make the user wait on SMTP
  sendWelcomeEmail(email).catch((err) =>
    console.error("[subscribe] welcome email failed:", err)
  );

  return NextResponse.json({ ok: true });
}
