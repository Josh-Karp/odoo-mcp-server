# odoo-mcp-server

A lightweight **MCP (Model Context Protocol) server** that connects AI assistants to an external **Odoo v14** instance via the Odoo XML-RPC API.

---

## Overview

This server exposes four MCP tools — `search_records`, `create_record`, `update_record`, and `get_allowed_models` — allowing MCP-compatible clients (such as Claude Desktop) to query and modify data in a live Odoo instance. It includes a model allow-list, optional read-only mode, and input validation to keep interactions safe and auditable.

---

## Prerequisites

- Python 3.11+
- Docker (optional, for containerised deployment)
- An external Odoo v14 instance with XML-RPC enabled

---

## Configuration

All configuration is provided through environment variables:

| Variable         | Description                                      | Required |
|------------------|--------------------------------------------------|----------|
| `ODOO_URL`       | Base URL of the Odoo instance (e.g. `https://myodoo.example.com`) | Yes |
| `ODOO_DB`        | Odoo database name                               | Yes |
| `ODOO_USERNAME`  | Odoo username (email)                            | Yes |
| `ODOO_PASSWORD`  | Odoo password or API key                         | Yes |
| `READ_ONLY_MODE` | Set to `true` to disable write operations (default: `false`) | No |

Copy `.env.example` to `.env` and fill in your values.

---

## Running with Docker

```bash
# Build the image
docker build -t odoo-mcp-server .

# Run the container (stdio transport — used by MCP clients directly)
docker run --rm \
  -e ODOO_URL=https://your-odoo.example.com \
  -e ODOO_DB=your_database \
  -e ODOO_USERNAME=your@email.com \
  -e ODOO_PASSWORD=your_password \
  odoo-mcp-server
```

Or using an env file:

```bash
docker run --rm --env-file .env odoo-mcp-server
```

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ODOO_URL=https://your-odoo.example.com
export ODOO_DB=your_database
export ODOO_USERNAME=your@email.com
export ODOO_PASSWORD=your_password

# Start the server
python src/mcp_server.py
```

---

## Available Tools

### `search_records`

Search for records in Odoo using domain filters.

| Parameter | Type  | Default | Description                                      |
|-----------|-------|---------|--------------------------------------------------|
| `model`   | str   | —       | Odoo model name (must be in the allow-list)      |
| `domain`  | list  | `[]`    | Odoo domain filter (e.g. `[["name","=","Test"]]`)|
| `fields`  | list  | `[]`    | Fields to return (`[]` returns all fields)       |
| `limit`   | int   | `100`   | Max records to return (max 500)                  |
| `offset`  | int   | `0`     | Pagination offset                                |

### `create_record`

Create a new record in Odoo.

| Parameter | Type  | Description                                      |
|-----------|-------|--------------------------------------------------|
| `model`   | str   | Odoo model name (must be in the allow-list)      |
| `values`  | dict  | Field values for the new record                  |

### `update_record`

Update an existing record in Odoo by ID.

| Parameter   | Type  | Description                                      |
|-------------|-------|--------------------------------------------------|
| `model`     | str   | Odoo model name (must be in the allow-list)      |
| `record_id` | int   | ID of the record to update                       |
| `values`    | dict  | Field values to update                           |

### `get_allowed_models`

Returns the list of Odoo models permitted by this MCP server. Takes no parameters.

| Parameter | Type | Description |
|---|---|---|
| *(none)* | — | This tool takes no parameters |

**Example response:**
```json
{
  "models": ["res.partner", "res.users", "sale.order", "..."],
  "count": 17
}
```

---

## Safeguards

### Model Allow-List

Only the models listed in **Allowed Models** below may be accessed. Any other model name is rejected with a clear error message.

### Read-Only Mode

Set `READ_ONLY_MODE=true` to disable `create_record` and `update_record`. Both tools will return an error when called in this mode.

### Input Validation

- `model` must be a non-empty string present in the allow-list.
- `values` must be a non-empty dict for create/update operations.
- `record_id` must be a positive integer for update operations.
- `limit` cannot exceed 500.
- Domain filters containing a top-level `|` (OR) with more than 5 conditions are rejected.

### Error Handling

Meaningful error messages are returned for:
- XML-RPC connection failures
- Authentication failures
- Invalid model or field names
- Record not found
- Permission errors from Odoo

---

## Allowed Models

```
res.partner
res.users
sale.order
sale.order.line
purchase.order
purchase.order.line
account.move
account.move.line
stock.picking
stock.move
product.product
product.template
mrp.production
project.project
project.task
hr.employee
crm.lead
```