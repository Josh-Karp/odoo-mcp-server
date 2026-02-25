import xmlrpc.client
from unittest.mock import MagicMock, patch

import pytest

from src.mcp_server import OdooConnection


class TestOdooConnectionAuthenticate:
    def test_authenticate_success(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_proxy.return_value = mock_common
            mock_common.authenticate.return_value = 1

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"

            uid = conn.authenticate()

        assert uid == 1
        assert conn.uid == 1

    def test_authenticate_connection_error(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_proxy.return_value = mock_common
            mock_common.authenticate.side_effect = Exception("Connection refused")

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"

            with pytest.raises(ConnectionError):
                conn.authenticate()

    def test_authenticate_permission_error_uid_false(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_proxy.return_value = mock_common
            mock_common.authenticate.return_value = False

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"

            with pytest.raises(PermissionError):
                conn.authenticate()

    def test_authenticate_permission_error_uid_zero(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_proxy.return_value = mock_common
            mock_common.authenticate.return_value = 0

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"

            with pytest.raises(PermissionError):
                conn.authenticate()


class TestOdooConnectionValidateConfig:
    def test_validate_config_raises_when_url_missing(self):
        with (
            patch("src.mcp_server.ODOO_URL", ""),
            patch("src.mcp_server.ODOO_DB", "testdb"),
            patch("src.mcp_server.ODOO_USERNAME", "user"),
            patch("src.mcp_server.ODOO_PASSWORD", "pass"),
        ):
            conn = OdooConnection()
            with pytest.raises(ValueError):
                conn._validate_config()

    def test_validate_config_raises_when_db_missing(self):
        with (
            patch("src.mcp_server.ODOO_URL", "http://test"),
            patch("src.mcp_server.ODOO_DB", ""),
            patch("src.mcp_server.ODOO_USERNAME", "user"),
            patch("src.mcp_server.ODOO_PASSWORD", "pass"),
        ):
            conn = OdooConnection()
            with pytest.raises(ValueError):
                conn._validate_config()

    def test_validate_config_raises_when_username_missing(self):
        with (
            patch("src.mcp_server.ODOO_URL", "http://test"),
            patch("src.mcp_server.ODOO_DB", "testdb"),
            patch("src.mcp_server.ODOO_USERNAME", ""),
            patch("src.mcp_server.ODOO_PASSWORD", "pass"),
        ):
            conn = OdooConnection()
            with pytest.raises(ValueError):
                conn._validate_config()

    def test_validate_config_raises_when_password_missing(self):
        with (
            patch("src.mcp_server.ODOO_URL", "http://test"),
            patch("src.mcp_server.ODOO_DB", "testdb"),
            patch("src.mcp_server.ODOO_USERNAME", "user"),
            patch("src.mcp_server.ODOO_PASSWORD", ""),
        ):
            conn = OdooConnection()
            with pytest.raises(ValueError):
                conn._validate_config()


class TestOdooConnectionExecute:
    def test_execute_calls_execute_kw(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_models = MagicMock()
            mock_proxy.return_value = mock_models
            mock_models.execute_kw.return_value = [{"id": 1}]

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"
            conn.uid = 1

            result = conn.execute(
                "res.partner", "search_read", [[]], {"fields": ["name"]}
            )

        mock_models.execute_kw.assert_called_once_with(
            "testdb",
            1,
            "pass",
            "res.partner",
            "search_read",
            [[]],
            {"fields": ["name"]},
        )
        assert result == [{"id": 1}]

    def test_execute_reauth_on_session_expiry(self):
        fault = xmlrpc.client.Fault(100, "Session expired")

        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_models = MagicMock()
            mock_proxy.return_value = mock_models
            mock_models.execute_kw.side_effect = [fault, [{"id": 1}]]

            conn = OdooConnection()
            conn.url = "http://test"
            conn.db = "testdb"
            conn.username = "user"
            conn.password = "pass"
            conn.uid = 1

            with patch.object(conn, "authenticate") as mock_auth:
                result = conn.execute("res.partner", "search_read", [[]], {})

        mock_auth.assert_called_once()
        assert result == [{"id": 1}]
