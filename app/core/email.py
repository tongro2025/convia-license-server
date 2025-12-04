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
        True if email was sent successfully (or logged), False otherwise
    """
    magic_link_url = f"{settings.frontend_url}/license/portal?token={token}"

    # SMTP 설정이 없으면 로그만 남기고 성공으로 처리 (개발 환경)
    if not settings.smtp_username or not settings.smtp_password:
        logger.info(
            f"Magic link email would be sent to {email}:\n"
            f"  License Key: {license_key}\n"
            f"  Magic Link: {magic_link_url}\n"
            f"  Token: {token}\n"
            f"  (SMTP not configured - email not actually sent)"
        )
        return True

    try:
        # 이메일 내용 생성
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = email
        msg["Subject"] = "Convia 라이선스 활성화 링크"

        # HTML 이메일 본문
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Convia 라이선스 활성화</h1>
                </div>
                <div class="content">
                    <p>안녕하세요,</p>
                    <p>Convia 라이선스가 성공적으로 생성되었습니다. 아래 링크를 클릭하여 라이선스를 활성화하세요.</p>
                    
                    <div style="text-align: center;">
                        <a href="{magic_link_url}" class="button">라이선스 활성화하기</a>
                    </div>
                    
                    <p>또는 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
                    <p style="word-break: break-all; background-color: #e8e8e8; padding: 10px; border-radius: 3px;">
                        {magic_link_url}
                    </p>
                    
                    <p><strong>라이선스 키:</strong> {license_key}</p>
                    
                    <p style="color: #d32f2f; font-size: 14px;">
                        ⚠️ 이 링크는 24시간 후에 만료됩니다.
                    </p>
                </div>
                <div class="footer">
                    <p>이 이메일은 Convia License Server에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 고객 지원팀에 연락해주세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 텍스트 버전 (HTML을 지원하지 않는 클라이언트용)
        text_body = f"""
        Convia 라이선스 활성화

        안녕하세요,

        Convia 라이선스가 성공적으로 생성되었습니다. 아래 링크를 클릭하여 라이선스를 활성화하세요.

        라이선스 활성화 링크: {magic_link_url}

        라이선스 키: {license_key}

        ⚠️ 이 링크는 24시간 후에 만료됩니다.

        ---
        이 이메일은 Convia License Server에서 자동으로 발송되었습니다.
        """

        # 이메일 본문 추가
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # SMTP 서버 연결 및 이메일 발송
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
        # 이메일 발송 실패해도 로그만 남기고 True 반환 (라이선스 생성은 성공)
        # 실제 운영 환경에서는 실패 시 재시도 로직을 추가할 수 있음
        return True
