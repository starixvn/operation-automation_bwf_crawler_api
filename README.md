# BWF Tournament Scraper API

A FastAPI-based web scraper for extracting Badminton World Federation (BWF) tournament schedules. This service provides RESTful APIs to scrape tournament listings and match schedules from BWF websites using Playwright browser automation.

## Features

- **This Week's Tournaments** - Scrape paginated list of current week tournaments
- **Two-Day Schedules** - Extract today and tomorrow match schedules for specific tournaments
- **Docker Support** - Containerized deployment with Docker Compose
- **Anti-Detection** - Browser automation with webdriver concealment
- **Dual-Site Support** - Handles both regular BWF and BWF World Tour website formats
- **Automatic Filtering** - Excludes para-badminton and lower-tier tournaments

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start the service
docker compose up -d --build

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

The API will be available at:
- **Local**: `http://localhost:8080`
- **Network**: `http://<SERVER_IP>:8080` (replace `<SERVER_IP>` with your server's IP address)
- **Example**: `http://192.168.1.100:8080` or `http://your-domain.com:8080`

> **Note**: Docker Compose maps container port 8000 to host port 8080. If you need to use port 8000, modify the `ports` section in `docker-compose.yml` to `"8000:8000"`.

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start the API server
python main.py
# or
uvicorn main:app --reload
```

The API will be available at:
- **Local**: `http://localhost:8000`
- **Network**: `http://<SERVER_IP>:8000`

> **Note**: Local development uses port 8000 by default.

## API Documentation

Once running, access the interactive API documentation:

### When using Docker Compose:
- **Swagger UI**: 
  - Local: http://localhost:8080/docs
  - Network: http://`<SERVER_IP>`:8080/docs
- **ReDoc**: 
  - Local: http://localhost:8080/redoc
  - Network: http://`<SERVER_IP>`:8080/redoc

### When using Local Development:
- **Swagger UI**: 
  - Local: http://localhost:8000/docs
  - Network: http://`<SERVER_IP>`:8000/docs
- **ReDoc**: 
  - Local: http://localhost:8000/redoc
  - Network: http://`<SERVER_IP>`:8000/redoc

Replace `<SERVER_IP>` with your server's actual IP address (e.g., `192.168.1.100` or `your-domain.com`)

### Endpoints

#### Health Check

```bash
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-11T10:30:00.123456"
}
```

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
  "timestamp": "2025-11-11T10:30:00.123456",
  "output_dir": "this_week",
  "files": {
    "page_1.html": "<html>...</html>",
    "page_2.html": "<html>...</html>"
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
  "tournaments": [
    {
      "url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
      "level": "World Tour Super 750",
      "country": "Finland",
      "city": "Vantaa",
      "IANA_timezone": "Europe/Helsinki"
    }
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
      "league_id": "5287",
      "league_name": "Clash of Clans Arctic Open 2025",
      "max_round": "R32",
      "today_html": "<html>...</html>",
      "tomorrow_html": "<html>...</html>"
    }
  ]
}
```

**Filtering Rules:**

The following tournament types are automatically excluded:
- Para-badminton tournaments (level contains "para")


## Usage Examples

### Python Example

```python
import requests

# For Docker Compose deployment (default port 8080)
BASE_URL = "http://localhost:8080"
# BASE_URL = "http://192.168.1.100:8080"  # Network access
# BASE_URL = "http://your-domain.com:8080"

# For Local Development (default port 8000)
# BASE_URL = "http://localhost:8000"
# BASE_URL = "http://192.168.1.100:8000"  # Network access

# Get this week's tournaments
response = requests.get(f"{BASE_URL}/this-week-tournaments")
data = response.json()
print(f"Status: {data['status']}")
print(f"Files: {len(data['files'])}")

# Get two-day schedules
payload = {
    "tournaments": [
        {
            "url": "https://bwfbadminton.com/tournament/5263/yonex-sunrise-bwf-world-junior-mixed-team-championships-2025",
            "level": "World Junior Championships",
            "country": "China",
            "city": "Nanjing",
            "IANA_timezone": "Asia/Shanghai"
        }
    ],
    "output_dir": "two_days"
}
response = requests.post(f"{BASE_URL}/two-days-matches", json=payload)
data = response.json()

for tournament in data["tournaments"]:
    print(f"Tournament: {tournament['league_name']}")
    print(f"Max Round: {tournament['max_round']}")
```

### cURL Examples

```bash
# Note: Use port 8080 for Docker Compose, port 8000 for local development
# Replace localhost with your server's IP address for network access

# Health check (Docker Compose)
curl http://localhost:8080/health

# Health check (Local Development)
# curl http://localhost:8000/health

# Get this week's tournaments (Docker Compose)
curl http://localhost:8080/this-week-tournaments

# Get two-day schedules (Docker Compose)
curl -X POST "http://localhost:8080/two-days-matches" \
  -H "Content-Type: application/json" \
  -d '{
    "tournaments": [
      {
        "url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
        "level": "World Tour Super 750",
        "country": "Finland",
        "city": "Vantaa",
        "IANA_timezone": "Europe/Helsinki"
      }
    ],
    "output_dir": "two_days"
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
├── BWF_cookies.json                       # Browser cookies for BWF sites
├── schema/                                # Pydantic models
│   ├── __init__.py
│   └── schema.py                          # API request/response models
├── script/                                # Scraper scripts
│   ├── __init__.py
│   ├── get_this_week_tournament_html.py  # Weekly tournament scraper
│   ├── get_two_days_match_html.py        # Two-day schedule scraper
│   ├── tournament_loader.py              # Tournament data loader
│   └── tournament_filter.py              # Tournament filtering logic
├── utils/                                 # Utility functions
│   ├── __init__.py
│   ├── file_utils.py                     # File operations
│   └── logger.py                         # Logging configuration
├── tests/                                 # Test suite
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_schema.py
│   └── test_utils.py
├── logs/                                  # Application logs
│   └── api.log                           # Main log file
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
- Cookie-based authentication for BWF sites
- Automatic popup/dialog dismissal
- Waits for dynamic content to load before extraction

