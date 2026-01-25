from __future__ import annotations
"""Notification services for alerts."""
import logging
from typing import Protocol

from app.config import get_settings
from app.models.opportunity import Opportunity

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """Protocol for notification services."""

    async def send_opportunity_alert(self, opportunity: Opportunity) -> bool:
        """Send an alert for a new opportunity."""
        ...


class TelegramNotifier:
    """
    Telegram bot for sending arbitrage alerts.

    Setup:
    1. Create a bot via @BotFather on Telegram
    2. Get the bot token
    3. Start a chat with your bot and get your chat_id
    4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ):
        settings = get_settings()
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self._bot = None

    @property
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.bot_token and self.chat_id)

    async def _get_bot(self):
        """Lazy load the Telegram bot."""
        if self._bot is None:
            if not self.is_configured:
                raise ValueError(
                    "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
                )
            try:
                from aiogram import Bot

                self._bot = Bot(token=self.bot_token)
            except ImportError:
                raise ImportError("aiogram not installed. Run: pip install aiogram")
        return self._bot

    async def send_opportunity_alert(self, opportunity: Opportunity) -> bool:
        """
        Send an arbitrage opportunity alert to Telegram.

        Args:
            opportunity: The opportunity to alert about

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Telegram not configured, skipping alert")
            return False

        try:
            bot = await self._get_bot()
            message = opportunity.to_alert_message()
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None,  # Plain text for reliability
            )
            logger.info(f"Sent Telegram alert for opportunity {opportunity.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    async def send_message(self, text: str) -> bool:
        """Send a custom message to Telegram."""
        if not self.is_configured:
            return False

        try:
            bot = await self._get_bot()
            await bot.send_message(chat_id=self.chat_id, text=text)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def close(self):
        """Close the bot session."""
        if self._bot:
            await self._bot.session.close()
            self._bot = None


class ConsoleNotifier:
    """Simple console notifier for development/testing."""

    async def send_opportunity_alert(self, opportunity: Opportunity) -> bool:
        """Print opportunity to console."""
        print("\n" + "=" * 60)
        print(opportunity.to_alert_message())
        print("=" * 60 + "\n")
        return True


class MultiNotifier:
    """Send notifications to multiple channels."""

    def __init__(self, notifiers: list[Notifier] | None = None):
        self.notifiers = notifiers or []

    def add_notifier(self, notifier: Notifier):
        """Add a notifier to the list."""
        self.notifiers.append(notifier)

    async def send_opportunity_alert(self, opportunity: Opportunity) -> bool:
        """Send alert to all configured notifiers."""
        results = []
        for notifier in self.notifiers:
            try:
                result = await notifier.send_opportunity_alert(opportunity)
                results.append(result)
            except Exception as e:
                logger.error(f"Notifier {type(notifier).__name__} failed: {e}")
                results.append(False)

        return any(results)  # True if at least one succeeded
