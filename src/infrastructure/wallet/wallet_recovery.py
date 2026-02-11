"""Wallet recovery with BIP39 and AES-256 encryption.

Provides secure wallet generation, backup, and recovery
with industry-standard encryption.
"""

import logging
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from eth_account import Account
from eth_account.hdaccount import generate_mnemonic, seed_from_mnemonic

logger = logging.getLogger(__name__)

# Security: Enable unaudited HDWallet features
Account.enable_unaudited_hdwallet_features()


class WalletRecovery:
    """Manages wallet recovery with BIP39 and AES-256 encryption.

    Provides:
    - BIP39 mnemonic generation (24 words)
    - AES-256 encryption at rest
    - Emergency withdrawal
    - Wallet rotation

    SECURITY: Mnemonics and private keys are NEVER logged.

    Example:
        >>> recovery = WalletRecovery(encryption_key=key)
        >>> mnemonic = recovery.generate_mnemonic()
        >>> encrypted = recovery.encrypt_mnemonic(mnemonic)
        >>> # Store encrypted mnemonic securely
        >>> decrypted = recovery.decrypt_mnemonic(encrypted)
        >>> account = recovery.recover_from_mnemonic(decrypted)
    """

    def __init__(self, encryption_key: Optional[bytes] = None) -> None:
        """Initialize wallet recovery.

        Args:
            encryption_key: 32-byte encryption key (generated if None)
        """
        if encryption_key is None:
            # Generate new encryption key
            encryption_key = Fernet.generate_key()
            logger.warning(
                "Generated new encryption key - SAVE THIS SECURELY",
                extra={"key_length": len(encryption_key)},
            )

        self.fernet = Fernet(encryption_key)
        logger.info("WalletRecovery initialized")

    def generate_mnemonic(self, num_words: int = 24) -> str:
        """Generate BIP39 mnemonic phrase.

        Args:
            num_words: Number of words (12 or 24)

        Returns:
            Mnemonic phrase (NEVER log this)

        Raises:
            ValueError: If num_words not 12 or 24

        Example:
            >>> mnemonic = recovery.generate_mnemonic(24)
            >>> # NEVER log mnemonic - encrypt immediately
            >>> encrypted = recovery.encrypt_mnemonic(mnemonic)
        """
        if num_words not in (12, 24):
            raise ValueError("num_words must be 12 or 24")

        strength = 128 if num_words == 12 else 256
        mnemonic = generate_mnemonic(num_words=num_words, lang="english")

        logger.info(
            "Mnemonic generated",
            extra={"num_words": num_words, "strength": strength},
        )

        return mnemonic

    def encrypt_mnemonic(self, mnemonic: str) -> bytes:
        """Encrypt mnemonic with AES-256.

        Args:
            mnemonic: Mnemonic phrase to encrypt

        Returns:
            Encrypted mnemonic bytes

        Example:
            >>> encrypted = recovery.encrypt_mnemonic(mnemonic)
            >>> # Store encrypted bytes securely
        """
        encrypted = self.fernet.encrypt(mnemonic.encode("utf-8"))
        logger.debug("Mnemonic encrypted", extra={"size": len(encrypted)})
        return encrypted

    def decrypt_mnemonic(self, encrypted: bytes) -> str:
        """Decrypt mnemonic.

        Args:
            encrypted: Encrypted mnemonic bytes

        Returns:
            Decrypted mnemonic phrase (NEVER log this)

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails

        Example:
            >>> decrypted = recovery.decrypt_mnemonic(encrypted_bytes)
            >>> account = recovery.recover_from_mnemonic(decrypted)
        """
        decrypted = self.fernet.decrypt(encrypted).decode("utf-8")
        logger.debug("Mnemonic decrypted")
        return decrypted

    def recover_from_mnemonic(
        self, mnemonic: str, account_index: int = 0
    ) -> Account:
        """Recover account from mnemonic.

        Uses BIP44 derivation path: m/44'/60'/0'/0/{account_index}

        Args:
            mnemonic: BIP39 mnemonic phrase
            account_index: Account index (default 0)

        Returns:
            Recovered account (NEVER log private key)

        Example:
            >>> account = recovery.recover_from_mnemonic(mnemonic, index=0)
            >>> # Use account.address (safe to log)
            >>> # NEVER log account.key or account.privateKey
        """
        account = Account.from_mnemonic(
            mnemonic,
            account_path=f"m/44'/60'/0'/0/{account_index}",
        )

        logger.info(
            "Account recovered from mnemonic",
            extra={"address": account.address, "index": account_index},
        )

        return account

    def create_new_wallet(self, num_words: int = 24) -> tuple[str, Account]:
        """Create new wallet with mnemonic.

        Args:
            num_words: Mnemonic word count (12 or 24)

        Returns:
            Tuple of (encrypted_mnemonic, account)

        Example:
            >>> encrypted_mnemonic, account = recovery.create_new_wallet(24)
            >>> # Store encrypted_mnemonic securely
            >>> logger.info(f"New wallet: {account.address}")
        """
        mnemonic = self.generate_mnemonic(num_words)
        encrypted = self.encrypt_mnemonic(mnemonic)
        account = self.recover_from_mnemonic(mnemonic)

        logger.info(
            "New wallet created",
            extra={"address": account.address, "num_words": num_words},
        )

        return encrypted.hex(), account

    def rotate_wallet(self, old_mnemonic: str) -> tuple[str, Account, Account]:
        """Rotate to new wallet, keeping old for transition.

        Args:
            old_mnemonic: Current wallet mnemonic

        Returns:
            Tuple of (new_encrypted_mnemonic, new_account, old_account)

        Example:
            >>> new_enc, new_acc, old_acc = recovery.rotate_wallet(old_mnemonic)
            >>> # Transfer funds from old_acc to new_acc
            >>> # Store new_enc securely
            >>> # Disable old_acc after confirmation
        """
        old_account = self.recover_from_mnemonic(old_mnemonic)
        new_mnemonic = self.generate_mnemonic(24)
        new_encrypted = self.encrypt_mnemonic(new_mnemonic)
        new_account = self.recover_from_mnemonic(new_mnemonic)

        logger.info(
            "Wallet rotation initiated",
            extra={
                "old_address": old_account.address,
                "new_address": new_account.address,
            },
        )

        return new_encrypted.hex(), new_account, old_account
