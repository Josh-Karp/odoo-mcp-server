import os
import xmlrpc.client

ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "false").lower() == "true"

MAX_LIMIT = 500

ALLOWED_MODELS = [
    "res.partner",
    "sale.order",
    "sale.order.line",
    "purchase.order",
    "purchase.order.line",
    "account.move",
    "account.move.line",
    "stock.picking",
    "stock.move",
    "project.project",
    "project.task",
    "hr.employee",
    "hr.leave",
    "product.product",
    "product.template",
    "crm.lead",
    "helpdesk.ticket",
]


class OdooConnection:
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.uid = None

    def _validate_config(self):
        missing = [
            name
            for name, val in [
                ("ODOO_URL", self.url),
                ("ODOO_DB", self.db),
                ("ODOO_USERNAME", self.username),
                ("ODOO_PASSWORD", self.password),
            ]
            if not val
        ]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    def authenticate(self):
        self._validate_config()
        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            uid = common.authenticate(self.db, self.username, self.password, {})
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Odoo: {e}") from e
        if not uid:
            raise PermissionError("Odoo authentication failed: invalid credentials")
        self.uid = uid
        return uid

    def execute(self, model, method, args=None, kwargs=None):
        if not self.uid:
            self.authenticate()
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        try:
            return models.execute_kw(
                self.db, self.uid, self.password, model, method, args, kwargs
            )
        except xmlrpc.client.Fault as e:
            if e.faultCode == 100:
                self.authenticate()
                models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
                return models.execute_kw(
                    self.db, self.uid, self.password, model, method, args, kwargs
                )
            raise


def _validate_model(model):
    if not isinstance(model, str) or not model:
        return f"Invalid model: {model!r}. Must be a non-empty string."
    if model not in ALLOWED_MODELS:
        return f"Model '{model}' is not allowed. Allowed models: {ALLOWED_MODELS}"
    return None


def _validate_domain(domain):
    if not isinstance(domain, list):
        return f"Domain must be a list, got {type(domain).__name__}"
    if "|" in domain:
        conditions = [x for x in domain if isinstance(x, (list, tuple))]
        if len(conditions) > 5:
            return (
                f"Domain with OR operator is limited to 5 conditions, "
                f"got {len(conditions)}"
            )
    return None


def search_records(model, domain=None, fields=None, limit=100, offset=0):
    error = _validate_model(model)
    if error:
        return {"error": error}

    if domain is None:
        domain = []

    error = _validate_domain(domain)
    if error:
        return {"error": error}

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        return {"error": f"limit must be a positive integer, got {limit!r}"}
    if limit > MAX_LIMIT:
        return {"error": f"limit cannot exceed {MAX_LIMIT}, got {limit}"}

    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        return {"error": f"offset must be a non-negative integer, got {offset!r}"}

    try:
        conn = OdooConnection()
        count = conn.execute(model, "search_count", [domain])
        records = conn.execute(
            model,
            "search_read",
            [domain],
            {"fields": fields or [], "limit": limit, "offset": offset},
        )
        return {"records": records, "count": count}
    except xmlrpc.client.Fault as e:
        return {"error": f"Odoo error: {e.faultString}"}
    except ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except PermissionError as e:
        return {"error": f"Permission error: {e}"}


def create_record(model, values):
    if READ_ONLY_MODE:
        return {"error": "Server is in read-only mode"}

    error = _validate_model(model)
    if error:
        return {"error": error}

    if not isinstance(values, dict):
        return {"error": f"values must be a dict, got {type(values).__name__}"}
    if not values:
        return {"error": "values cannot be empty"}

    try:
        conn = OdooConnection()
        record_id = conn.execute(model, "create", [values])
        return {"id": record_id}
    except xmlrpc.client.Fault as e:
        return {"error": f"Odoo error: {e.faultString}"}
    except ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except PermissionError as e:
        return {"error": f"Permission error: {e}"}


def update_record(model, record_id, values):
    if READ_ONLY_MODE:
        return {"error": "Server is in read-only mode"}

    error = _validate_model(model)
    if error:
        return {"error": error}

    if isinstance(record_id, bool) or not isinstance(record_id, int):
        return {"error": f"record_id must be a positive integer, got {record_id!r}"}
    if record_id <= 0:
        return {"error": f"record_id must be a positive integer, got {record_id}"}

    if not isinstance(values, dict):
        return {"error": f"values must be a dict, got {type(values).__name__}"}
    if not values:
        return {"error": "values cannot be empty"}

    try:
        conn = OdooConnection()
        result = conn.execute(model, "write", [[record_id], values])
        if not result:
            return {
                "error": f"Record with id {record_id} not found or could not be updated"
            }
        return {"success": True, "id": record_id}
    except xmlrpc.client.Fault as e:
        return {"error": f"Odoo error: {e.faultString}"}
    except ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except PermissionError as e:
        return {"error": f"Permission error: {e}"}
