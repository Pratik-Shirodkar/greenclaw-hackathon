FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (App Runner uses 8000 by default)
EXPOSE 8000

# Start the server (bot runs as background thread inside server.py)
CMD ["python", "server.py"]
