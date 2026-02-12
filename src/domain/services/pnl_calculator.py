"""P&L calculator domain service."""

from decimal import Decimal
from typing import Optional

from src.domain.entities.position import Position
from src.domain.entities.trade import Trade
from src.domain.value_objects.pnl import PnL


class PnLCalculator:
    """P&L calculator for position and portfolio performance.

    Calculates:
    - Realized and unrealized P&L
    - Sharpe ratio
    - Win rate and average win/loss
    - ROI and total return

    Example:
        >>> calc = PnLCalculator()
        >>> pnl = calc.calculate_position_pnl(
        ...     position=position,
        ...     current_price=Price(Decimal("0.60")),
        ... )
    """

    @staticmethod
    def calculate_position_pnl(
        position: Position,
        current_price,
    ) -> PnL:
        """Calculate position P&L.

        Args:
            position: Position entity
            current_price: Current market price

        Returns:
            PnL value object
        """
        if position.is_open():
            # Unrealized P&L
            return position.calculate_unrealized_pnl(current_price)
        else:
            # Realized P&L
            if position.pnl:
                return position.pnl
            return PnL(realized=Decimal("0"))

    @staticmethod
    def calculate_trade_pnl(trade: Trade) -> PnL:
        """Calculate trade P&L (realized).

        Args:
            trade: Trade entity

        Returns:
            PnL with realized value

        Note:
            For a complete P&L, need to know exit trade.
            This just calculates costs.
        """
        # Costs (negative)
        costs = trade.fees_paid + trade.gas_cost_usdc
        return PnL(realized=-costs)

    @staticmethod
    def calculate_portfolio_pnl(
        positions: list[Position],
        current_prices: dict[str, any],
    ) -> PnL:
        """Calculate total portfolio P&L.

        Args:
            positions: List of positions
            current_prices: Dict of market_id -> current_price

        Returns:
            Total P&L
        """
        total_realized = Decimal("0")
        total_unrealized = Decimal("0")

        for position in positions:
            if position.is_open():
                # Unrealized
                current_price = current_prices.get(position.market_id)
                if current_price:
                    pnl = position.calculate_unrealized_pnl(current_price)
                    if pnl.unrealized:
                        total_unrealized += pnl.unrealized
            else:
                # Realized
                if position.pnl and position.pnl.realized:
                    total_realized += position.pnl.realized

        return PnL(realized=total_realized, unrealized=total_unrealized)

    @staticmethod
    def calculate_win_rate(
        positions: list[Position],
    ) -> Decimal:
        """Calculate win rate from closed positions.

        Args:
            positions: List of closed positions

        Returns:
            Win rate (0.0 to 1.0)
        """
        closed = [p for p in positions if not p.is_open()]
        if not closed:
            return Decimal("0")

        wins = sum(
            1
            for p in closed
            if p.pnl and p.pnl.realized and p.pnl.realized > Decimal("0")
        )

        return Decimal(wins) / Decimal(len(closed))

    @staticmethod
    def calculate_average_win_loss(
        positions: list[Position],
    ) -> tuple[Decimal, Decimal]:
        """Calculate average win and loss.

        Args:
            positions: List of closed positions

        Returns:
            Tuple of (avg_win, avg_loss)
        """
        closed = [p for p in positions if not p.is_open()]
        if not closed:
            return Decimal("0"), Decimal("0")

        wins = [
            p.pnl.realized
            for p in closed
            if p.pnl and p.pnl.realized and p.pnl.realized > Decimal("0")
        ]
        losses = [
            abs(p.pnl.realized)
            for p in closed
            if p.pnl and p.pnl.realized and p.pnl.realized < Decimal("0")
        ]

        avg_win = sum(wins) / Decimal(len(wins)) if wins else Decimal("0")
        avg_loss = sum(losses) / Decimal(len(losses)) if losses else Decimal("0")

        return avg_win, avg_loss

    @staticmethod
    def calculate_sharpe_ratio(
        returns: list[Decimal],
        risk_free_rate: Decimal = Decimal("0.05"),
    ) -> Optional[Decimal]:
        """Calculate Sharpe ratio.

        Args:
            returns: List of period returns
            risk_free_rate: Annual risk-free rate (default 5%)

        Returns:
            Sharpe ratio or None if insufficient data

        Formula:
            Sharpe = (mean_return - risk_free_rate) / std_dev
        """
        if len(returns) < 2:
            return None

        # Mean return
        mean_return = sum(returns) / Decimal(len(returns))

        # Standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / Decimal(
            len(returns) - 1
        )
        std_dev = variance.sqrt()

        if std_dev == Decimal("0"):
            return None

        # Sharpe ratio
        sharpe = (mean_return - risk_free_rate) / std_dev
        return sharpe

    @staticmethod
    def calculate_roi(
        final_value: Decimal,
        initial_value: Decimal,
    ) -> Decimal:
        """Calculate return on investment.

        Args:
            final_value: Final portfolio value
            initial_value: Initial portfolio value

        Returns:
            ROI as percentage (e.g., 0.15 for 15%)
        """
        if initial_value <= Decimal("0"):
            return Decimal("0")

        return (final_value - initial_value) / initial_value
