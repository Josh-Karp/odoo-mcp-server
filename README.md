# odoo-mcp-server

## Available Tools

### `search_records`

Search for records in an Odoo model.

### `create_record`

Create a new record in an Odoo model.

### `update_record`

Update an existing record in an Odoo model.

### `get_allowed_models`

Returns the list of Odoo models permitted by this MCP server. Takes no parameters.

**Example response:**
```json
{
  "models": ["res.partner", "res.users", "sale.order", "..."],
  "count": 17
}
```
