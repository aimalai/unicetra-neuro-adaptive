# Use an official lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by the 'unstructured' library
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker's caching
COPY requirements.txt .

# Install the necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code into the container
COPY . .

# Expose the port FastAPI runs on (default is usually 8000)
EXPOSE 8000

# Command to run the FastAPI server
# Note: Update "main:app" if your primary file is named something else (e.g., "api:app")
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]