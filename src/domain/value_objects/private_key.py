"""Private key value object with security."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PrivateKey:
    """Private key value object.
    
    SECURITY:
    - NEVER log this object
    - NEVER serialize to JSON
    - NEVER send over network
    - NEVER store in database unencrypted
    - NEVER print or display
    """

    _value: str  # Private leading underscore to discourage direct access

    def __post_init__(self):
        """Validate private key."""
        if not self._value:
            raise ValueError("Private key cannot be empty")
        
        # Basic validation: should be hex string (64 chars for 32 bytes)
        if not all(c in '0123456789abcdefABCDEF' for c in self._value.replace('0x', '')):
            raise ValueError("Private key must be hexadecimal")
    
    def __repr__(self) -> str:
        """Secure repr - NEVER show actual key."""
        return "PrivateKey(***REDACTED***)"
    
    def __str__(self) -> str:
        """Secure str - NEVER show actual key."""
        return "***REDACTED***"
    
    @property
    def value(self) -> str:
        """Get private key value.
        
        WARNING: Only use for signing transactions.
        NEVER log, print, or store the return value.
        """
        return self._value
    
    def to_bytes(self) -> bytes:
        """Convert to bytes for signing.
        
        Returns:
            Private key as bytes
        """
        hex_str = self._value.replace('0x', '')
        return bytes.fromhex(hex_str)
