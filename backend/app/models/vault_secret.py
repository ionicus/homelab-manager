"""Vault secret model for storing encrypted secrets."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text

from app.database import Base


class VaultSecret(Base):
    """Store encrypted secrets for use in automation playbooks.

    Secrets are encrypted at rest using Fernet symmetric encryption.
    The encryption key is stored in the VAULT_ENCRYPTION_KEY environment variable.
    """

    __tablename__ = "vault_secrets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Encrypted content stored as binary
    encrypted_content = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_content: bool = False):
        """Convert model to dictionary.

        Args:
            include_content: If True, includes decrypted content (use with caution)

        Returns:
            Dictionary representation of the secret
        """
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        # Content is only included when explicitly requested
        # It must be decrypted by the caller using VaultService
        return result

    def __repr__(self):
        """String representation."""
        return f"<VaultSecret {self.name}>"
