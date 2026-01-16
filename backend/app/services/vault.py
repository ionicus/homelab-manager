"""Vault service for encrypting and decrypting secrets."""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import Config

logger = logging.getLogger(__name__)


class VaultService:
    """Service for encrypting and decrypting vault secrets.

    Uses Fernet symmetric encryption with a key derived from the
    VAULT_ENCRYPTION_KEY environment variable.
    """

    _fernet: Fernet | None = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or create the Fernet cipher.

        Returns:
            Fernet cipher instance
        """
        if cls._fernet is None:
            key = cls._derive_key(Config.VAULT_ENCRYPTION_KEY)
            cls._fernet = Fernet(key)
        return cls._fernet

    @staticmethod
    def _derive_key(key_string: str) -> bytes:
        """Derive a valid Fernet key from the config key.

        Fernet requires a 32-byte base64-encoded key. This method ensures
        we always get a valid key regardless of the input format.

        Args:
            key_string: The key from configuration

        Returns:
            A valid Fernet key (32 bytes, base64-encoded)
        """
        # Try to use the key directly if it's already a valid Fernet key
        try:
            # If it's a valid base64 key of the right length, use it
            decoded = base64.urlsafe_b64decode(key_string)
            if len(decoded) == 32:
                return key_string.encode()
        except Exception:
            pass

        # Otherwise, derive a key using SHA-256
        key_hash = hashlib.sha256(key_string.encode()).digest()
        return base64.urlsafe_b64encode(key_hash)

    @classmethod
    def encrypt(cls, plaintext: str) -> bytes:
        """Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Encrypted bytes
        """
        fernet = cls._get_fernet()
        return fernet.encrypt(plaintext.encode("utf-8"))

    @classmethod
    def decrypt(cls, encrypted: bytes) -> str:
        """Decrypt encrypted bytes to a string.

        Args:
            encrypted: The encrypted bytes

        Returns:
            Decrypted string

        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        fernet = cls._get_fernet()
        try:
            return fernet.decrypt(encrypted).decode("utf-8")
        except InvalidToken as e:
            logger.error("Failed to decrypt vault secret - invalid key or corrupted data")
            raise ValueError("Failed to decrypt secret") from e

    @classmethod
    def reset(cls):
        """Reset the cached Fernet instance.

        Useful for testing or when the key changes.
        """
        cls._fernet = None
