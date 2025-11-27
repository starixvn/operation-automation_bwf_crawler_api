# BWF Tournament Scraper API

A FastAPI-based web scraper for extracting Badminton World Federation (BWF) tournament schedules. This service provides RESTful APIs to scrape tournament listings and match schedules from BWF websites using Playwright browser automation.

## Features

- **Tournament List** - Get current week's tournament list
- **Date Matches** - Scrape matches for a specific tournament on a specific date
- **Draw Data** - Get maximum rounds for each mode (MS, WS, MD, WD, XD) for tournaments
- **Match Info** - Map match information with tournament details
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
GET /get-tournament-list
```

Gets the current week's tournament list from BWF calendar.

**Response:**
```json
{
  "status": "success",
  "message": "Successfully got tournament list",
  "tournaments": [
    {
      "tmt_id": 5287,
      "tmt_code": "CLASH_OF_CLANS_ARCTIC_OPEN_2025",
      "tmt_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
      "tmt_name": "Clash of Clans Arctic Open 2025",
      "tmt_level": "World Tour Super 750"
    }
  ]
}
```

#### Get Day Matches

```bash
POST /day-matches
```

Scrapes matches for a specific tournament on a specific date.

**Request Body:**
```json
{
  "tmt_code": "CLASH_OF_CLANS_ARCTIC_OPEN_2025",
  "url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
  "date": "2025-11-11"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully scraped the specified date matches, total 20 matches.",
  "matches": [
    {
      "league_id": 5287,
      "match_id": 12345,
      "player_home_1_id": 1001,
      "player_home_1_country": "CHN",
      "player_home_1_name": "Player A",
      "player_home_2_id": null,
      "player_home_2_country": "",
      "player_home_2_name": "",
      "player_away_1_id": 1002,
      "player_away_1_country": "JPN",
      "player_away_1_name": "Player B",
      "player_away_2_id": null,
      "player_away_2_country": "",
      "player_away_2_name": "",
      "mode": "MS",
      "round": "R32",
      "court": "Court 1",
      "kickoff_time": "2025-11-11T10:00:00"
    }
  ]
}
```

**Filtering Rules:**

The following tournament types are automatically excluded:
- Para-badminton tournaments (level contains "para")
- Empty or null level
- "International Series"
- "International Challenge"
- "Junior International Series"
- "Junior Tournament"

#### Get Draw Data

```bash
POST /get-draw-data
```

Gets tournament draw data.

**Request Body:**
```json
{
  "tournament_id": "5287",
  "tournament_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
  "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully got draw data in 5.23s",
  "tournament_id": "5287",
  "draw_data": {
    "MS": {...},
    "WS": {...},
    "MD": {...},
    "WD": {...},
    "XD": {...}
  }
}
```

#### Match Info

```bash
POST /match-info
```

Maps match information with tournament details.

**Request Body:**
```json
{
  "tmt_id": 5287,
  "tmt_name": "Clash of Clans Arctic Open 2025",
  "tmt_level": "World Tour Super 750",
  "draw_data": {...},
  "matches_data": [...]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully mapped match info",
  "matches_data": [
    {
      "league_id": 5287,
      "match_id": 12345,
      "player_home_1_id": 1001,
      "player_home_1_country": "CHN",
      "player_home_1_name": "Player A",
      "player_away_1_id": 1002,
      "player_away_1_country": "JPN",
      "player_away_1_name": "Player B",
      "mode": "MS",
      "round": "R32",
      "court": "Court 1",
      "kickoff_time": "2025-11-11T10:00:00",
      "league_name": "Clash of Clans Arctic Open 2025",
      "level": "World Tour Super 750",
      "current_round": "R32",
      "max_round": "R32"
    }
  ]
}
```


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

# Get tournament list
response = requests.get(f"{BASE_URL}/get-tournament-list")
data = response.json()
print(f"Status: {data['status']}")
print(f"Tournaments: {len(data['tournaments'])}")

# Get max rounds for a tournament
payload = {
    "tournament_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex"
}
response = requests.post(f"{BASE_URL}/get-max-rounds", json=payload)
data = response.json()
print(f"Max Rounds: {data['mode_max_round']}")

# Get matches for a specific date
payload = {
    "tmt_code": "CLASH_OF_CLANS_ARCTIC_OPEN_2025",
    "url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "date": "2025-11-11"
}
response = requests.post(f"{BASE_URL}/day-matches", json=payload)
data = response.json()
print(f"Matches: {len(data['matches'])}")

# Get draw data
payload = {
    "tournament_id": "5287",
    "tournament_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex"
}
response = requests.post(f"{BASE_URL}/get-draw-data", json=payload)
data = response.json()
print(f"Draw Data: {data['status']}")
```

