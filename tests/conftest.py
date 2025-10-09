"""Pytest configuration and fixtures"""

import pytest
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_html():
    """Sample HTML content for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Tournament</title></head>
    <body>
        <h1>Tournament Schedule</h1>
        <div class="match">Test Match</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_tournament_data():
    """Sample tournament data for testing"""
    return {
        "tournament_name": "test-tournament-2025",
        "tournament_url": "https://bwf.tournamentsoftware.com/sport/tournament?id=test-tournament-2025",
        "max_round": "R32",
        "today_html": "<html><body>Today's matches</body></html>",
        "tomorrow_html": "<html><body>Tomorrow's matches</body></html>"
    }

