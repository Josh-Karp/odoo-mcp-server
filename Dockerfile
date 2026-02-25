FROM python:3.11-slim

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# Switch to non-root user
USER appuser

# Environment variables (no secrets baked in — supply at runtime)
ENV ODOO_URL="" \
    ODOO_DB="" \
    ODOO_USERNAME="" \
    ODOO_PASSWORD="" \
    READ_ONLY_MODE="false"

# MCP servers typically communicate over stdio; expose 8000 for HTTP transports
EXPOSE 8000

CMD ["python", "src/mcp_server.py"]
