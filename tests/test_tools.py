"""
Tests for API Tools - Unit tests for GitHub, Weather, and News tools
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from tools.github import GitHubTool
from tools.weather import WeatherTool
from tools.news import NewsTool
from tools.base import ToolResult, ToolStatus


class TestGitHubTool:
    """Test cases for GitHub Tool."""
    
    @pytest.fixture
    def github_tool(self):
        """Create GitHub tool for testing."""
        return GitHubTool()
    
    def test_get_capabilities(self, github_tool):
        """Test getting tool capabilities."""
        capabilities = github_tool.get_capabilities()
        assert len(capabilities) == 4
        
        capability_names = [cap.name for cap in capabilities]
        assert "search_repositories" in capability_names
        assert "get_repository" in capability_names
        assert "get_user_info" in capability_names
        assert "list_repository_commits" in capability_names
    
    def test_validate_parameters(self, github_tool):
        """Test parameter validation."""
        # Valid parameters
        is_valid, error = github_tool.validate_parameters("search_repositories", {
            "query": "language:python",
            "per_page": 10
        })
        assert is_valid is True
        assert error is None
        
        # Invalid per_page
        is_valid, error = github_tool.validate_parameters("search_repositories", {
            "query": "language:python",
            "per_page": 150  # Over limit
        })
        assert is_valid is False
        assert "per_page must be an integer between 1 and 100" in error
        
        # Missing required parameter
        is_valid, error = github_tool.validate_parameters("search_repositories", {})
        assert is_valid is False
        assert "Missing required parameter: query" in error
    
    @pytest.mark.asyncio
    async def test_search_repositories_success(self, github_tool):
        """Test successful repository search."""
        mock_response = {
            "items": [
                {
                    "name": "react",
                    "full_name": "facebook/react",
                    "owner": {"login": "facebook"},
                    "description": "A declarative JavaScript library",
                    "stargazers_count": 200000,
                    "forks_count": 40000,
                    "language": "JavaScript",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "created_at": "2013-01-01T00:00:00Z",
                    "html_url": "https://github.com/facebook/react",
                    "topics": ["javascript", "react", "library"]
                }
            ],
            "total_count": 1
        }
        
        with patch.object(github_tool, '_make_request', return_value=mock_response):
            result = await github_tool.execute("search_repositories", {
                "query": "react",
                "per_page": 10
            })
        
        assert result.status == ToolStatus.SUCCESS
        assert "repositories" in result.data
        assert len(result.data["repositories"]) == 1
        assert result.data["repositories"][0]["name"] == "react"
        assert result.data["total_count"] == 1
    
    @pytest.mark.asyncio
    async def test_search_repositories_error(self, github_tool):
        """Test repository search with error."""
        with patch.object(github_tool, '_make_request', side_effect=Exception("API Error")):
            result = await github_tool.execute("search_repositories", {
                "query": "react"
            })
        
        assert result.status == ToolStatus.ERROR
        assert "Repository search failed" in result.error
    
    def test_validate_api_key(self, github_tool):
        """Test API key validation."""
        # No key (should be valid for public endpoints)
        github_tool.token = None
        assert github_tool.validate_api_key() is False  # We require key for this tool
        
        # Invalid key format
        github_tool.token = "invalid_key"
        assert github_tool.validate_api_key() is False
        
        # Valid key format
        github_tool.token = "ghp_1234567890abcdef1234567890abcdef12345678"
        assert github_tool.validate_api_key() is True


class TestWeatherTool:
    """Test cases for Weather Tool."""
    
    @pytest.fixture
    def weather_tool(self):
        """Create Weather tool for testing."""
        return WeatherTool()
    
    def test_get_capabilities(self, weather_tool):
        """Test getting tool capabilities."""
        capabilities = weather_tool.get_capabilities()
        assert len(capabilities) == 3
        
        capability_names = [cap.name for cap in capabilities]
        assert "get_current_weather" in capability_names
        assert "get_weather_forecast" in capability_names
        assert "get_weather_by_coordinates" in capability_names
    
    def test_validate_parameters(self, weather_tool):
        """Test parameter validation."""
        # Valid city parameters
        is_valid, error = weather_tool.validate_parameters("get_current_weather", {
            "city": "New York",
            "units": "metric"
        })
        assert is_valid is True
        assert error is None
        
        # Invalid coordinates
        is_valid, error = weather_tool.validate_parameters("get_weather_by_coordinates", {
            "lat": 91,  # Invalid latitude
            "lon": 0
        })
        assert is_valid is False
        assert "lat must be a number between -90 and 90" in error
        
        # Missing city
        is_valid, error = weather_tool.validate_parameters("get_current_weather", {})
        assert is_valid is False
        assert "Missing required parameter: city" in error
    
    @pytest.mark.asyncio
    async def test_get_current_weather_success(self, weather_tool):
        """Test successful current weather retrieval."""
        mock_response = {
            "name": "New York",
            "sys": {"country": "US", "sunrise": 1609459200, "sunset": 1609495600},
            "coord": {"lat": 40.7128, "lon": -74.0060},
            "main": {
                "temp": 22.5,
                "feels_like": 24.0,
                "humidity": 65,
                "pressure": 1013
            },
            "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 3.5, "deg": 180},
            "clouds": {"all": 0},
            "visibility": 10000,
            "dt": 1609459200
        }
        
        weather_tool.api_key = "1234567890abcdef1234567890abcdef"  # Valid format
        
        with patch.object(weather_tool, '_make_request', return_value=mock_response):
            result = await weather_tool.execute("get_current_weather", {
                "city": "New York",
                "units": "metric"
            })
        
        assert result.status == ToolStatus.SUCCESS
        assert "location" in result.data
        assert result.data["location"]["name"] == "New York"
        assert result.data["current"]["temperature"] == 22.5
        assert result.data["weather"]["main"] == "Clear"
    
    @pytest.mark.asyncio
    async def test_get_current_weather_no_api_key(self, weather_tool):
        """Test weather retrieval without API key."""
        weather_tool.api_key = None
        
        result = await weather_tool.execute("get_current_weather", {
            "city": "New York"
        })
        
        assert result.status == ToolStatus.ERROR
        assert "WEATHER_API_KEY not configured" in result.error
    
    def test_validate_api_key(self, weather_tool):
        """Test API key validation."""
        # No key
        weather_tool.api_key = None
        assert weather_tool.validate_api_key() is False
        
        # Invalid key length
        weather_tool.api_key = "short"
        assert weather_tool.validate_api_key() is False
        
        # Valid key format
        weather_tool.api_key = "1234567890abcdef1234567890abcdef"
        assert weather_tool.validate_api_key() is True


class TestNewsTool:
    """Test cases for News Tool."""
    
    @pytest.fixture
    def news_tool(self):
        """Create News tool for testing."""
        return NewsTool()
    
    def test_get_capabilities(self, news_tool):
        """Test getting tool capabilities."""
        capabilities = news_tool.get_capabilities()
        assert len(capabilities) == 3
        
        capability_names = [cap.name for cap in capabilities]
        assert "get_top_headlines" in capability_names
        assert "search_news" in capability_names
        assert "get_sources" in capability_names
    
    def test_validate_parameters(self, news_tool):
        """Test parameter validation."""
        # Valid headline parameters
        is_valid, error = news_tool.validate_parameters("get_top_headlines", {
            "country": "us",
            "category": "technology",
            "page_size": 20
        })
        assert is_valid is True
        assert error is None
        
        # Invalid country code
        is_valid, error = news_tool.validate_parameters("get_top_headlines", {
            "country": "USA"  # Should be 2 letters
        })
        assert is_valid is False
        assert "country must be a 2-letter ISO country code" in error
        
        # Missing search query
        is_valid, error = news_tool.validate_parameters("search_news", {})
        assert is_valid is False
        assert "Missing required parameter: query" in error
    
    @pytest.mark.asyncio
    async def test_get_top_headlines_success(self, news_tool):
        """Test successful headlines retrieval."""
        mock_response = {
            "articles": [
                {
                    "title": "AI Breakthrough",
                    "description": "New AI technology announced",
                    "content": "Full article content here...",
                    "source": {"name": "Tech News"},
                    "author": "John Doe",
                    "url": "https://example.com/article1",
                    "urlToImage": "https://example.com/image1.jpg",
                    "publishedAt": "2024-01-01T12:00:00Z"
                }
            ],
            "totalResults": 1
        }
        
        news_tool.api_key = "1234567890abcdef1234567890abcdef"  # Valid format
        
        with patch.object(news_tool, '_make_request', return_value=mock_response):
            result = await news_tool.execute("get_top_headlines", {
                "country": "us",
                "page_size": 10
            })
        
        assert result.status == ToolStatus.SUCCESS
        assert "articles" in result.data
        assert len(result.data["articles"]) == 1
        assert result.data["articles"][0]["title"] == "AI Breakthrough"
        assert result.data["total_results"] == 1
    
    @pytest.mark.asyncio
    async def test_search_news_success(self, news_tool):
        """Test successful news search."""
        mock_response = {
            "articles": [
                {
                    "title": "Climate Change Update",
                    "description": "Latest climate research",
                    "source": {"name": "Science News"},
                    "publishedAt": "2024-01-01T10:00:00Z"
                }
            ],
            "totalResults": 1
        }
        
        news_tool.api_key = "1234567890abcdef1234567890abcdef"
        
        with patch.object(news_tool, '_make_request', return_value=mock_response):
            result = await news_tool.execute("search_news", {
                "query": "climate change",
                "page_size": 5
            })
        
        assert result.status == ToolStatus.SUCCESS
        assert result.data["search_query"] == "climate change"
        assert "date_range" in result.data
    
    def test_create_summary(self, news_tool):
        """Test summary creation."""
        # Short content
        short_content = "Short article content"
        summary = news_tool._create_summary(short_content)
        assert summary == short_content
        
        # Long content
        long_content = "This is a very long article content that should be truncated " * 20
        summary = news_tool._create_summary(long_content, max_length=50)
        assert len(summary) <= 53  # 50 + "..."
        assert summary.endswith("...")
    
    def test_validate_api_key(self, news_tool):
        """Test API key validation."""
        # No key
        news_tool.api_key = None
        assert news_tool.validate_api_key() is False
        
        # Valid key format
        news_tool.api_key = "1234567890abcdef1234567890abcdef"
        assert news_tool.validate_api_key() is True


if __name__ == "__main__":
    pytest.main([__file__])
