"""
Email notification sender for claimed leads via Brevo (free tier: 300/day).
"""
import logging
import requests

from config import Config

logger = logging.getLogger(__name__)


def send_lead_email(lead_info: dict) -> bool:
    """Send a notification email to the claimed lead. Returns True on success."""
    if not Config.EMAIL_ENABLED:
        logger.info("Email notifications disabled, skipping.")
        return False

    recipient = lead_info.get("email", "").strip()
    if not recipient:
        logger.warning("No lead email address found, cannot send notification.")
        return False

    name = lead_info.get("name", "")
    greeting = f"Hello {name},\n\n" if name else "Hello,\n\n"

    body = (
        greeting
        + "Thank you for your interest in Prestige Generatrices.\n\n"
        + "One of our team members will contact you shortly.\n\n"
        + "Best regards,\n"
        + "Prestige Generatrices Team"
    )

    payload = {
        "sender": {"name": "Prestige Generatrices", "email": Config.EMAIL_FROM},
        "to": [{"email": recipient}],
        "subject": "We received your request — our team will contact you shortly",
        "textContent": body,
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": Config.BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"✉ Email sent to {recipient}")
        return True

    except requests.HTTPError as e:
        logger.error(f"Brevo API error {response.status_code}: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False
