"""Tests for main API endpoints"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import json


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Badminton Tournament Scraper API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "this_week" in data["endpoints"]
        assert "two_days" in data["endpoints"]


class TestHealthCheck:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestThisWeekTournaments:
    """Tests for this-week-tournaments endpoint"""
    
    @patch('main.run_this_week')
    @patch('main.async_playwright')
    @patch('main.clear_directory')
    def test_this_week_tournaments_success(
        self, mock_clear_dir, mock_playwright, mock_run_this_week, client, temp_dir, sample_html
    ):
        """Test successful scraping of this week's tournaments"""
        # Setup mock
        mock_clear_dir.return_value = None
        mock_run_this_week.return_value = AsyncMock()
        
        # Create temporary test files
        test_folder = "this_week"
        os.makedirs(test_folder, exist_ok=True)
        with open(os.path.join(test_folder, "page_1.html"), "w", encoding="utf-8") as f:
            f.write(sample_html)
        
        try:
            # Mock playwright context manager
            mock_pw_instance = MagicMock()
            mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
            mock_playwright.return_value.__aexit__.return_value = None
            
            response = client.get("/this-week-tournaments")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "message" in data
            assert "timestamp" in data
            assert "files" in data
            
        finally:
            # Cleanup
            if os.path.exists(test_folder):
                import shutil
                shutil.rmtree(test_folder)
    
    @patch('main.run_this_week')
    @patch('main.async_playwright')
    @patch('main.clear_directory')
    def test_this_week_tournaments_failure(
        self, mock_clear_dir, mock_playwright, mock_run_this_week, client
    ):
        """Test handling of scraping failure"""
        # Setup mock to raise exception
        mock_clear_dir.return_value = None
        mock_run_this_week.side_effect = Exception("Scraping failed")
        
        # Mock playwright context manager
        mock_pw_instance = MagicMock()
        mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
        mock_playwright.return_value.__aexit__.return_value = None
        
        response = client.get("/this-week-tournaments")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Scraping failed" in data["detail"]


class TestTwoDaysMatches:
    """Tests for two-days-matches endpoint"""
    
    def test_two_days_matches_no_urls(self, client):
        """Test that endpoint requires at least one URL"""
        response = client.post(
            "/two-days-matches",
            json={"urls": []}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_two_days_matches_invalid_url(self, client):
        """Test handling of invalid URL"""
        response = client.post(
            "/two-days-matches",
            json={"urls": ["not-a-valid-url"]}
        )
        assert response.status_code == 422  # Pydantic validation error
    
    @patch('main.run_two_days')
    @patch('main.async_playwright')
    @patch('main.clear_directory')
    def test_two_days_matches_success(
        self, mock_clear_dir, mock_playwright, mock_run_two_days, 
        client, temp_dir, sample_html
    ):
        """Test successful scraping of two-days matches"""
        # Setup mocks
        mock_clear_dir.return_value = None
        mock_run_two_days.return_value = AsyncMock()
        
        # Create temporary test files
        test_folder = "two_days"
        os.makedirs(test_folder, exist_ok=True)
        
        tournament_name = "test-tournament-2025"
        tournament_url = f"https://bwfworldtour.bwfbadminton.com/tournament/1234/{tournament_name}/results"
        with open(os.path.join(test_folder, f"{tournament_name}_today.html"), "w", encoding="utf-8") as f:
            f.write(sample_html)
        with open(os.path.join(test_folder, f"{tournament_name}_tomorrow.html"), "w", encoding="utf-8") as f:
            f.write(sample_html)
        with open(os.path.join(test_folder, f"{tournament_name}_round_info.json"), "w", encoding="utf-8") as f:
            json.dump({
                "tournament_url": tournament_url,
                "league_id": "1234",
                "league_name": "Tournament",
                "level": "BWF Tour Super 100",
                "age_category": "Adults",
                "mode_max_round": {"MS": "R32", "WS": "R16"}
            }, f)
        
        try:
            # Mock playwright context manager
            mock_pw_instance = MagicMock()
            mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
            mock_playwright.return_value.__aexit__.return_value = None
            
            response = client.post(
                "/two-days-matches",
                json={
                    "urls": [f"https://bwfworldtour.bwfbadminton.com/tournament/1234/{tournament_name}/results"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "tournaments" in data
            assert len(data["tournaments"]) > 0
            
            # Check tournament data structure
            tournament = data["tournaments"][0]
            assert "league_id" in tournament
            assert "league_name" in tournament
            assert "today_html" in tournament
            assert "tomorrow_html" in tournament
            
        finally:
            # Cleanup
            if os.path.exists(test_folder):
                import shutil
                shutil.rmtree(test_folder)
    
    @patch('main.run_two_days')
    @patch('main.async_playwright')
    @patch('main.clear_directory')
    def test_two_days_matches_failure(
        self, mock_clear_dir, mock_playwright, mock_run_two_days, client
    ):
        """Test handling of scraping failure"""
        # Setup mock to raise exception
        mock_clear_dir.return_value = None
        mock_run_two_days.side_effect = Exception("Network error")
        
        # Mock playwright context manager
        mock_pw_instance = MagicMock()
        mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
        mock_playwright.return_value.__aexit__.return_value = None
        
        response = client.post(
            "/two-days-matches",
            json={
                "urls": ["https://bwfworldtour.bwfbadminton.com/tournament/9999/test-tournament-2025/results"]
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

