import logging
from email.message import EmailMessage
from typing import List, Optional
import aiosmtplib
from .config import settings

logger = logging.getLogger("connect_hub.mailer")


class MailerService:
    def __init__(self):
        self.enabled = settings.SMTP_ENABLED and bool(settings.SMTP_USER)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Sends an email asynchronously via SMTP.
        If SMTP is disabled, logs the email content to console.
        """
        if not self.enabled:
            logger.info(
                f"[SMTP Simulation] To: {to_email} | Subject: {subject}\nContent: {text_content or html_content}"
            )
            return True

        message = EmailMessage()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject

        if text_content:
            message.set_content(text_content)
            message.add_alternative(html_content, subtype="html")
        else:
            message.set_content(html_content, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_PORT == 465,
                start_tls=settings.SMTP_PORT == 587 and settings.SMTP_TLS,
            )
            logger.info(f"Successfully sent email to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        subject = "Welcome to Connect-Hub!"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #2563eb;">Welcome to Connect-Hub, {user_name}! 👋</h2>
            <p>Thank you for joining Connect-Hub - your unified platform for stories, groups, chat, and high-quality audio & video calling.</p>
            <p>Explore feeds, connect with friends, and start sharing your moments.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
            <p style="color: #888; font-size: 12px;">© 2026 Connect-Hub Team. All rights reserved.</p>
        </div>
        """
        return await self.send_email(to_email, subject, html)

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        subject = "Connect-Hub Password Reset Request"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #2563eb;">Password Reset Request</h2>
            <p>You requested to reset your Connect-Hub account password. Use the verification token below:</p>
            <div style="padding: 12px; background: #f3f4f6; border-radius: 6px; font-size: 18px; font-weight: bold; text-align: center; letter-spacing: 2px;">
                {reset_token}
            </div>
            <p>If you did not request this, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
            <p style="color: #888; font-size: 12px;">© 2026 Connect-Hub Team.</p>
        </div>
        """
        return await self.send_email(to_email, subject, html)


mailer_service = MailerService()
