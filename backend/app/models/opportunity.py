from __future__ import annotations
"""Arbitrage opportunity models."""
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
import hashlib


class OpportunityType(str, Enum):
    """Types of arbitrage opportunities."""

    YES_NO = "yes_no"  # YES + NO < $1.00
    CROSS_PLATFORM = "cross_platform"  # Price diff between platforms


class Opportunity(BaseModel):
    """An arbitrage opportunity."""

    type: OpportunityType
    market_id: str
    market_question: str

    # Prices
    yes_price: float
    no_price: float
    combined_cost: float

    # Profit calculation
    gross_profit: float  # Before fees
    net_profit: float  # After fees
    edge_percent: float  # Net profit as percentage

    # Execution details
    yes_token_id: str | None = None
    no_token_id: str | None = None
    max_size: float | None = None  # Max size at these prices

    # Metadata
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    platform: str = "polymarket"

    @property
    def id(self) -> str:
        """Generate unique ID for this opportunity."""
        data = f"{self.market_id}:{self.type}:{self.combined_cost:.4f}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    @property
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable after fees."""
        return self.net_profit > 0

    def to_alert_message(self) -> str:
        """Format opportunity for Telegram alert."""
        return f"""
🚨 ARBITRAGE OPPORTUNITY 🚨

📊 Market: {self.market_question[:100]}

💰 Prices:
   YES: ${self.yes_price:.4f}
   NO:  ${self.no_price:.4f}
   Combined: ${self.combined_cost:.4f}

📈 Profit:
   Gross: ${self.gross_profit:.4f}
   Net:   ${self.net_profit:.4f} ({self.edge_percent:.2f}%)

⏰ Detected: {self.detected_at.strftime('%H:%M:%S UTC')}
🔗 Platform: {self.platform}
        """.strip()
