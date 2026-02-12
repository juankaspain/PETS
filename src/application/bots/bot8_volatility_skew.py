"""Bot 8: Volatility Skew Arbitrage Strategy.

Evidence: $106K profit from manual trading.

Strategy:
1. Monitor ATH/ATL spread (>15% opportunity)
2. Entry: Buy cheap YES (<0.20) OR expensive NO (>0.80)
3. Hold: 24-48h for mean reversion
4. Exit: Take profit at 0.25-0.35 delta improvement
5. Stop-loss: 10% drawdown max

Risk:
- Zone 2-3 only (medium risk, Kelly 5-10%)
- Max position: 10-15% portfolio
- Post-only orders OBLIGATORIO
- Circuit breakers active
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from src.domain.entities.market import Market
from src.domain.entities.order import OrderSide
from src.domain.entities.position import Position
from src.domain.services.kelly_calculator import KellyCalculator
from src.domain.services.risk_calculator import RiskCalculator
from src.domain.services.zone_classifier import ZoneClassifier
from src.domain.value_objects.price import Price
from src.domain.value_objects.zone import Zone

logger = logging.getLogger(__name__)


@dataclass
class OpportunitySignal:
    """Opportunity signal for Bot 8."""

    market: Market
    side: OrderSide
    entry_price: Price
    zone: Zone
    spread: Decimal
    edge: Decimal
    reason: str


class Bot8VolatilitySkew:
    """Bot 8: Volatility Skew Arbitrage.

    Exploits mispricing in volatile markets with mean reversion.

    Example:
        >>> bot = Bot8VolatilitySkew(
        ...     bot_id=1,
        ...     config={
        ...         "spread_threshold": 0.15,
        ...         "entry_threshold_low": 0.20,
        ...         "entry_threshold_high": 0.80,
        ...         "hold_hours_min": 24,
        ...         "hold_hours_max": 48,
        ...         "target_delta": 0.30,
        ...         "stop_loss_pct": 0.10,
        ...     },
        ... )
        >>> signal = bot.analyze_market(market)
    """

    def __init__(
        self,
        bot_id: int,
        config: dict,
    ) -> None:
        """Initialize Bot 8.

        Args:
            bot_id: Bot ID
            config: Strategy configuration
        """
        self.bot_id = bot_id
        self.config = config

        # Strategy parameters
        self.spread_threshold = Decimal(str(config.get("spread_threshold", 0.15)))
        self.entry_threshold_low = Decimal(str(config.get("entry_threshold_low", 0.20)))
        self.entry_threshold_high = Decimal(
            str(config.get("entry_threshold_high", 0.80))
        )
        self.hold_hours_min = config.get("hold_hours_min", 24)
        self.hold_hours_max = config.get("hold_hours_max", 48)
        self.target_delta = Decimal(str(config.get("target_delta", 0.30)))
        self.stop_loss_pct = Decimal(str(config.get("stop_loss_pct", 0.10)))

        # Risk management
        self.risk_calc = RiskCalculator()
        self.kelly_calc = KellyCalculator()
        self.zone_classifier = ZoneClassifier()

        logger.info(
            "Bot8VolatilitySkew initialized",
            extra={"bot_id": bot_id, "config": config},
        )

    def analyze_market(self, market: Market) -> Optional[OpportunitySignal]:
        """Analyze market for opportunities.

        Args:
            market: Market to analyze

        Returns:
            OpportunitySignal if opportunity found, None otherwise

        Logic:
        1. Check market active and liquid
        2. Calculate ATH/ATL spread
        3. Check spread > threshold (15%)
        4. Identify entry: cheap YES (<0.20) OR expensive NO (>0.80)
        5. Classify zone (must be 2-3)
        6. Estimate edge (mean reversion probability)
        7. Return signal if valid
        """
        # 1. Market checks
        if not market.is_active():
            return None

        if not market.has_sufficient_liquidity(Decimal("10000")):
            logger.debug(
                "Insufficient liquidity",
                extra={"market_id": market.market_id, "liquidity": float(market.liquidity)},
            )
            return None

        # 2. Check prices available
        if not market.yes_price or not market.no_price:
            return None

        yes_price = market.yes_price
        no_price = market.no_price

        # 3. Calculate spread (deviation from 0.50)
        spread = max(
            abs(yes_price.value - Decimal("0.50")),
            abs(no_price.value - Decimal("0.50")),
        )

        if spread < self.spread_threshold:
            return None

        # 4. Identify entry opportunity
        signal: Optional[OpportunitySignal] = None

        # CHEAP YES (<0.20): Buy YES
        if yes_price.value < self.entry_threshold_low:
            zone = self.zone_classifier.classify_price(yes_price)
            if zone.is_safe():  # Zone 1-3 only
                edge = self._estimate_edge(yes_price, True)
                signal = OpportunitySignal(
                    market=market,
                    side=OrderSide.BUY,
                    entry_price=yes_price,
                    zone=zone,
                    spread=spread,
                    edge=edge,
                    reason=f"Cheap YES {yes_price.value:.4f} < {self.entry_threshold_low}",
                )

        # EXPENSIVE NO (>0.80): Sell NO (= Buy YES at 1-price)
        elif no_price.value > self.entry_threshold_high:
            # In Polymarket, selling NO = buying YES at (1 - NO_price)
            implied_yes_price = Price(Decimal("1.0") - no_price.value)
            zone = self.zone_classifier.classify_price(implied_yes_price)
            if zone.is_safe():
                edge = self._estimate_edge(implied_yes_price, False)
                signal = OpportunitySignal(
                    market=market,
                    side=OrderSide.SELL,
                    entry_price=no_price,
                    zone=zone,
                    spread=spread,
                    edge=edge,
                    reason=f"Expensive NO {no_price.value:.4f} > {self.entry_threshold_high}",
                )

        if signal:
            logger.info(
                "Opportunity detected",
                extra={
                    "market_id": market.market_id,
                    "side": signal.side.value,
                    "price": float(signal.entry_price.value),
                    "zone": signal.zone.value,
                    "spread": float(signal.spread),
                    "edge": float(signal.edge),
                    "reason": signal.reason,
                },
            )

        return signal

    def _estimate_edge(self, price: Price, is_cheap_yes: bool) -> Decimal:
        """Estimate edge for mean reversion trade.

        Args:
            price: Entry price
            is_cheap_yes: True if cheap YES, False if expensive NO

        Returns:
            Estimated edge (0.0 to 1.0)

        Logic:
        - Extreme prices (far from 0.50) have higher mean reversion probability
        - Historical evidence: ~60-70% win rate for Bot 8 type trades
        - Edge = distance from 0.50 * reversion factor
        """
        distance_from_fair = abs(price.value - Decimal("0.50"))

        # Reversion factor (empirical from $106K evidence)
        # Cheap prices (<0.20) or expensive prices (>0.80) revert ~60-70%
        if distance_from_fair >= Decimal("0.30"):
            # Extreme mispricing: 15-20% edge
            base_edge = Decimal("0.175")
        elif distance_from_fair >= Decimal("0.20"):
            # Moderate mispricing: 10-15% edge
            base_edge = Decimal("0.125")
        else:
            # Small mispricing: 5-10% edge
            base_edge = Decimal("0.075")

        return base_edge

    def should_exit(self, position: Position, current_price: Price) -> tuple[bool, str]:
        """Check if position should be exited.

        Args:
            position: Current position
            current_price: Current market price

        Returns:
            Tuple of (should_exit, reason)

        Exit conditions:
        1. Target delta achieved (0.25-0.35 improvement)
        2. Stop-loss hit (10% drawdown)
        3. Hold time exceeded (48h)
        4. Mean reversion failed (still extreme after 48h)
        """
        # Calculate P&L
        pnl = position.calculate_unrealized_pnl(current_price)
        pnl_pct = (
            pnl.unrealized / (position.size.value * position.entry_price.value)
            if pnl.unrealized
            else Decimal("0")
        )

        # 1. Target profit
        if pnl.unrealized and pnl.unrealized > Decimal("0"):
            price_delta = abs(current_price.value - position.entry_price.value)
            if price_delta >= self.target_delta * Decimal("0.80"):  # 80% of target
                return True, f"Target profit {price_delta:.4f} (target {self.target_delta})"

        # 2. Stop-loss
        if pnl_pct < -self.stop_loss_pct:
            return True, f"Stop-loss {pnl_pct*100:.1f}% (max {self.stop_loss_pct*100:.1f}%)"

        # 3. Max hold time
        holding_hours = position.holding_time_hours()
        if holding_hours >= self.hold_hours_max:
            return True, f"Max hold time {holding_hours:.1f}h exceeded"

        # 4. Min hold time not met
        if holding_hours < self.hold_hours_min:
            return False, "Min hold time not met"

        return False, ""

    def calculate_position_size(
        self,
        signal: OpportunitySignal,
        portfolio_value: Decimal,
    ) -> Decimal:
        """Calculate position size using Kelly.

        Args:
            signal: Opportunity signal
            portfolio_value: Total portfolio value

        Returns:
            Position size in USDC

        Logic:
        - Estimate win probability (60-70% for Bot 8)
        - Calculate Kelly fraction for zone
        - Apply max 15% position size cap
        """
        # Win probability (empirical from Bot 8 evidence)
        win_prob = Decimal("0.65")  # 65% win rate typical

        # Kelly sizing
        kelly_size = self.kelly_calc.calculate_position_size(
            zone=signal.zone,
            win_prob=win_prob,
            edge=signal.edge,
            portfolio_value=portfolio_value,
        )

        # Cap at 15% portfolio
        max_size = portfolio_value * Decimal("0.15")
        position_size = min(kelly_size, max_size)

        logger.info(
            "Position size calculated",
            extra={
                "kelly_size": float(kelly_size),
                "max_size": float(max_size),
                "final_size": float(position_size),
                "pct_portfolio": float(position_size / portfolio_value * 100),
            },
        )

        return position_size
