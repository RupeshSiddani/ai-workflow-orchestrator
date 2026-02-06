"""
News API Tool - Integration with NewsAPI
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .base import BaseTool, ToolResult, ToolStatus, ToolCapability, ToolParameter


class NewsTool(BaseTool):
    """News API integration tool using NewsAPI."""
    
    def __init__(self):
        """Initialize news tool."""
        super().__init__(
            name="news",
            description="Integration with NewsAPI for news articles and headlines"
        )
        
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        
        # Define capabilities
        self.capabilities = [
            ToolCapability(
                name="get_top_headlines",
                description="Get top headlines from various sources",
                parameters=[
                    ToolParameter(
                        name="country",
                        type="string",
                        description="ISO 3166-1 alpha-2 country code (e.g., 'us', 'gb', 'jp')",
                        required=False
                    ),
                    ToolParameter(
                        name="category",
                        type="string",
                        description="News category (business, entertainment, general, health, science, sports, technology)",
                        required=False,
                        enum=["business", "entertainment", "general", "health", "science", "sports", "technology"]
                    ),
                    ToolParameter(
                        name="source",
                        type="string",
                        description="Specific news source ID",
                        required=False
                    ),
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Search query for headlines",
                        required=False
                    ),
                    ToolParameter(
                        name="page_size",
                        type="number",
                        description="Number of results to return (max 100)",
                        required=False,
                        default=20
                    )
                ],
                examples=[
                    "get_top_headlines(country='us')",
                    "get_top_headlines(category='technology', country='us')",
                    "get_top_headlines(query='artificial intelligence', page_size=10)"
                ]
            ),
            ToolCapability(
                name="search_news",
                description="Search for news articles from the past month",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Search query or keywords",
                        required=True
                    ),
                    ToolParameter(
                        name="language",
                        type="string",
                        description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')",
                        required=False,
                        default="en"
                    ),
                    ToolParameter(
                        name="sort_by",
                        type="string",
                        description="Sort order (relevancy, popularity, publishedAt)",
                        required=False,
                        default="publishedAt",
                        enum=["relevancy", "popularity", "publishedAt"]
                    ),
                    ToolParameter(
                        name="page_size",
                        type="number",
                        description="Number of results to return (max 100)",
                        required=False,
                        default=20
                    )
                ],
                examples=[
                    "search_news(query='climate change')",
                    "search_news(query='machine learning', language='en')",
                    "search_news(query='stock market', sort_by='popularity')"
                ]
            ),
            ToolCapability(
                name="get_sources",
                description="Get available news sources",
                parameters=[
                    ToolParameter(
                        name="category",
                        type="string",
                        description="Filter by category",
                        required=False,
                        enum=["business", "entertainment", "general", "health", "science", "sports", "technology"]
                    ),
                    ToolParameter(
                        name="language",
                        type="string",
                        description="Filter by language (ISO 639-1)",
                        required=False
                    ),
                    ToolParameter(
                        name="country",
                        type="string",
                        description="Filter by country (ISO 3166-1)",
                        required=False
                    )
                ],
                examples=[
                    "get_sources()",
                    "get_sources(category='technology', language='en')",
                    "get_sources(country='us')"
                ]
            )
        ]
    
    async def execute(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a news API capability."""
        try:
            # Validate API key
            if not self.validate_api_key():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="NEWS_API_KEY not configured or invalid"
                )
            
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(capability, parameters)
            if not is_valid:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Invalid parameters: {error_msg}"
                )
            
            # Execute the specific capability
            if capability == "get_top_headlines":
                return await self._get_top_headlines(parameters)
            elif capability == "search_news":
                return await self._search_news(parameters)
            elif capability == "get_sources":
                return await self._get_sources(parameters)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"News API error: {str(e)}"
            )
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to NewsAPI."""
        params["apiKey"] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise Exception("Invalid API key")
                elif response.status == 429:
                    raise Exception("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def _get_top_headlines(self, params: Dict[str, Any]) -> ToolResult:
        """Get top headlines."""
        request_params = {}
        
        # Add optional parameters
        if "country" in params:
            request_params["country"] = params["country"]
        if "category" in params:
            request_params["category"] = params["category"]
        if "source" in params:
            request_params["sources"] = params["source"]
        if "query" in params:
            request_params["q"] = params["query"]
        
        request_params["pageSize"] = min(params.get("page_size", 20), 100)
        
        try:
            data = await self._make_request("top-headlines", request_params)
            
            articles = []
            for article in data.get("articles", []):
                article_info = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "url": article.get("url", ""),
                    "image_url": article.get("urlToImage", ""),
                    "published_at": article.get("publishedAt", ""),
                    "summary": self._create_summary(article.get("description", article.get("content", "")))
                }
                articles.append(article_info)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "articles": articles,
                    "total_results": data.get("totalResults", 0),
                    "query": request_params
                },
                metadata={
                    "api_source": "NewsAPI",
                    "results_returned": len(articles)
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Headlines lookup failed: {str(e)}"
            )
    
    async def _search_news(self, params: Dict[str, Any]) -> ToolResult:
        """Search for news articles."""
        request_params = {
            "q": params["query"],
            "language": params.get("language", "en"),
            "sortBy": params.get("sort_by", "publishedAt"),
            "pageSize": min(params.get("page_size", 20), 100)
        }
        
        # Set date range to past month
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        request_params["from"] = start_date.strftime("%Y-%m-%d")
        request_params["to"] = end_date.strftime("%Y-%m-%d")
        
        try:
            data = await self._make_request("everything", request_params)
            
            articles = []
            for article in data.get("articles", []):
                article_info = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "url": article.get("url", ""),
                    "image_url": article.get("urlToImage", ""),
                    "published_at": article.get("publishedAt", ""),
                    "summary": self._create_summary(article.get("description", article.get("content", "")))
                }
                articles.append(article_info)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "articles": articles,
                    "total_results": data.get("totalResults", 0),
                    "search_query": params["query"],
                    "date_range": {
                        "from": request_params["from"],
                        "to": request_params["to"]
                    }
                },
                metadata={
                    "api_source": "NewsAPI",
                    "results_returned": len(articles)
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"News search failed: {str(e)}"
            )
    
    async def _get_sources(self, params: Dict[str, Any]) -> ToolResult:
        """Get available news sources."""
        request_params = {}
        
        if "category" in params:
            request_params["category"] = params["category"]
        if "language" in params:
            request_params["language"] = params["language"]
        if "country" in params:
            request_params["country"] = params["country"]
        
        try:
            data = await self._make_request("top-headlines/sources", request_params)
            
            sources = []
            for source in data.get("sources", []):
                source_info = {
                    "id": source.get("id", ""),
                    "name": source.get("name", ""),
                    "description": source.get("description", ""),
                    "category": source.get("category", ""),
                    "language": source.get("language", ""),
                    "country": source.get("country", ""),
                    "url": source.get("url", "")
                }
                sources.append(source_info)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "sources": sources,
                    "total_sources": len(sources),
                    "filters": request_params
                },
                metadata={
                    "api_source": "NewsAPI"
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Sources lookup failed: {str(e)}"
            )
    
    def _create_summary(self, content: str, max_length: int = 200) -> str:
        """Create a summary from article content."""
        if not content:
            return ""
        
        # Remove HTML tags and extra whitespace
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        if len(clean_content) <= max_length:
            return clean_content
        
        # Truncate at word boundary
        truncated = clean_content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # Only truncate if we have most of the content
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def get_capabilities(self) -> List[ToolCapability]:
        """Get list of available capabilities."""
        return self.capabilities
    
    def validate_parameters(
        self,
        capability: str,
        parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate parameters for a capability."""
        cap = next((c for c in self.capabilities if c.name == capability), None)
        if not cap:
            return False, f"Unknown capability: {capability}"
        
        # Check required parameters
        for param in cap.parameters:
            if param.required and param.name not in parameters:
                return False, f"Missing required parameter: {param.name}"
        
        # Validate parameter types and values
        if capability == "search_news":
            query = parameters.get("query", "")
            if not isinstance(query, str) or len(query.strip()) == 0:
                return False, "query must be a non-empty string"
        
        # Validate page_size
        page_size = parameters.get("page_size", 20)
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            return False, "page_size must be an integer between 1 and 100"
        
        # Validate country codes
        if "country" in parameters:
            country = parameters["country"]
            if not isinstance(country, str) or len(country) != 2:
                return False, "country must be a 2-letter ISO country code"
        
        # Validate language codes
        if "language" in parameters:
            language = parameters["language"]
            if not isinstance(language, str) or len(language) != 2:
                return False, "language must be a 2-letter ISO language code"
        
        return True, None
    
    def validate_api_key(self) -> bool:
        """Validate NewsAPI key."""
        if not self.api_key:
            return False
        
        # NewsAPI keys are typically 32 characters long and alphanumeric
        return len(self.api_key) == 32 and self.api_key.isalnum()
