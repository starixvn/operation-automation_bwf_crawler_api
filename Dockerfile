FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install Playwright
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install --with-deps

# Copy application files
COPY api.py .
COPY get_two_days_match_html.py .
COPY get_this_week_tournament_html.py .

# Create output directories
RUN mkdir -p /app/two_days /app/this_week

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "600"]
