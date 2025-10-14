FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Expose port
EXPOSE 6004

# Set environment variables
ENV SURYA_PORT=6004
ENV SURYA_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "main.py"]
