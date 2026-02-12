"""Key manager for BIP39/BIP32/BIP44 wallet derivation."""

import logging
import os
from cryptography.fernet import Fernet
from mnemonic import Mnemonic

from src.domain.value_objects.private_key import PrivateKey

logger = logging.getLogger(__name__)


class KeyManager:
    """Manager for mnemonic and private key operations.
    
    Handles:
    - BIP39 mnemonic generation
    - BIP32/BIP44 HD wallet derivation
    - Private key encryption/decryption
    - Secure key storage
    """

    def __init__(self, encryption_key: str | None = None):
        """Initialize key manager.
        
        Args:
            encryption_key: Fernet encryption key (base64 encoded)
        """
        self.mnemonic_gen = Mnemonic("english")
        
        # Encryption for at-rest storage
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = None
        
        logger.info("KeyManager initialized")

    def generate_mnemonic(self, strength: int = 256) -> str:
        """Generate BIP39 mnemonic phrase.
        
        Args:
            strength: Bits of entropy (128, 160, 192, 224, 256)
            
        Returns:
            Mnemonic phrase (24 words for 256 bits)
            
        SECURITY: Store mnemonic OFFLINE (write down on paper)
        """
        mnemonic = self.mnemonic_gen.generate(strength=strength)
        
        # NEVER log mnemonic
        logger.info("Mnemonic generated", extra={"strength": strength})
        
        return mnemonic

    def validate_mnemonic(self, mnemonic: str) -> bool:
        """Validate BIP39 mnemonic phrase.
        
        Args:
            mnemonic: Mnemonic phrase to validate
            
        Returns:
            True if valid
        """
        return self.mnemonic_gen.check(mnemonic)

    def derive_from_mnemonic(
        self,
        mnemonic: str,
        account: int = 0,
        index: int = 0,
    ) -> tuple[PrivateKey, str]:
        """Derive private key and address from mnemonic.
        
        Uses BIP44 path: m/44'/60'/0'/0/{index}
        - 44' = BIP44
        - 60' = Ethereum
        - 0' = Account 0
        - 0 = External chain
        - index = Address index
        
        Args:
            mnemonic: BIP39 mnemonic phrase
            account: Account number (default 0)
            index: Address index (default 0)
            
        Returns:
            Tuple of (private_key, address)
        """
        if not self.validate_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        # For production, would use proper BIP32/BIP44 derivation
        # Simplified here - real implementation needs eth_account
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        
        # Derive account
        account_obj = Account.from_mnemonic(
            mnemonic,
            account_path=f"m/44'/60'/{account}'/0/{index}"
        )
        
        private_key = PrivateKey(account_obj.key.hex())
        address = account_obj.address
        
        logger.info(
            "Keys derived from mnemonic",
            extra={"address": address, "account": account, "index": index},
        )
        
        return private_key, address

    def generate_wallet(
        self,
        account: int = 0,
        index: int = 0,
    ) -> tuple[str, PrivateKey, str]:
        """Generate new wallet (mnemonic + keys).
        
        Args:
            account: Account number
            index: Address index
            
        Returns:
            Tuple of (mnemonic, private_key, address)
        """
        mnemonic = self.generate_mnemonic()
        private_key, address = self.derive_from_mnemonic(mnemonic, account, index)
        
        return mnemonic, private_key, address

    def encrypt_private_key(self, private_key: PrivateKey) -> bytes:
        """Encrypt private key for storage.
        
        Args:
            private_key: Private key to encrypt
            
        Returns:
            Encrypted private key bytes
        """
        if not self.cipher:
            raise ValueError("Encryption key not configured")
        
        encrypted = self.cipher.encrypt(private_key.value.encode())
        
        logger.info("Private key encrypted for storage")
        
        return encrypted

    def decrypt_private_key(self, encrypted: bytes) -> PrivateKey:
        """Decrypt private key from storage.
        
        Args:
            encrypted: Encrypted private key bytes
            
        Returns:
            Decrypted private key
        """
        if not self.cipher:
            raise ValueError("Encryption key not configured")
        
        decrypted = self.cipher.decrypt(encrypted).decode()
        
        logger.info("Private key decrypted from storage")
        
        return PrivateKey(decrypted)

    @staticmethod
    def generate_encryption_key() -> str:
        """Generate new Fernet encryption key.
        
        Returns:
            Base64 encoded encryption key
        """
        key = Fernet.generate_key()
        return key.decode()
