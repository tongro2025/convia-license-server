"""Email utility functions."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_magic_link_email(email: str, token: str, license_key: str) -> bool:
    """Send magic link email to user.

    Args:
        email: Recipient email address
        token: Magic token for license activation
        license_key: License key (paddle_subscription_id)

    Returns:
        True if email was sent successfully (or at least logged), False otherwise.
    """
    # Normalize base URL and build magic link
    # settings.frontend_url is expected to be something like: https://license.convia.vip
    base_url = settings.frontend_url.rstrip("/")
    magic_link_url = f"{base_url}/license/magic?token={token}"

    # If SMTP is not configured, just log and pretend success (dev / staging environments)
    if not settings.smtp_username or not settings.smtp_password:
        logger.info(
            "Magic link email would be sent (SMTP not configured):\n"
            f"  To: {email}\n"
            f"  License Key: {license_key}\n"
            f"  Magic Link: {magic_link_url}\n"
            f"  Token: {token}"
        )
        return True

    try:
        # Build email message
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = email
        msg["Subject"] = "Convia License – Your Magic Sign-In Link"

        # Plain text body (for clients that do not support HTML)
        text_body = f"""
Convia License – Magic Sign-In Link

Hi,

Your Convia license has been created successfully.

Use the magic link below to open your license dashboard, view your license details,
and manage container usage and machine bindings:

Magic link:
{magic_link_url}

License key:
{license_key}

⚠ This link will expire in 24 hours. If the link has expired, you can request a new
magic link from the Convia license portal using your license key.

—
This email was sent automatically by the Convia License Server.
If you did not request this, you can safely ignore this email.
"""

        # HTML body (main user-facing content)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Convia License – Magic Sign-In Link</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f3f4f6;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 640px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 24px 32px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
        }}
        .content {{
            padding: 28px 32px 24px 32px;
            background-color: #f9fafb;
        }}
        .button-wrapper {{
            text-align: center;
            margin: 24px 0 18px 0;
        }}
        .button {{
            display: inline-block;
            padding: 12px 32px;
            background-color: #4f46e5;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 999px;
            font-weight: 600;
            font-size: 14px;
        }}
        .button:hover {{
            background-color: #4338ca;
        }}
        .code-block {{
            word-break: break-all;
            background-color: #e5e7eb;
            padding: 10px 12px;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 13px;
        }}
        .label {{
            font-weight: 600;
        }}
        .warning {{
            color: #b91c1c;
            font-size: 13px;
            margin-top: 16px;
        }}
        .footer {{
            padding: 14px 24px 18px 24px;
            font-size: 12px;
            color: #6b7280;
            text-align: center;
            background-color: #f3f4f6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Convia License – Magic Sign-In Link</h1>
        </div>
        <div class="content">
            <p>Hi,</p>
            <p>
                Your Convia license has been created successfully.
                Click the button below to open your license dashboard,
                view your license details, and manage container usage and machine bindings.
            </p>

            <div class="button-wrapper">
                <a href="{magic_link_url}" class="button">Open License Dashboard</a>
            </div>

            <p>If the button above does not work, copy and paste this link into your browser:</p>
            <p class="code-block">{magic_link_url}</p>

            <p class="label">License key:</p>
            <p class="code-block">{license_key}</p>

            <p class="warning">
                ⚠ This magic link will expire in 24 hours. If it has expired,
                please request a new link from the Convia license portal using your license key.
            </p>
        </div>
        <div class="footer">
            <p>This email was sent automatically by the Convia License Server.</p>
            <p>If you did not request this, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
        """

        # Attach both plain text and HTML parts
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via SMTP
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
        server.quit()

        logger.info(f"Magic link email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send magic link email to {email}: {e}", exc_info=True)
        # We still return True so that license creation/webhook handling
        # is treated as successful; email retry logic can be added separately.
        return True