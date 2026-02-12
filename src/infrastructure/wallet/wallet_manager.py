"""Production wallet manager."""

import logging
from decimal import Decimal

from src.domain.entities.production_wallet import ProductionWallet
from src.domain.value_objects.private_key import PrivateKey
from src.infrastructure.wallet.key_manager import KeyManager

logger = logging.getLogger(__name__)


class WalletManager:
    """Manager for production hot/cold wallets.
    
    Responsibilities:
    - Create/load wallets from mnemonic
    - Manage hot/cold split
    - Rebalance when needed
    - Secure key storage
    """

    def __init__(self, key_manager: KeyManager):
        """Initialize wallet manager.
        
        Args:
            key_manager: Key manager for mnemonic/private keys
        """
        self.key_manager = key_manager
        
        # SECURITY: Never log wallet creation
        logger.info("WalletManager initialized")

    def create_wallet(
        self,
        total_balance: Decimal,
        hot_wallet_pct: Decimal = Decimal("0.15"),
    ) -> tuple[ProductionWallet, PrivateKey, str]:
        """Create new production wallet.
        
        Args:
            total_balance: Total capital to allocate
            hot_wallet_pct: Percentage for hot wallet (10-20%)
            
        Returns:
            Tuple of (wallet, private_key, mnemonic)
            
        SECURITY:
        - Mnemonic should be stored OFFLINE (written down)
        - Private key should be encrypted before storage
        - NEVER log mnemonic or private key
        """
        # Generate mnemonic and derive keys
        mnemonic, private_key, address = self.key_manager.generate_wallet()
        
        # Calculate hot/cold split
        hot_balance = total_balance * hot_wallet_pct
        cold_balance = total_balance - hot_balance
        
        wallet = ProductionWallet(
            address=address,
            total_balance=total_balance,
            hot_balance=hot_balance,
            cold_balance=cold_balance,
            hot_wallet_pct=hot_wallet_pct,
        )
        
        logger.info(
            "Production wallet created",
            extra={
                "address": address,
                "total_balance": float(total_balance),
                "hot_balance": float(hot_balance),
                "cold_balance": float(cold_balance),
            },
        )
        
        return wallet, private_key, mnemonic

    def load_wallet(
        self,
        mnemonic: str,
        total_balance: Decimal,
        hot_wallet_pct: Decimal = Decimal("0.15"),
    ) -> tuple[ProductionWallet, PrivateKey]:
        """Load existing wallet from mnemonic.
        
        Args:
            mnemonic: BIP39 mnemonic phrase
            total_balance: Current total balance
            hot_wallet_pct: Hot wallet percentage
            
        Returns:
            Tuple of (wallet, private_key)
        """
        # Derive keys from mnemonic
        private_key, address = self.key_manager.derive_from_mnemonic(mnemonic)
        
        # Calculate hot/cold split
        hot_balance = total_balance * hot_wallet_pct
        cold_balance = total_balance - hot_balance
        
        wallet = ProductionWallet(
            address=address,
            total_balance=total_balance,
            hot_balance=hot_balance,
            cold_balance=cold_balance,
            hot_wallet_pct=hot_wallet_pct,
        )
        
        logger.info(
            "Production wallet loaded",
            extra={
                "address": address,
                "total_balance": float(total_balance),
            },
        )
        
        return wallet, private_key

    def check_rebalance(self, wallet: ProductionWallet) -> dict:
        """Check if rebalance needed.
        
        Args:
            wallet: Production wallet
            
        Returns:
            Rebalance info dict
        """
        if not wallet.needs_rebalance():
            return {"needed": False}
        
        amount, direction = wallet.calculate_rebalance()
        
        logger.info(
            "Rebalance needed",
            extra={
                "amount": float(amount),
                "direction": direction,
                "current_hot": float(wallet.hot_balance),
                "target_hot": float(wallet.total_balance * wallet.hot_wallet_pct),
            },
        )
        
        return {
            "needed": True,
            "amount": amount,
            "direction": direction,
        }

    def execute_rebalance(
        self,
        wallet: ProductionWallet,
        amount: Decimal,
        direction: str,
    ) -> ProductionWallet:
        """Execute hot/cold rebalance.
        
        Args:
            wallet: Current wallet
            amount: Amount to transfer
            direction: 'hot_to_cold' or 'cold_to_hot'
            
        Returns:
            Updated wallet
        """
        if direction == "hot_to_cold":
            new_wallet = wallet.transfer_to_cold(amount)
        elif direction == "cold_to_hot":
            new_wallet = wallet.transfer_to_hot(amount)
        else:
            raise ValueError(f"Invalid direction: {direction}")
        
        logger.info(
            "Rebalance executed",
            extra={
                "amount": float(amount),
                "direction": direction,
                "new_hot": float(new_wallet.hot_balance),
                "new_cold": float(new_wallet.cold_balance),
            },
        )
        
        return new_wallet
