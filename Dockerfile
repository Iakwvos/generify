# Use Python 3.11 slim image for a smaller footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PORT=8000

# Expose port (using PORT environment variable)
EXPOSE ${PORT}

# Create a shell script to start gunicorn
RUN echo '#!/bin/bash\ngunicorn --bind 0.0.0.0:${PORT} app:app' > start.sh && chmod +x start.sh

# Run the start script
CMD ["./start.sh"] 