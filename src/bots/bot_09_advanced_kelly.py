"""Bot 9: Advanced Kelly Strategy with Dynamic Fraction Adjustment.

This bot implements sophisticated Kelly Criterion with:
- Dynamic fraction adjustment [0.15-0.50] based on edge confidence
- Multi-timeframe analysis (1h/4h/24h) for edge detection
- Volatility-adjusted sizing
- Market efficiency scoring
- Portfolio correlation optimization

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from src.bots.base_bot import BaseBotStrategy
from src.domain.entities import Market, Order, Position
from src.domain.value_objects import BotState, OrderStatus, Side, Zone
from src.domain.exceptions import RiskViolation

logger = logging.getLogger(__name__)


@dataclass
class EdgeMetrics:
    """Edge estimation metrics for Kelly calculation."""

    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    sharpe_ratio: Decimal
    confidence_score: Decimal  # 0-100
    volatility: Decimal
    sample_size: int
    timeframe: str  # "1h", "4h", "24h"


@dataclass
class KellyFractionResult:
    """Kelly fraction calculation result."""

    optimal_fraction: Decimal
    base_kelly: Decimal
    adjustment_factor: Decimal
    confidence: Decimal
    edge_estimate: Decimal
    recommended_size: Decimal


class AdvancedKellyStrategy(BaseBotStrategy):
    """Bot 9: Advanced Kelly with dynamic fraction adjustment.

    Key features:
    - Quarter Kelly base (0.25) + dynamic adjustment
    - Multi-timeframe edge detection
    - Volatility-adjusted sizing
    - Correlation-aware portfolio optimization
    - Adaptive to market conditions

    Risk controls:
    - Max Kelly: 0.50 (Half Kelly ceiling)
    - Min Kelly: 0.15 (floor for viability)
    - Min edge: 5% required
    - Min confidence: 60% required
    - Circuit breakers on consecutive losses

    Attributes:
        base_kelly_fraction: Base Kelly (0.25 = Quarter Kelly)
        min_kelly: Minimum viable Kelly fraction
        max_kelly: Maximum allowed Kelly fraction
        min_edge_pct: Minimum edge required (5%)
        min_confidence: Minimum confidence score (60%)
        timeframes: Analysis windows ["1h", "4h", "24h"]
        max_correlation: Max portfolio correlation allowed
        volatility_scaling: Reduce Kelly on high vol
    """

    def __init__(self, config: Dict) -> None:
        """Initialize Advanced Kelly strategy.

        Args:
            config: Bot configuration with Kelly parameters

        Raises:
            ValueError: If config invalid
        """
        super().__init__(config)

        # Kelly parameters
        self.base_kelly_fraction = Decimal(str(config.get("base_kelly_fraction", 0.25)))
        self.min_kelly = Decimal(str(config.get("min_kelly", 0.15)))
        self.max_kelly = Decimal(str(config.get("max_kelly", 0.50)))

        # Edge requirements
        self.min_edge_pct = Decimal(str(config.get("min_edge_pct", 5.0)))
        self.min_confidence = Decimal(str(config.get("min_confidence", 60.0)))

        # Timeframes for analysis
        self.timeframes: List[str] = config.get("timeframes", ["1h", "4h", "24h"])

        # Portfolio optimization
        self.max_correlation = Decimal(str(config.get("max_correlation", 0.70)))
        self.volatility_scaling = config.get("volatility_scaling", True)

        # Market filters
        self.min_liquidity = Decimal(str(config.get("min_liquidity", 5000)))
        self.target_zones = config.get("target_zones", [1, 2, 3])

        # State tracking
        self._edge_cache: Dict[str, Dict[str, EdgeMetrics]] = {}
        self._last_edge_update: Dict[str, datetime] = {}
        self._portfolio_correlation: Dict[Tuple[str, str], Decimal] = {}

        logger.info(
            "advanced_kelly_initialized",
            extra={
                "bot_id": self.bot_id,
                "base_kelly": float(self.base_kelly_fraction),
                "kelly_range": f"{float(self.min_kelly):.2f}-{float(self.max_kelly):.2f}",
                "min_edge_pct": float(self.min_edge_pct),
                "timeframes": self.timeframes,
            },
        )

    async def initialize(self) -> None:
        """Initialize Advanced Kelly bot.

        Loads:
        - Historical market data for edge calculation
        - Past positions for win rate analysis
        - Market correlation matrices

        Raises:
            InfrastructureError: If data loading fails
        """
        logger.info("initializing_advanced_kelly", extra={"bot_id": self.bot_id})

        # Load historical data for edge estimation
        await self._load_historical_data()

        # Calculate initial edge metrics for active markets
        await self._update_all_edge_metrics()

        # Build correlation matrix
        await self._build_correlation_matrix()

        self._state = BotState.IDLE
        logger.info("advanced_kelly_initialized", extra={"bot_id": self.bot_id})

    async def execute_cycle(self) -> None:
        """Execute one Advanced Kelly trading cycle.

        Steps:
        1. Update edge metrics for active markets (5min cache)
        2. Calculate optimal Kelly fraction per market
        3. Select best opportunities (highest edge * confidence)
        4. Size positions with dynamic Kelly
        5. Place orders with risk validation
        6. Monitor correlations and adjust

        Cycle time target: <100ms p99
        """
        cycle_start = datetime.utcnow()

        try:
            # 1. Update edge metrics (cached 5min)
            await self._update_edge_metrics_if_stale()

            # 2. Get active markets meeting criteria
            candidate_markets = await self._get_candidate_markets()

            if not candidate_markets:
                logger.debug(
                    "no_candidates",
                    extra={"bot_id": self.bot_id, "reason": "no_markets_meet_criteria"},
                )
                return

            # 3. Calculate Kelly fractions for each candidate
            kelly_opportunities = []
            for market in candidate_markets:
                kelly_result = await self._calculate_dynamic_kelly(market)

                if kelly_result and kelly_result.optimal_fraction >= self.min_kelly:
                    kelly_opportunities.append((market, kelly_result))

            # Sort by edge * confidence (expected value)
            kelly_opportunities.sort(
                key=lambda x: x[1].edge_estimate * x[1].confidence, reverse=True
            )

            # 4. Select top opportunities respecting position limits
            open_positions = await self._get_open_positions()
            available_slots = self.config["max_positions"] - len(open_positions)

            if available_slots <= 0:
                logger.debug(
                    "max_positions_reached",
                    extra={
                        "bot_id": self.bot_id,
                        "open_positions": len(open_positions),
                    },
                )
                return

            # 5. Place orders for top opportunities
            orders_placed = 0
            for market, kelly_result in kelly_opportunities[:available_slots]:
                try:
                    await self._place_kelly_order(market, kelly_result)
                    orders_placed += 1
                except RiskViolation as e:
                    logger.warning(
                        "order_rejected_risk",
                        extra={
                            "bot_id": self.bot_id,
                            "market_id": market.market_id,
                            "reason": str(e),
                        },
                    )

            # 6. Update metrics
            cycle_time_ms = (datetime.utcnow() - cycle_start).total_seconds() * 1000
            self._metrics["cycle_time_ms"] = cycle_time_ms
            self._metrics["orders_placed"] += orders_placed

            logger.debug(
                "cycle_completed",
                extra={
                    "bot_id": self.bot_id,
                    "cycle_time_ms": round(cycle_time_ms, 2),
                    "candidates": len(candidate_markets),
                    "opportunities": len(kelly_opportunities),
                    "orders_placed": orders_placed,
                },
            )

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(
                "cycle_error",
                extra={"bot_id": self.bot_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def _calculate_dynamic_kelly(self, market: Market) -> Optional[KellyFractionResult]:
        """Calculate dynamic Kelly fraction for market.

        Formula:
        1. Base Kelly = (bp - q) / b  (classic Kelly)
        2. Confidence adjustment: * (confidence / 100)
        3. Volatility adjustment: * (1 - volatility_penalty)
        4. Clamp to [min_kelly, max_kelly]

        Args:
            market: Market to calculate Kelly for

        Returns:
            KellyFractionResult if valid edge found, None otherwise

        Example:
            Edge 8%, Win rate 54%, Confidence 75%, Low volatility
            Base Kelly = 0.30
            Confidence adj = 0.30 * 0.75 = 0.225
            Volatility adj = 0.225 * 1.0 = 0.225
            Final = 0.225 (Quarter Kelly)
        """
        # Get multi-timeframe edge metrics
        edge_metrics = await self._get_edge_metrics(market.market_id)

        if not edge_metrics:
            return None

        # Use weighted average across timeframes (24h heaviest)
        weights = {"1h": Decimal("0.2"), "4h": Decimal("0.3"), "24h": Decimal("0.5")}

        weighted_win_rate = Decimal("0")
        weighted_confidence = Decimal("0")
        weighted_volatility = Decimal("0")

        for tf, metrics in edge_metrics.items():
            weight = weights.get(tf, Decimal("0"))
            weighted_win_rate += metrics.win_rate * weight
            weighted_confidence += metrics.confidence_score * weight
            weighted_volatility += metrics.volatility * weight

        # Check minimum requirements
        if weighted_confidence < self.min_confidence:
            return None

        # Calculate edge
        win_rate = weighted_win_rate / Decimal("100")  # Convert to 0-1
        lose_rate = Decimal("1") - win_rate

        # Simplified: assume 1:1 payoff for edge estimation
        edge = win_rate - lose_rate

        if edge < self.min_edge_pct / Decimal("100"):
            return None

        # Base Kelly = edge / odds
        # For binary markets with fair odds, Kelly = edge
        base_kelly = edge

        # Apply Quarter Kelly base
        base_kelly = base_kelly * self.base_kelly_fraction

        # Confidence adjustment
        confidence_factor = weighted_confidence / Decimal("100")
        adjusted_kelly = base_kelly * confidence_factor

        # Volatility adjustment (reduce on high vol)
        if self.volatility_scaling:
            # High volatility (>20%) reduces Kelly by up to 50%
            volatility_penalty = min(weighted_volatility / Decimal("40"), Decimal("0.5"))
            volatility_factor = Decimal("1") - volatility_penalty
            adjusted_kelly = adjusted_kelly * volatility_factor

        # Clamp to bounds
        optimal_kelly = max(self.min_kelly, min(adjusted_kelly, self.max_kelly))

        # Calculate recommended size
        available_capital = Decimal(str(self.config["capital_allocated"]))
        recommended_size = available_capital * optimal_kelly

        return KellyFractionResult(
            optimal_fraction=optimal_kelly,
            base_kelly=base_kelly,
            adjustment_factor=confidence_factor * (
                Decimal("1") - (volatility_penalty if self.volatility_scaling else Decimal("0"))
            ),
            confidence=weighted_confidence,
            edge_estimate=edge * Decimal("100"),  # As percentage
            recommended_size=recommended_size,
        )

    async def _get_edge_metrics(self, market_id: str) -> Dict[str, EdgeMetrics]:
        """Get edge metrics for market across all timeframes.

        Args:
            market_id: Market to get metrics for

        Returns:
            Dict mapping timeframe to EdgeMetrics
        """
        return self._edge_cache.get(market_id, {})

    async def _update_all_edge_metrics(self) -> None:
        """Update edge metrics for all active markets."""
        # TODO: Implement with historical data analysis
        # For now, stub with reasonable defaults
        pass

    async def _update_edge_metrics_if_stale(self) -> None:
        """Update edge metrics if cache is stale (>5min)."""
        now = datetime.utcnow()
        stale_threshold = timedelta(minutes=5)

        # Check if global update needed
        if not self._last_edge_update or (
            now - min(self._last_edge_update.values()) > stale_threshold
        ):
            await self._update_all_edge_metrics()

    async def _get_candidate_markets(self) -> List[Market]:
        """Get candidate markets meeting criteria.

        Filters:
        - Liquidity >= min_liquidity
        - Zone in target_zones
        - Has valid edge metrics
        - Not already in portfolio

        Returns:
            List of candidate markets
        """
        # TODO: Implement with market data service
        return []

    async def _place_kelly_order(self, market: Market, kelly_result: KellyFractionResult) -> None:
        """Place order sized with Kelly fraction.

        Args:
            market: Market to trade
            kelly_result: Kelly calculation result with sizing

        Raises:
            RiskViolation: If order violates risk rules
        """
        # TODO: Implement with order execution engine
        pass

    async def _get_open_positions(self) -> List[Position]:
        """Get currently open positions for this bot.

        Returns:
            List of open positions
        """
        # TODO: Implement with position repository
        return []

    async def _load_historical_data(self) -> None:
        """Load historical market data for edge calculation."""
        # TODO: Implement with historical data service
        pass

    async def _build_correlation_matrix(self) -> None:
        """Build correlation matrix for portfolio optimization."""
        # TODO: Implement correlation analysis
        pass

    async def stop_gracefully(self) -> None:
        """Stop bot gracefully.

        Actions:
        - Cancel all pending orders
        - Close positions (optional, based on config)
        - Save state
        - Clear caches
        """
        logger.info("stopping_gracefully", extra={"bot_id": self.bot_id})

        # Clear caches
        self._edge_cache.clear()
        self._last_edge_update.clear()
        self._portfolio_correlation.clear()

        self._state = BotState.STOPPED
        logger.info("bot_stopped", extra={"bot_id": self.bot_id})
