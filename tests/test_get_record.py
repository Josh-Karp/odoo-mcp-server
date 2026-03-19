import xmlrpc.client
from unittest.mock import patch

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_server import get_record


@pytest.fixture(autouse=True)
def mock_odoo_execute():
    with patch("mcp_server._odoo.execute") as mock_exec:
        yield mock_exec


def test_get_record_success(mock_odoo_execute):
    mock_odoo_execute.return_value = [
        {"id": 1, "name": "Azure Interior", "email": "azure.interior@example.com"}
    ]
    result = get_record("res.partner", 1)
    assert result == {
        "record": {"id": 1, "name": "Azure Interior", "email": "azure.interior@example.com"}
    }
    mock_odoo_execute.assert_called_once_with(
        "res.partner", "read", [[1]], {"fields": []}
    )


def test_get_record_with_fields(mock_odoo_execute):
    mock_odoo_execute.return_value = [{"id": 1, "name": "Azure Interior"}]
    result = get_record("res.partner", 1, fields=["name"])
    assert result == {"record": {"id": 1, "name": "Azure Interior"}}
    mock_odoo_execute.assert_called_once_with(
        "res.partner", "read", [[1]], {"fields": ["name"]}
    )


def test_get_record_not_found(mock_odoo_execute):
    mock_odoo_execute.return_value = []
    result = get_record("res.partner", 9999)
    assert result == {
        "error": "Record with id=9999 not found in model 'res.partner'."
    }


def test_get_record_disallowed_model(mock_odoo_execute):
    result = get_record("bad.model", 1)
    assert "error" in result
    assert "bad.model" in result["error"]
    mock_odoo_execute.assert_not_called()


def test_get_record_zero_record_id(mock_odoo_execute):
    result = get_record("res.partner", 0)
    assert result == {"error": "Parameter 'record_id' must be a positive integer."}
    mock_odoo_execute.assert_not_called()


def test_get_record_negative_record_id(mock_odoo_execute):
    result = get_record("res.partner", -1)
    assert result == {"error": "Parameter 'record_id' must be a positive integer."}
    mock_odoo_execute.assert_not_called()


def test_get_record_non_integer_record_id(mock_odoo_execute):
    result = get_record("res.partner", "abc")
    assert result == {"error": "Parameter 'record_id' must be a positive integer."}
    mock_odoo_execute.assert_not_called()


def test_get_record_xmlrpc_fault(mock_odoo_execute):
    fault = xmlrpc.client.Fault(1, "Access Denied")
    mock_odoo_execute.side_effect = fault
    result = get_record("res.partner", 1)
    assert result == {"error": "Odoo error: Access Denied"}


def test_get_record_connection_error(mock_odoo_execute):
    mock_odoo_execute.side_effect = ConnectionError("Connection refused")
    result = get_record("res.partner", 1)
    assert result == {"error": "Connection error: Connection refused"}


def test_get_record_permission_error(mock_odoo_execute):
    mock_odoo_execute.side_effect = PermissionError("Not allowed")
    result = get_record("res.partner", 1)
    assert result == {"error": "Permission denied: Not allowed"}
