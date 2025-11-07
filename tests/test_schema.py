"""Tests for Pydantic schemas"""

import pytest
from pydantic import ValidationError
from schema import TournamentRequest, TournamentData, ScrapeResponse, TwoDaysResponse


class TestTournamentRequest:
    """Tests for TournamentRequest schema"""
    
    def test_valid_tournament_request(self):
        """Test valid tournament request"""
        data = {
            "urls": ["https://bwf.tournamentsoftware.com/sport/tournament?id=test-2025"]
        }
        request = TournamentRequest(**data)
        assert len(request.urls) == 1
        assert request.output_dir == "two_days"  # Default value
    
    def test_tournament_request_with_output_dir(self):
        """Test tournament request with custom output directory"""
        data = {
            "urls": ["https://bwf.tournamentsoftware.com/sport/tournament?id=test-2025"],
            "output_dir": "custom_dir"
        }
        request = TournamentRequest(**data)
        assert request.output_dir == "custom_dir"
    
    def test_invalid_url(self):
        """Test that invalid URL raises validation error"""
        data = {
            "urls": ["not-a-valid-url"]
        }
        with pytest.raises(ValidationError):
            TournamentRequest(**data)
    
    def test_empty_urls_list(self):
        """Test that empty URL list is accepted by schema (validation happens in endpoint)"""
        data = {
            "urls": []
        }
        request = TournamentRequest(**data)
        assert len(request.urls) == 0


class TestTournamentData:
    """Tests for TournamentData schema"""
    
    def test_valid_tournament_data(self):
        """Test valid tournament data"""
        data = {
            "tournament_url": "https://bwf.tournamentsoftware.com/sport/tournament?id=test-2025",
            "league_id": "test-2025",
            "league_name": "Test Tournament",
            "level": "BWF Tour Super 100",
            "age_category": "Adults",
            "mode_max_round": {"MS": "R32", "WS": "R16"},
            "today_html": "<html>Today</html>",
            "tomorrow_html": "<html>Tomorrow</html>"
        }
        tournament = TournamentData(**data)
        assert tournament.league_id == "test-2025"
        assert tournament.league_name == "Test Tournament"
        assert tournament.mode_max_round == {"MS": "R32", "WS": "R16"}
        assert tournament.today_html == "<html>Today</html>"
    
    def test_tournament_data_with_none_values(self):
        """Test tournament data with optional None values"""
        data = {
            "tournament_url": "https://bwf.tournamentsoftware.com/sport/tournament?id=test",
            "league_id": "test",
            "league_name": "Test",
            "level": "Test Level",
            "age_category": "Adults"
        }
        tournament = TournamentData(**data)
        assert tournament.mode_max_round is None
        assert tournament.today_html is None
        assert tournament.tomorrow_html is None
    
    def test_tournament_data_missing_required_fields(self):
        """Test that missing required fields raises validation error"""
        data = {
            "league_name": "test"
        }
        with pytest.raises(ValidationError):
            TournamentData(**data)


class TestScrapeResponse:
    """Tests for ScrapeResponse schema"""
    
    def test_valid_scrape_response(self):
        """Test valid scrape response"""
        data = {
            "status": "success",
            "message": "Scraping completed",
            "timestamp": "2025-10-09T12:00:00",
            "output_dir": "this_week",
            "files": {"page_1.html": "<html>Content</html>"}
        }
        response = ScrapeResponse(**data)
        assert response.status == "success"
        assert "page_1.html" in response.files
    
    def test_scrape_response_minimal(self):
        """Test scrape response with only required fields"""
        data = {
            "status": "failed",
            "message": "Error occurred",
            "timestamp": "2025-10-09T12:00:00"
        }
        response = ScrapeResponse(**data)
        assert response.status == "failed"
        assert response.output_dir is None
        assert response.files is None


class TestTwoDaysResponse:
    """Tests for TwoDaysResponse schema"""
    
    def test_valid_two_days_response(self):
        """Test valid two days response"""
        data = {
            "status": "success",
            "message": "Scraping completed",
            "tournaments": [
                {
                    "tournament_url": "https://bwf.tournamentsoftware.com/sport/tournament?id=test",
                    "league_id": "test",
                    "league_name": "Test Tournament",
                    "level": "BWF Tour Super 100",
                    "age_category": "Adults",
                    "mode_max_round": {"MS": "R32", "WS": "R16"},
                    "today_html": "<html>Today</html>",
                    "tomorrow_html": "<html>Tomorrow</html>"
                }
            ]
        }
        response = TwoDaysResponse(**data)
        assert response.status == "success"
        assert len(response.tournaments) == 1
        assert response.tournaments[0].league_id == "test"
        assert response.tournaments[0].league_name == "Test Tournament"
    
    def test_two_days_response_empty_tournaments(self):
        """Test two days response with empty tournaments list"""
        data = {
            "status": "success",
            "message": "No tournaments found",
            "tournaments": []
        }
        response = TwoDaysResponse(**data)
        assert len(response.tournaments) == 0
    
    def test_two_days_response_missing_required_fields(self):
        """Test that missing required fields raises validation error"""
        data = {
            "status": "success",
            "message": "Test"
        }
        with pytest.raises(ValidationError):
            TwoDaysResponse(**data)

