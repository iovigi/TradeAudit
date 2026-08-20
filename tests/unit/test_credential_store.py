"""
Unit tests for CredentialStore using keyring mocking.
"""

import pytest
from unittest.mock import patch, MagicMock

from tradeaudit.infrastructure.security.credential_store import CredentialStore, SERVICE_NAME
from tradeaudit.app.exceptions import CredentialStoreError


def test_credential_store_save_and_get():
    store_dict = {}

    def mock_set_password(service, username, password):
        store_dict[(service, username)] = password

    def mock_get_password(service, username):
        return store_dict.get((service, username))

    def mock_delete_password(service, username):
        if (service, username) in store_dict:
            del store_dict[(service, username)]
        else:
            import keyring.errors
            raise keyring.errors.PasswordDeleteError("Not found")

    with patch("keyring.set_password", side_effect=mock_set_password), \
         patch("keyring.get_password", side_effect=mock_get_password), \
         patch("keyring.delete_password", side_effect=mock_delete_password):

        store = CredentialStore()
        login = 12345678
        password = "SecretPassword123!"

        store.save_password(login, password)
        retrieved = store.get_password(login)
        assert retrieved == password

        store.delete_password(login)
        assert store.get_password(login) is None


def test_credential_store_invalid_inputs():
    store = CredentialStore()
    with pytest.raises(CredentialStoreError):
        store.save_password(0, "password")

    with pytest.raises(CredentialStoreError):
        store.save_password(12345, None)

    assert store.get_password(0) is None
