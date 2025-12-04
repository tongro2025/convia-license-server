"""Email utility functions."""

import logging

logger = logging.getLogger(__name__)


def send_magic_link_email(email: str, token: str, license_key: str) -> bool:
    """Send magic link email to user.

    Args:
        email: Recipient email address
        token: Magic token for license activation
        license_key: License key (paddle_subscription_id)

    Returns:
        True if email was sent successfully (or logged), False otherwise

    TODO:
        - Implement actual email sending using SMTP or SendGrid API
        - Configure SMTP settings in config.py or environment variables
        - Create email template with magic link URL
        - Handle email sending errors properly
    """
    # Placeholder implementation - just log for now
    magic_link_url = f"https://convia.vip/license/portal?token={token}"
    
    logger.info(
        f"Magic link email would be sent to {email}:\n"
        f"  License Key: {license_key}\n"
        f"  Magic Link: {magic_link_url}\n"
        f"  Token: {token}"
    )
    
    # TODO: Implement actual email sending
    # Example with SMTP:
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    # 
    # msg = MIMEMultipart()
    # msg['From'] = settings.smtp_from_email
    # msg['To'] = email
    # msg['Subject'] = "Your Convia License Activation Link"
    # 
    # body = f"Click here to activate your license: {magic_link_url}"
    # msg.attach(MIMEText(body, 'plain'))
    # 
    # server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    # server.starttls()
    # server.login(settings.smtp_username, settings.smtp_password)
    # server.send_message(msg)
    # server.quit()
    
    return True


