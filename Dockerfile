FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directories for static files and templates if not already present
RUN mkdir -p static/css templates

# Expose port for the API
EXPOSE 8000

# Command to run the API service
CMD ["uvicorn", "src.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 