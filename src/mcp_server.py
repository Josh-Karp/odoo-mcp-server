import os
import xmlrpc.client
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ODOO_URL = os.environ.get("ODOO_URL", "")
ODOO_DB = os.environ.get("ODOO_DB", "")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "")
READ_ONLY_MODE = os.environ.get("READ_ONLY_MODE", "false").strip().lower() == "true"

ALLOWED_MODELS = [
    "res.partner",
    "res.users",
    "sale.order",
    "sale.order.line",
    "purchase.order",
    "purchase.order.line",
    "account.move",
    "account.move.line",
    "stock.picking",
    "stock.move",
    "product.product",
    "product.template",
    "mrp.production",
    "project.project",
    "project.task",
    "hr.employee",
    "crm.lead",
]

MAX_LIMIT = 500

# ---------------------------------------------------------------------------
# Odoo connection helper
# ---------------------------------------------------------------------------


class OdooConnection:
    """Manages XML-RPC connections and authentication to an Odoo instance."""

    def __init__(self) -> None:
        self._uid: int | None = None

    def _validate_config(self) -> None:
        missing = [
            name
            for name, val in [
                ("ODOO_URL", ODOO_URL),
                ("ODOO_DB", ODOO_DB),
                ("ODOO_USERNAME", ODOO_USERNAME),
                ("ODOO_PASSWORD", ODOO_PASSWORD),
            ]
            if not val
        ]
        if missing:
            raise ValueError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )

    def authenticate(self) -> int:
        """Authenticate against Odoo and return the uid."""
        self._validate_config()
        try:
            common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
            uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        except Exception as exc:
            raise ConnectionError(
                f"Failed to connect to Odoo at {ODOO_URL}: {exc}"
            ) from exc

        if not uid:
            raise PermissionError(
                "Odoo authentication failed. Check ODOO_USERNAME and ODOO_PASSWORD."
            )
        self._uid = uid
        return uid

    @property
    def uid(self) -> int:
        if self._uid is None:
            self.authenticate()
        return self._uid  # type: ignore[return-value]

    def execute(self, model: str, method: str, *args: Any) -> Any:
        """Execute an Odoo XML-RPC call, re-authenticating on session expiry."""
        self._validate_config()
        models_proxy = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        try:
            return models_proxy.execute_kw(
                ODOO_DB, self.uid, ODOO_PASSWORD, model, method, *args
            )
        except xmlrpc.client.Fault as fault:
            # Session expired — re-authenticate once and retry
            if "session" in fault.faultString.lower() or fault.faultCode == 100:
                self._uid = None
                return models_proxy.execute_kw(
                    ODOO_DB, self.uid, ODOO_PASSWORD, model, method, *args
                )
            raise


_odoo = OdooConnection()

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("odoo-mcp-server")

# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------


def _validate_model(model: str) -> str | None:
    """Return an error string if the model is not allowed, else None."""
    if not isinstance(model, str) or not model.strip():
        return "Parameter 'model' must be a non-empty string."
    if model not in ALLOWED_MODELS:
        return (
            f"Model '{model}' is not in the allow-list. "
            f"Allowed models: {', '.join(ALLOWED_MODELS)}"
        )
    return None


def _validate_domain(domain: list) -> str | None:
    """Return an error string if the domain is considered unsafe."""
    if not isinstance(domain, list):
        return "Parameter 'domain' must be a list."
    # Reject top-level OR with more than 5 conditions
    if domain and domain[0] == "|":
        conditions = [item for item in domain if item != "|"]
        if len(conditions) > 5:
            return (
                "Domain rejected: top-level OR ('|') with more than 5 conditions "
                "is not allowed to prevent overly broad queries."
            )
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_records(
    model: str,
    domain: list | None = None,
    fields: list | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Search for records in Odoo using domain filters.

    Args:
        model: The Odoo model to search (must be in the allow-list).
        domain: Odoo domain filter (e.g. [["name", "=", "Test"]]). Defaults to [].
        fields: List of fields to return. Defaults to [] (all fields).
        limit: Max number of records to return (default 100, max 500).
        offset: Offset for pagination. Defaults to 0.
    """
    if domain is None:
        domain = []
    if fields is None:
        fields = []

    if err := _validate_model(model):
        return {"error": err}
    if err := _validate_domain(domain):
        return {"error": err}
    if not isinstance(limit, int) or limit < 1:
        return {"error": "Parameter 'limit' must be a positive integer."}
    if limit > MAX_LIMIT:
        return {"error": f"Parameter 'limit' cannot exceed {MAX_LIMIT}."}
    if not isinstance(offset, int) or offset < 0:
        return {"error": "Parameter 'offset' must be a non-negative integer."}

    try:
        records = _odoo.execute(
            model,
            "search_read",
            [domain],
            {"fields": fields, "limit": limit, "offset": offset},
        )
        return {"records": records, "count": len(records)}
    except PermissionError as exc:
        return {"error": f"Permission denied: {exc}"}
    except ConnectionError as exc:
        return {"error": f"Connection error: {exc}"}
    except xmlrpc.client.Fault as fault:
        return {"error": f"Odoo error: {fault.faultString}"}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def create_record(model: str, values: dict) -> dict:
    """Create a new record in Odoo.

    Args:
        model: The Odoo model to create a record in (must be in the allow-list).
        values: Field values for the new record.
    """
    if READ_ONLY_MODE:
        return {
            "error": "Server is running in read-only mode. create_record is disabled."
        }

    if err := _validate_model(model):
        return {"error": err}
    if not isinstance(values, dict) or not values:
        return {"error": "Parameter 'values' must be a non-empty dict."}

    try:
        new_id = _odoo.execute(model, "create", [values])
        return {"id": new_id}
    except PermissionError as exc:
        return {"error": f"Permission denied: {exc}"}
    except ConnectionError as exc:
        return {"error": f"Connection error: {exc}"}
    except xmlrpc.client.Fault as fault:
        return {"error": f"Odoo error: {fault.faultString}"}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def update_record(model: str, record_id: int, values: dict) -> dict:
    """Update an existing record in Odoo by ID.

    Args:
        model: The Odoo model (must be in the allow-list).
        record_id: The ID of the record to update.
        values: Field values to update.
    """
    if READ_ONLY_MODE:
        return {
            "error": "Server is running in read-only mode. update_record is disabled."
        }

    if err := _validate_model(model):
        return {"error": err}
    if not isinstance(record_id, int) or record_id <= 0:
        return {"error": "Parameter 'record_id' must be a positive integer."}
    if not isinstance(values, dict) or not values:
        return {"error": "Parameter 'values' must be a non-empty dict."}

    try:
        result = _odoo.execute(model, "write", [[record_id], values])
        if not result:
            return {
                "error": f"Record with id={record_id} not found or could not be updated."
            }
        return {"success": True, "id": record_id}
    except PermissionError as exc:
        return {"error": f"Permission denied: {exc}"}
    except ConnectionError as exc:
        return {"error": f"Connection error: {exc}"}
    except xmlrpc.client.Fault as fault:
        return {"error": f"Odoo error: {fault.faultString}"}
    except Exception as exc:
        return {"error": f"Unexpected error: {exc}"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
