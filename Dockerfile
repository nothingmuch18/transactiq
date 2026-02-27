FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ ./backend/

# Run Uvicorn server, using the PORT environment variable provided by Railway
CMD sh -c "cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
