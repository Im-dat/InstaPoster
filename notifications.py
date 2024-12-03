import smtplib
from telegram.ext import Application
import logging
from typing import Union
from config import Config
from exceptions import NotificationException
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, config: Config):
        self.config = config
        self._setup_services()
        self.logger = logging.getLogger(__name__)
    
    def _setup_services(self):
        if self.config.telegram_enabled:
            self._setup_telegram()
        if self.config.email_enabled:
            self._setup_email()
    
    def _setup_telegram(self):
        try:
            self.bot = Application.from_token(token=self.config.telegram_token)
        except Exception as e:
            raise NotificationException("Erro ao configurar Telegram", "telegram", {"error": str(e)})
    
    def _setup_email(self):
        try:
            self.smtp = smtplib.SMTP(self.config.smtp_server)
            self.smtp.starttls()
            self.smtp.login(self.config.smtp_user, self.config.smtp_password)
        except Exception as e:
            raise NotificationException("Erro ao configurar email", "email", {"error": str(e)})
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def notify(self, message: str, error: Union[Exception, None] = None):
        """Envia notificação com retry automático"""
        try:
            if self.config.telegram_enabled:
                await self._notify_telegram(message, error)
            if self.config.email_enabled:
                await self._notify_email(message, error)
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação: {e}")
            raise
    
    async def _notify_telegram(self, message: str, error: Union[Exception, None]):
        try:
            await self.bot.send_message(
                chat_id=self.config.telegram_chat_id,
                text=f"{message}\n{str(error) if error else ''}"
            )
        except Exception as e:
            raise NotificationException(f"Erro ao enviar notificação Telegram: {e}")
    
    async def _notify_email(self, message: str, error: Union[Exception, None]):
        try:
            subject = "Erro no Upload" if error else "Status do Upload"
            body = f"{message}\n{str(error) if error else ''}"
            self.smtp.sendmail(
                self.config.smtp_from,
                self.config.smtp_to,
                f"Subject: {subject}\n\n{body}"
            )
        except Exception as e:
            raise NotificationException(f"Erro ao enviar email: {e}") 