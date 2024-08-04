# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Set an environment variable for the port
ENV PORT 1234

# Expose the port that Gunicorn will run on
EXPOSE $PORT

# As an example here we're running the web service with one worker on uvicorn.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --loop asyncio
