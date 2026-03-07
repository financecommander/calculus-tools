"""SendGrid automation — core email-sending logic.

No CrewAI dependency.  Importable as::

    from calculus_tools.sendgrid import send_email, send_batch
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None  # type: ignore[misc]
    Mail = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Sent-tracker for dedup
# ---------------------------------------------------------------------------

_SENT_TRACKER = Path("data/sent/sent_tracker.json")


def load_sent_tracker() -> set[str]:
    """Load set of already-sent email addresses."""
    try:
        return set(json.loads(_SENT_TRACKER.read_text()))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_sent_tracker(sent: set[str]) -> None:
    """Persist set of sent email addresses."""
    _SENT_TRACKER.parent.mkdir(parents=True, exist_ok=True)
    _SENT_TRACKER.write_text(json.dumps(sorted(sent)))


# ---------------------------------------------------------------------------
# Single email
# ---------------------------------------------------------------------------

def send_email(
    to_email: str,
    name: str = "there",
    company: str = "",
    subject: str = "",
    html_content: str = "",
    from_email: Optional[str] = None,
) -> tuple[bool, str]:
    """Send one email via SendGrid.  Returns ``(success, message)``."""
    if SendGridAPIClient is None:
        return False, "sendgrid package not installed (pip install sendgrid)"

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        return False, "SENDGRID_API_KEY env var not set"

    from_email = from_email or os.getenv("EMAIL_FROM", "sean@calculusoutreach.com")

    if not subject:
        subject = (
            f"AI-Powered Solutions for {company}"
            if company
            else "AI-Powered Solutions for Your Business"
        )

    if not html_content:
        html_content = (
            f"<p>Hi {name},</p>"
            f"<p>I'm reaching out because we've built an AI orchestration platform "
            f"that helps companies like {company or 'yours'} automate complex "
            f"workflows — from code generation to financial analysis — at a "
            f"fraction of the cost of single-model approaches.</p>"
            f"<p>Would you be open to a 15-minute call this week?</p>"
            f"<p>Best,<br>Sean<br>Calculus Holdings</p>"
        )

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        if response.status_code == 202:
            return True, f"Sent to {to_email} (202)"
        return False, f"Unexpected status {response.status_code}"
    except Exception as exc:
        return False, f"SendGrid error: {exc}"


# ---------------------------------------------------------------------------
# Batch campaign
# ---------------------------------------------------------------------------

def send_batch(
    leads: list[dict],
    dry_run: bool = True,
    limit: int = 30,
) -> dict:
    """Run an email campaign over a list of lead dicts.

    Each lead may have keys: ``email`` (required), ``name``, ``company``.
    Automatically deduplicates against the sent tracker.

    Returns ``{"sent": int, "failed": int, "details": [...]}``
    """
    sent_set = load_sent_tracker()
    details: list[str] = []
    sent_count = 0
    failed_count = 0

    for lead in leads[:limit]:
        email = lead.get("email", "")
        if not email or email in sent_set:
            continue

        name = lead.get("name", "there")
        company = lead.get("company", "")

        if dry_run:
            details.append(f"DRY RUN — would send to {email} ({name})")
            sent_count += 1
        else:
            ok, msg = send_email(email, name, company)
            details.append(msg)
            if ok:
                sent_count += 1
                sent_set.add(email)
            else:
                failed_count += 1

    if not dry_run:
        save_sent_tracker(sent_set)

    return {"sent": sent_count, "failed": failed_count, "details": details}


__all__ = [
    "send_email",
    "send_batch",
    "load_sent_tracker",
    "save_sent_tracker",
]
