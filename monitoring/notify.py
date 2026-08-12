"""Alert delivery over free channels.

Primary: SMTP email via any free account (Gmail smtp.gmail.com:587 with an
App Password, or Outlook smtp.office365.com:587).

Free SMS: add the carrier email-to-SMS gateway address to MAIL_TO, e.g.
    9198XXXXXXXX@jio.com   (Reliance Jio)
    9198XXXXXXXX@airtelindia.com  (Airtel - legacy/best effort)
    9194XXXXXXXX@bsnlmsg.in (BSNL)
Email-to-SMS is free but best-effort / carrier-dependent; keep a normal email
address in MAIL_TO as the reliable copy.

Alert bodies are deliberately terse: WHAT / SINCE / WHERE.
"""
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

from .config import settings
from .state import log_alert


def _configured():
    s = settings()
    return bool(s["smtp_host"] and s["smtp_user"] and s["smtp_password"] and s["mail_to"])


def send(subject, body):
    """Send an alert to all recipients. Always logs to reports/alerts.log.

    Returns True if email was dispatched, False if SMTP is not configured
    (alert is still logged locally).
    """
    log_alert("ALERT %s\n    %s" % (subject, body.replace("\n", " | ")))
    if not _configured():
        return False

    s = settings()
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = s["smtp_from"]
    msg["To"] = ", ".join(s["mail_to"])
    msg["Date"] = formatdate(localtime=True)

    try:
        if s["smtp_port"] == 465:
            server = smtplib.SMTP_SSL(s["smtp_host"], s["smtp_port"], timeout=30)
        else:
            server = smtplib.SMTP(s["smtp_host"], s["smtp_port"], timeout=30)
            server.starttls()
        server.login(s["smtp_user"], s["smtp_password"])
        server.sendmail(s["smtp_from"], s["mail_to"], msg.as_string())
        server.quit()
        return True
    except Exception as e:  # pragma: no cover - depends on external SMTP
        log_alert("SMTP SEND FAILED: %s" % e)
        return False


def incident_body(what, since, where, detail=""):
    lines = [
        "WHAT : %s" % what,
        "SINCE: %s" % since,
        "WHERE: %s" % where,
    ]
    if detail:
        lines.append("DETAIL: %s" % detail)
    return "\n".join(lines)


def recovery_body(what, where):
    return "\n".join([
        "RESOLVED",
        "WHAT : %s" % what,
        "WHERE: %s" % where,
        "The feed has recovered. No action needed.",
    ])


def digests(ok_lines, warn_lines, crit_lines):
    """Terse daily digest: only issues, one line each (daily report email)."""
    parts = []
    if crit_lines:
        parts.append("CRITICAL:\n  " + "\n  ".join(crit_lines))
    if warn_lines:
        parts.append("WARN:\n  " + "\n  ".join(warn_lines))
    if not parts:
        parts.append("No issues detected in the last 24h.")
    return "\n\n".join(parts)
