"""Email sending service – SMTP with dev fallback (console logging)."""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

from app.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str, text: str) -> None:
    """Blocking SMTP send – called via run_in_executor."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.ehlo()
        if settings.smtp_port != 465:
            server.starttls()
            server.ehlo()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, [to], msg.as_string())


async def send_email(to: str, subject: str, html: str, text: str = "") -> None:
    """Send an email asynchronously. Logs to console if SMTP not configured."""
    if not settings.smtp_host:
        logger.info(
            "[DEV EMAIL] To: %s | Subject: %s\n%s",
            to,
            subject,
            text or html,
        )
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(_send_smtp, to, subject, html, text))


# ── Wiadomości ─────────────────────────────────────────────────────────────────

def _reset_html(link: str) -> str:
    return f"""
<html><body style="font-family:Arial,sans-serif;color:#1e293b;max-width:480px;margin:auto">
  <div style="background:#2563eb;padding:20px 24px;border-radius:8px 8px 0 0">
    <h2 style="color:#fff;margin:0">Źródło – System Parafialny</h2>
  </div>
  <div style="background:#fff;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
    <h3>Reset hasła</h3>
    <p>Otrzymaliśmy prośbę o reset hasła dla Twojego konta. Kliknij poniższy przycisk,
       aby ustawić nowe hasło. Link jest ważny przez <strong>1 godzinę</strong>.</p>
    <p style="text-align:center;margin:28px 0">
      <a href="{link}"
         style="background:#2563eb;color:#fff;padding:12px 28px;border-radius:6px;
                text-decoration:none;font-weight:bold;display:inline-block">
        Zresetuj hasło
      </a>
    </p>
    <p style="color:#64748b;font-size:12px">Jeśli to nie Ty wysłałeś(aś) tę prośbę, zignoruj tę wiadomość.</p>
    <p style="color:#64748b;font-size:12px">Link: <a href="{link}">{link}</a></p>
  </div>
</body></html>
"""


async def send_reset_email(to: str, token: str) -> None:
    base = settings.app_url.rstrip("/")
    link = f"{base}/reset-hasla/zmien?token={token}"
    await send_email(
        to=to,
        subject="Źródło – reset hasła",
        html=_reset_html(link),
        text=f"Zresetuj hasło: {link}\n\nLink ważny 1 godzinę.",
    )
