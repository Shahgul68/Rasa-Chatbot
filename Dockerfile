# Use Python 3.7.7 slim base image
FROM python:3.7.7-slim-stretch

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    jq \
    libgomp1 \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy Rasa project files
COPY . .

# Copy only necessary files
COPY config.yml .
COPY domain.yml .
COPY credentials.yml .
COPY endpoints.yml .
COPY data/ ./data/
COPY actions/ ./actions/

# Expose ports
EXPOSE 5005

# Command to run the Rasa server
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--debug"]