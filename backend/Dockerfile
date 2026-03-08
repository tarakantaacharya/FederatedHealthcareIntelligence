FROM python:3.10

WORKDIR /app

# Install only minimal build-essential dependencies (git for version control)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create storage directories
RUN mkdir -p storage/datasets storage/models

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
