# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data ahead of time (no internet at runtime)
RUN python -m nltk.downloader punkt

# Default command to run the script
CMD ["python", "main.py"]
