import xmlrpc.client
from unittest.mock import patch

from src.mcp_server import OdooConnection, search_records


class TestSearchRecords:
    def test_successful_search(self):
        records = [{"id": 1, "name": "Test"}]
        with patch.object(OdooConnection, "execute", return_value=records):
            result = search_records("res.partner")
        assert result == {"records": records, "count": 1}

    def test_empty_domain_defaults(self):
        with patch.object(OdooConnection, "execute", return_value=[]):
            result = search_records("res.partner", domain=None)
        assert result == {"records": [], "count": 0}

    def test_limit_exceeds_max(self):
        result = search_records("res.partner", limit=501)
        assert "error" in result

    def test_limit_zero(self):
        result = search_records("res.partner", limit=0)
        assert "error" in result

    def test_limit_negative(self):
        result = search_records("res.partner", limit=-1)
        assert "error" in result

    def test_negative_offset(self):
        result = search_records("res.partner", offset=-1)
        assert "error" in result

    def test_disallowed_model(self):
        result = search_records("secret.table")
        assert "error" in result

    def test_empty_model_string(self):
        result = search_records("")
        assert "error" in result

    def test_unsafe_domain_or_too_many_conditions(self):
        # 5 "|" operators → 6 conditions; exceeds the 5-condition limit.
        domain = [
            "|",
            "|",
            "|",
            "|",
            "|",
            ("f", "=", 1),
            ("f", "=", 2),
            ("f", "=", 3),
            ("f", "=", 4),
            ("f", "=", 5),
            ("f", "=", 6),
        ]
        result = search_records("res.partner", domain=domain)
        assert "error" in result

    def test_xmlrpc_fault_caught(self):
        fault = xmlrpc.client.Fault(1, "Access denied")
        with patch.object(OdooConnection, "execute", side_effect=fault):
            result = search_records("res.partner")
        assert "error" in result

    def test_connection_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=ConnectionError("Cannot connect")
        ):
            result = search_records("res.partner")
        assert "error" in result

    def test_permission_error_caught(self):
        with patch.object(
            OdooConnection, "execute", side_effect=PermissionError("Not allowed")
        ):
            result = search_records("res.partner")
        assert "error" in result
