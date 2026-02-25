import xmlrpc.client
from unittest.mock import patch

from src.mcp_server import OdooConnection, create_record


class TestCreateRecord:
    def test_successful_create(self):
        with patch.object(OdooConnection, "execute", return_value=42):
            result = create_record("res.partner", {"name": "Test"})
        assert result == {"id": 42}

    def test_disallowed_model(self):
        result = create_record("secret.table", {"name": "Test"})
        assert "error" in result

    def test_empty_values(self):
        result = create_record("res.partner", {})
        assert "error" in result

    def test_non_dict_values(self):
        result = create_record("res.partner", "not a dict")
        assert "error" in result

    def test_read_only_mode(self):
        with patch("src.mcp_server.READ_ONLY_MODE", True):
            result = create_record("res.partner", {"name": "Test"})
        assert "error" in result

    def test_xmlrpc_fault_caught(self):
        fault = xmlrpc.client.Fault(1, "Access denied")
        with patch.object(OdooConnection, "execute", side_effect=fault):
            result = create_record("res.partner", {"name": "Test"})
        assert "error" in result

    def test_connection_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=ConnectionError("Cannot connect")
        ):
            result = create_record("res.partner", {"name": "Test"})
        assert "error" in result

    def test_permission_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=PermissionError("Not allowed")
        ):
            result = create_record("res.partner", {"name": "Test"})
        assert "error" in result