### Tournament Filtering

The API automatically filters out unwanted tournaments based on the `level` field:

**Excluded Levels:**
- Empty or null level
- Contains "para" (para-badminton)
- "International Series"
- "International Challenge"
- "Junior International Series"
- "Junior Tournament"

**Included Levels:**
- World Tour Super Series (100, 300, 500, 750, 1000)
- BWF World Championships
- Continental Championships
- Other major tournaments

### Data Schema

#### Tournament Input
```json
{
  "url": "string (required)",
  "level": "string (required)",
  "country": "string (optional)",
  "city": "string (optional)",
  "IANA_timezone": "string (optional)"
}
```

#### Tournament Output
```json
{
  "tournament_url": "string",
  "tournament_name": "string",
  "league_id": "string",
  "league_name": "string",
  "max_round": "string",
  "today_html": "string (HTML content)",
  "tomorrow_html": "string or null (HTML content)"
}
```

## Logging

The application uses structured logging with daily rotation to track operations and errors.

### Log Files

- **Location**: `logs/api.log`
- **Rotation**: Daily at midnight
- **Retention**: 7 days (one week)
- **Format**: Archived logs are named `api.log.YYYY-MM-DD`

### View Logs

```bash
# View latest logs
tail -f logs/api.log

# View logs in Docker
docker compose logs -f badminton-api

# View logs inside container
docker compose exec badminton-api tail -f /app/logs/api.log

# Search for errors
grep "ERROR" logs/api.log

# View specific day's logs
cat logs/api.log.2025-11-09
```

### What Gets Logged

**✅ Logged:**
- API startup/shutdown events
- Scraping start and completion times
- Number of files/tournaments scraped
- File sizes (not content)
- Processing duration
- Tournament names and URLs
- Filtering statistics
- Error messages with stack traces

**❌ NOT Logged:**
- HTML content
- Actual scraped data
- Health check requests (DEBUG level only)

### Log Levels

- **INFO**: Normal operations (API start, scraping progress, file metrics)
- **WARNING**: Non-critical issues (empty URLs, missing data)
- **ERROR**: Errors with stack traces (scraping failures)
- **DEBUG**: Detailed information (health checks, verbose debugging)

### Log Example

```
============================================================
2025-11-11 10:00:00 - main - INFO - Starting this week tournaments scraping
2025-11-11 10:00:01 - main - INFO - Cleared output directory: this_week
2025-11-11 10:00:02 - main - INFO - Launching browser for scraping
2025-11-11 10:00:10 - main - INFO - Scraped file: page_1.html (size: 12,345 bytes)
2025-11-11 10:00:12 - main - INFO - Successfully scraped 3 tournament files in 12.34s
============================================================
```

For more details, see [logs/README.md](logs/README.md)

## Troubleshooting

### Port Already in Use

**For Docker Compose (default port 8080):**

Check if port 8080 is occupied:
```bash
lsof -i :8080
```

If port 8080 is in use, change the host port in `docker-compose.yml`:
```yaml
ports:
  - "9000:8000"  # Map to port 9000 instead
```

**For Local Development (default port 8000):**

Check if port 8000 is occupied:
```bash
lsof -i :8000
```

Change the port when starting the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 9000
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

### Cookie Authentication Issues

**Important**: BWF cookies need to be updated **monthly** to maintain authentication.

- **Current Update**: November 10, 2025
- **Next Update Due**: Before December 09, 2025

If you encounter authentication errors or the cookies have expired, update the `BWF_cookies.json` file with valid cookies from your browser:

1. Open BWF website in your browser (https://bwfbadminton.com/)
2. Open Developer Tools (F12)
3. Go to **Application** > **Cookies** > https://bwfbadminton.com
4. Copy the following **3 cookies** and update them in `BWF_cookies.json`:
   - `CookieScriptConsent` - Cookie consent tracking
   - `laravel_session` - Session authentication
   - `cf_clearance` - Cloudflare clearance token
5. Update the corresponding values in `BWF_cookies.json` following this format:

```json
[
  {
    "name": "CookieScriptConsent",
    "value": "YOUR_COOKIE_VALUE_HERE",
    "domain": ".bwfbadminton.com",
    "path": "/"
  },
  {
    "name": "laravel_session",
    "value": "YOUR_COOKIE_VALUE_HERE",
    "domain": ".bwfbadminton.com",
    "path": "/"
  },
  {
    "name": "cf_clearance",
    "value": "YOUR_COOKIE_VALUE_HERE",
    "domain": ".bwfbadminton.com",
    "path": "/"
  }
]
```

6. Restart the API service: `docker compose restart` or restart the local server

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
3. **New schema** - Add Pydantic models in `schema/schema.py`
4. **New filter** - Add filter logic in `script/tournament_filter.py`

## Limitations

- Only supports BWF official websites
- Para-badminton tournaments are automatically skipped
- Requires stable internet connection for scraping
- Scraping operations are synchronous (blocking)
- Cookie authentication may expire and require manual update

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Playwright**: Browser automation library
- **Pydantic**: Data validation using Python type annotations
- **Unidecode**: Unicode text to ASCII transliteration

For complete list, see [requirements.txt](requirements.txt)

## License

This project is for educational and research purposes only. Please respect BWF's terms of service and robots.txt policies.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- [BWF (Badminton World Federation)](https://bwfbadminton.com/) for tournament data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Playwright](https://playwright.dev/) for browser automation