### cURL Examples

```bash
# Note: Use port 8080 for Docker Compose, port 8000 for local development
# Replace localhost with your server's IP address for network access

# Health check (Docker Compose)
curl http://localhost:8080/health

# Health check (Local Development)
# curl http://localhost:8000/health

# Get tournament list (Docker Compose)
curl http://localhost:8080/get-tournament-list

# Get max rounds (Docker Compose)
curl -X POST "http://localhost:8080/get-max-rounds" \
  -H "Content-Type: application/json" \
  -d '{
    "tournament_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex"
  }'

# Get day matches (Docker Compose)
curl -X POST "http://localhost:8080/day-matches" \
  -H "Content-Type: application/json" \
  -d '{
    "tmt_code": "CLASH_OF_CLANS_ARCTIC_OPEN_2025",
    "url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "date": "2025-11-11"
  }'

# Get draw data (Docker Compose)
curl -X POST "http://localhost:8080/get-draw-data" \
  -H "Content-Type: application/json" \
  -d '{
    "tournament_id": "5287",
    "tournament_url": "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "tournament_name": "clash-of-clans-arctic-open-2025-powered-by-yonex"
  }'
```

## Output Files

The API may save cached data to local directories (also mounted as Docker volumes):

### Max Rounds Cache
- **Directory**: `mode_max_round/`
- **Files**: JSON files containing cached max round data for tournaments
- **Retention**: Files older than 8 days are automatically cleaned up

### Draw Data Cache
- **Directory**: Various cache directories
- **Files**: JSON files containing cached draw data
- **Retention**: Files older than 8 days are automatically cleaned up

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

#### Tournament List Item
```json
{
  "tmt_id": "integer",
  "tmt_code": "string",
  "tmt_url": "string",
  "tmt_name": "string",
  "tmt_level": "string"
}
```

#### Day Matches Request
```json
{
  "tmt_code": "string (required)",
  "url": "string (required)",
  "date": "string (required, format: YYYY-MM-DD)"
}
```

#### Match Data
```json
{
  "league_id": "integer",
  "match_id": "integer",
  "player_home_1_id": "integer or null",
  "player_home_1_country": "string",
  "player_home_1_name": "string",
  "player_home_2_id": "integer or null",
  "player_home_2_country": "string",
  "player_home_2_name": "string",
  "player_away_1_id": "integer or null",
  "player_away_1_country": "string",
  "player_away_1_name": "string",
  "player_away_2_id": "integer or null",
  "player_away_2_country": "string",
  "player_away_2_name": "string",
  "mode": "string (MS/WS/MD/WD/XD)",
  "round": "string",
  "court": "string",
  "kickoff_time": "string (ISO format)"
}
```

#### Draw Data Request
```json
{
  "tournament_id": "string (required)",
  "tournament_url": "string (required)",
  "tournament_name": "string (required)"
}
```

#### Match Info Request
```json
{
  "tmt_id": "integer (required)",
  "tmt_name": "string (required)",
  "tmt_level": "string (required)",
  "draw_data": "object (required)",
  "matches_data": "array (required)"
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
python script/get-tournament-list.py

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
