# BWF Tournament Scraper API

A FastAPI-based web scraper for extracting Badminton World Federation (BWF) tournament schedules. This service provides RESTful APIs to scrape tournament listings and match schedules from BWF websites using Playwright browser automation.

## Features

- **This Week's Tournaments** - Scrape paginated list of current week tournaments
- **Two-Day Schedules** - Extract today and tomorrow match schedules for specific tournaments
- **Docker Support** - Containerized deployment with Docker Compose
- **HTML Compression** - Gzip + Base64 encoding to reduce response payload size
- **Anti-Detection** - Browser automation with webdriver concealment
- **Dual-Site Support** - Handles both regular BWF and BWF World Tour website formats

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

The API will be available at `http://localhost:8000`

### Option 2: Docker

```bash
# Build the image
docker build -t badminton-api .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/two_days:/app/two_days \
  -v $(pwd)/this_week:/app/this_week \
  --name badminton-api \
  badminton-api
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start the API server
python main.py
# or
uvicorn main:app --reload
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### Health Check

```bash
GET /health
```

Returns server health status.

#### Get This Week's Tournaments

```bash
GET /this-week-tournaments
```

Scrapes the current week's tournament list from BWF calendar.

**Response:**
```json
{
  "status": "success",
  "message": "Successfully scraped this week's tournaments, total 3 files",
  "timestamp": "2025-10-08T10:30:00.123456",
  "output_dir": "this_week",
  "files": {
    "page_1.html": {
      "compressed": true,
      "data": "H4sIAAAAAAAA..."
    }
  }
}
```

#### Get Two-Day Match Schedules

```bash
POST /two-days-matches
```

Scrapes today and tomorrow schedules for specified tournament URLs.

**Request Body:**
```json
{
  "urls": [
    "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/"
  ],
  "output_dir": "two_days"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully scraped today and tomorrow schedules for 1 tournaments",
  "tournaments": [
    {
      "tournament_url": "https://...",
      "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex",
      "max_round": "R32",
      "today_html": {
        "compressed": true,
        "data": "H4sIAAAAAAAA..."
      },
      "tomorrow_html": {
        "compressed": true,
        "data": "H4sIAAAAAAAA..."
      }
    }
  ]
}
```

## Usage Examples

### Python Example

```python
import requests
import gzip
import base64

BASE_URL = "http://localhost:8000"

# Get this week's tournaments
response = requests.get(f"{BASE_URL}/this-week-tournaments")
data = response.json()

if data["status"] == "success":
    # Decompress HTML
    for filename, content in data["files"].items():
        compressed_data = base64.b64decode(content["data"])
        html = gzip.decompress(compressed_data).decode('utf-8')
        print(f"{filename}: {len(html)} characters")

# Get two-day schedules
payload = {
    "urls": [
        "https://bwfbadminton.com/tournament/5263/yonex-sunrise-bwf-world-junior-mixed-team-championships-2025"
    ]
}
response = requests.post(f"{BASE_URL}/two-days-matches", json=payload)
data = response.json()

for tournament in data["tournaments"]:
    print(f"Tournament: {tournament['tournament_name']}")
    print(f"Max Round: {tournament['max_round']}")
```

### cURL Examples

```bash
# Get this week's tournaments
curl http://localhost:8000/this-week-tournaments

# Get two-day schedules
curl -X POST "http://localhost:8000/two-days-matches" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/"
    ]
  }'
```

## Output Files

The API saves scraped HTML to local directories (also mounted as Docker volumes):

### This Week's Tournaments
- **Directory**: `this_week/`
- **Files**: `page_1.html`, `page_2.html`, ...

### Two-Day Schedules
- **Directory**: `two_days/` (customizable via `output_dir` parameter)
- **Files**:
  - `{tournament_name}_today.html` - Today's schedule
  - `{tournament_name}_tomorrow.html` - Tomorrow's schedule
  - `{tournament_name}_round_info.json` - Tournament metadata

## Project Structure

```
bwf_crawler_api/
├── main.py                                # FastAPI application
├── requirements.txt                       # Python dependencies
├── Dockerfile                             # Docker image configuration
├── docker-compose.yml                     # Docker Compose setup
├── schema/                                # Pydantic models
│   ├── __init__.py
│   └── schema.py                          # API request/response models
├── script/                                # Scraper scripts
│   ├── __init__.py
│   ├── get_this_week_tournament_html.py  # Weekly tournament scraper
│   └── get_two_days_match_html.py        # Two-day schedule scraper
├── utils/                                 # Utility functions
│   ├── __init__.py
│   └── file_utils.py                     # File operations
├── this_week/                             # Output directory for weekly data
├── two_days/                              # Output directory for two-day data
├── .dockerignore                          # Docker build exclusions
├── .gitignore                             # Git exclusions
└── README.md                              # This file
```

## Technical Details

### Supported Websites

- **BWF Regular**: `https://bwfbadminton.com/tournament/...`
- **BWF World Tour**: `https://bwfworldtour.bwfbadminton.com/tournament/.../results/`

The scraper automatically detects the site type and uses the appropriate navigation strategy:
- **Regular sites**: Date navigation via tab clicks
- **World Tour sites**: Date navigation via URL modification (`/results/YYYY-MM-DD`)

### Browser Automation

- Uses Playwright with Chromium
- Headless mode with anti-detection measures
- Custom user agent to mimic regular browser
- Automatic popup/dialog dismissal
- Waits for dynamic content to load before extraction

### Data Compression

All HTML responses are compressed to reduce payload size:
1. HTML content is gzipped
2. Compressed data is base64-encoded
3. Response includes `{"compressed": true, "data": "..."}`

## Troubleshooting

### Port Already in Use

Check if port 8000 is occupied:
```bash
lsof -i :8000
```

Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Use 8080 instead
```

### Playwright Browser Issues

If running locally, ensure Chromium is installed:
```bash
playwright install chromium
```

For Docker, the browser is pre-installed in the image.

### Timeout Errors

The API has a 600-second timeout for long-running scrapes. If you encounter timeouts:
- Check your internet connection
- Verify the tournament URLs are accessible
- Check container logs: `docker compose logs -f`

## Development

### Running Tests

Run unit tests to verify functionality:

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run tests in Docker
docker compose run --rm badminton-api pytest
```

For detailed testing documentation, see [tests/README.md](tests/README.md)

### Running Standalone Scrapers

Test scrapers independently without the API:

```bash
# Test weekly tournament scraper
python script/get_this_week_tournament_html.py

# Test two-day schedule scraper
python script/get_two_days_match_html.py
```

### Adding New Features

The codebase is structured for easy extension:

1. **New scraper** - Create a new async function in the scraper modules
2. **New endpoint** - Add route handler in `main.py`:
   ```python
   @app.post("/api/your-endpoint")
   async def your_endpoint():
       # Your implementation
       pass
   ```

## Limitations

- Only supports BWF official websites
- Para-badminton tournaments are automatically skipped
- Requires stable internet connection for scraping
- Scraping operations are synchronous (blocking)

## License

This project is for educational and research purposes only. Please respect BWF's terms of service and robots.txt policies.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- [BWF (Badminton World Federation)](https://bwfbadminton.com/) for tournament data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Playwright](https://playwright.dev/) for browser automation
