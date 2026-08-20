"""
Secure credential storage using OS Native Credential Locker via Python keyring.
"""

import logging
from typing import Optional
import keyring
from keyring.errors import KeyringError

from tradeaudit.app.exceptions import CredentialStoreError

logger = logging.getLogger("tradeaudit.infrastructure.security.credential_store")

SERVICE_NAME = "TradeAudit_MT5"


class CredentialStore:
    """Provides secure password storage and retrieval using OS keyring."""

    def __init__(self, service_name: str = SERVICE_NAME):
        self.service_name = service_name

    def save_password(self, login: int, password: str) -> None:
        """Securely store MT5 account password."""
        if not login:
            raise CredentialStoreError("Cannot store password for invalid login (0 or empty).")
        if password is None:
            raise CredentialStoreError("Password cannot be None.")

        username = str(login)
        try:
            keyring.set_password(self.service_name, username, password)
            logger.info("Successfully stored secure password for account %s.", username)
        except KeyringError as e:
            logger.error("Failed to store password in keyring for account %s: %s", username, str(e))
            raise CredentialStoreError(f"Failed to store credentials: {e}") from e
        except Exception as e:
            logger.error("Unexpected error saving credentials for account %s: %s", username, str(e))
            raise CredentialStoreError(f"Unexpected credential storage error: {e}") from e

    def get_password(self, login: int) -> Optional[str]:
        """Retrieve MT5 account password from keyring."""
        if not login:
            return None

        username = str(login)
        try:
            password = keyring.get_password(self.service_name, username)
            if password:
                logger.info("Successfully retrieved secure password for account %s.", username)
            else:
                logger.info("No stored password found for account %s.", username)
            return password
        except KeyringError as e:
            logger.error("Failed to read password from keyring for account %s: %s", username, str(e))
            raise CredentialStoreError(f"Failed to read credentials: {e}") from e
        except Exception as e:
            logger.error("Unexpected error reading credentials for account %s: %s", username, str(e))
            raise CredentialStoreError(f"Unexpected credential reading error: {e}") from e

    def delete_password(self, login: int) -> None:
        """Delete stored password for MT5 account."""
        if not login:
            return

        username = str(login)
        try:
            keyring.delete_password(self.service_name, username)
            logger.info("Successfully deleted password for account %s.", username)
        except keyring.errors.PasswordDeleteError:
            logger.warning("No password existed to delete for account %s.", username)
        except KeyringError as e:
            logger.error("Failed to delete password from keyring for account %s: %s", username, str(e))
            raise CredentialStoreError(f"Failed to delete credentials: {e}") from e
