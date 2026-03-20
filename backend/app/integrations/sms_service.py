"""SMS integration stub — logs in development, would use Azure Communication Services in production."""

import structlog

logger = structlog.get_logger()


async def send_sms(*, to: str, message: str) -> bool:
    """Send an SMS. Currently a stub that logs the message."""
    logger.info("sms_sent_stub", to=to, message_preview=message[:80])
    return True


async def send_alert_sms(*, to: str, alert_title: str, alert_severity: str) -> bool:
    message = f"[FinShield] {alert_severity.upper()}: {alert_title}. Check dashboard for details."
    return await send_sms(to=to, message=message)
