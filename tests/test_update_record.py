import xmlrpc.client
from unittest.mock import patch

from src.mcp_server import OdooConnection, update_record


class TestUpdateRecord:
    def test_successful_update(self):
        with patch.object(OdooConnection, "execute", return_value=True):
            result = update_record("res.partner", 1, {"name": "Updated"})
        assert result == {"success": True, "id": 1}

    def test_odoo_returns_false(self):
        with patch.object(OdooConnection, "execute", return_value=False):
            result = update_record("res.partner", 1, {"name": "Updated"})
        assert "error" in result

    def test_disallowed_model(self):
        result = update_record("secret.table", 1, {"name": "Test"})
        assert "error" in result

    def test_record_id_zero(self):
        result = update_record("res.partner", 0, {"name": "Test"})
        assert "error" in result

    def test_record_id_negative(self):
        result = update_record("res.partner", -1, {"name": "Test"})
        assert "error" in result

    def test_non_integer_record_id(self):
        result = update_record("res.partner", "not an int", {"name": "Test"})
        assert "error" in result

    def test_empty_values(self):
        result = update_record("res.partner", 1, {})
        assert "error" in result

    def test_non_dict_values(self):
        result = update_record("res.partner", 1, "not a dict")
        assert "error" in result

    def test_read_only_mode(self):
        with patch("src.mcp_server.READ_ONLY_MODE", True):
            result = update_record("res.partner", 1, {"name": "Test"})
        assert "error" in result

    def test_xmlrpc_fault_caught(self):
        fault = xmlrpc.client.Fault(1, "Access denied")
        with patch.object(OdooConnection, "execute", side_effect=fault):
            result = update_record("res.partner", 1, {"name": "Test"})
        assert "error" in result

    def test_connection_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=ConnectionError("Cannot connect")
        ):
            result = update_record("res.partner", 1, {"name": "Test"})
        assert "error" in result

    def test_permission_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=PermissionError("Not allowed")
        ):
            result = update_record("res.partner", 1, {"name": "Test"})
        assert "error" in result
