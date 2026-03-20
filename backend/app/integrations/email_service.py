"""Email integration — routes through MailHog in development."""

import structlog

from app.config import get_settings

logger = structlog.get_logger()


async def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html: bool = False,
) -> bool:
    """Send an email. In dev mode, logs the email and sends via MailHog SMTP."""
    settings = get_settings()

    if settings.environment == "development":
        logger.info(
            "email_sent_dev",
            to=to,
            subject=subject,
            body_preview=body[:100],
        )
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body, "html" if html else "plain")
            msg["Subject"] = subject
            msg["From"] = "noreply@finshield.dev"
            msg["To"] = to

            with smtplib.SMTP("localhost", 1025) as server:
                server.send_message(msg)
            return True
        except Exception as exc:
            logger.warning("email_send_failed", error=str(exc))
            return False

    logger.info("email_send_skipped", environment=settings.environment)
    return False


async def send_alert_notification(
    *,
    to: str,
    alert_title: str,
    alert_severity: str,
    alert_id: str,
) -> bool:
    subject = f"[FinShield] {alert_severity.upper()} Alert: {alert_title}"
    body = (
        f"<h2>Fraud Alert Notification</h2>"
        f"<p><strong>Title:</strong> {alert_title}</p>"
        f"<p><strong>Severity:</strong> {alert_severity}</p>"
        f"<p><strong>Alert ID:</strong> {alert_id}</p>"
        f"<p>Please review this alert in the FinShield dashboard.</p>"
    )
    return await send_email(to=to, subject=subject, body=body, html=True)
