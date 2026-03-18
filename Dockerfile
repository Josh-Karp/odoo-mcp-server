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

# Only READ_ONLY_MODE has a safe default; all Odoo connection variables
# must be supplied at runtime (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD).
ENV READ_ONLY_MODE="false"

CMD ["python", "src/mcp_server.py"]
