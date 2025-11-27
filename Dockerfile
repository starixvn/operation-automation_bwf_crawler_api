# FROM python:3.12-slim
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

COPY requirements.txt .
RUN pip install -r requirements.txt

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Create output and logs directories
RUN mkdir -p /app/two_days /app/this_week /app/logs

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--timeout-keep-alive", "600"]
