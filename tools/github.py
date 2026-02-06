"""
GitHub API Tool - Integration with GitHub REST API
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseTool, ToolResult, ToolStatus, ToolCapability, ToolParameter


class GitHubTool(BaseTool):
    """GitHub API integration tool."""
    
    def __init__(self):
        """Initialize GitHub tool."""
        super().__init__(
            name="github",
            description="Integration with GitHub API for repository and user information"
        )
        
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        
        # Define capabilities
        self.capabilities = [
            ToolCapability(
                name="search_repositories",
                description="Search GitHub repositories",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Search query (e.g., 'language:python stars:>100')",
                        required=True
                    ),
                    ToolParameter(
                        name="sort",
                        type="string",
                        description="Sort field (stars, forks, updated)",
                        required=False,
                        default="stars",
                        enum=["stars", "forks", "updated", "created"]
                    ),
                    ToolParameter(
                        name="order",
                        type="string",
                        description="Sort order (desc, asc)",
                        required=False,
                        default="desc",
                        enum=["desc", "asc"]
                    ),
                    ToolParameter(
                        name="per_page",
                        type="number",
                        description="Number of results per page (max 100)",
                        required=False,
                        default=10
                    )
                ],
                examples=[
                    "search_repositories(query='language:python machine learning')",
                    "search_repositories(query='stars:>1000', sort='stars')",
                    "search_repositories(query='react', per_page=20)"
                ]
            ),
            ToolCapability(
                name="get_repository",
                description="Get detailed information about a specific repository",
                parameters=[
                    ToolParameter(
                        name="owner",
                        type="string",
                        description="Repository owner (username or organization)",
                        required=True
                    ),
                    ToolParameter(
                        name="repo",
                        type="string",
                        description="Repository name",
                        required=True
                    )
                ],
                examples=[
                    "get_repository(owner='facebook', repo='react')",
                    "get_repository(owner='python', repo='cpython')"
                ]
            ),
            ToolCapability(
                name="get_user_info",
                description="Get information about a GitHub user",
                parameters=[
                    ToolParameter(
                        name="username",
                        type="string",
                        description="GitHub username",
                        required=True
                    )
                ],
                examples=[
                    "get_user_info(username='torvalds')",
                    "get_user_info(username='octocat')"
                ]
            ),
            ToolCapability(
                name="list_repository_commits",
                description="List commits in a repository",
                parameters=[
                    ToolParameter(
                        name="owner",
                        type="string",
                        description="Repository owner",
                        required=True
                    ),
                    ToolParameter(
                        name="repo",
                        type="string",
                        description="Repository name",
                        required=True
                    ),
                    ToolParameter(
                        name="per_page",
                        type="number",
                        description="Number of commits to return (max 100)",
                        required=False,
                        default=10
                    )
                ],
                examples=[
                    "list_repository_commits(owner='facebook', repo='react')",
                    "list_repository_commits(owner='python', repo='cpython', per_page=5)"
                ]
            )
        ]
    
    async def execute(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a GitHub API capability."""
        try:
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(capability, parameters)
            if not is_valid:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Invalid parameters: {error_msg}"
                )
            
            # Execute the specific capability
            if capability == "search_repositories":
                return await self._search_repositories(parameters)
            elif capability == "get_repository":
                return await self._get_repository(parameters)
            elif capability == "get_user_info":
                return await self._get_user_info(parameters)
            elif capability == "list_repository_commits":
                return await self._list_repository_commits(parameters)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"GitHub API error: {str(e)}"
            )
    
    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Ops-Assistant/1.0"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    raise Exception("Rate limit exceeded or insufficient permissions")
                elif response.status == 404:
                    raise Exception("Resource not found")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def _search_repositories(self, params: Dict[str, Any]) -> ToolResult:
        """Search for repositories."""
        url = f"{self.base_url}/search/repositories"
        
        search_params = {
            "q": params["query"],
            "sort": params.get("sort", "stars"),
            "order": params.get("order", "desc"),
            "per_page": min(params.get("per_page", 10), 100)
        }
        
        try:
            data = await self._make_request(url, search_params)
            
            # Extract relevant information
            repositories = []
            for item in data.get("items", []):
                repo_info = {
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "owner": item["owner"]["login"],
                    "description": item.get("description", ""),
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "language": item.get("language"),
                    "updated_at": item["updated_at"],
                    "created_at": item["created_at"],
                    "url": item["html_url"],
                    "topics": item.get("topics", [])
                }
                repositories.append(repo_info)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "repositories": repositories,
                    "total_count": data.get("total_count", 0),
                    "query": params["query"]
                },
                metadata={
                    "rate_limit_remaining": self.rate_limit_remaining,
                    "results_returned": len(repositories)
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Repository search failed: {str(e)}"
            )
    
    async def _get_repository(self, params: Dict[str, Any]) -> ToolResult:
        """Get detailed repository information."""
        url = f"{self.base_url}/repos/{params['owner']}/{params['repo']}"
        
        try:
            data = await self._make_request(url)
            
            repo_info = {
                "name": data["name"],
                "full_name": data["full_name"],
                "owner": data["owner"]["login"],
                "description": data.get("description", ""),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "watchers": data["watchers_count"],
                "language": data.get("language"),
                "size": data["size"],
                "updated_at": data["updated_at"],
                "created_at": data["created_at"],
                "pushed_at": data["pushed_at"],
                "url": data["html_url"],
                "clone_url": data["clone_url"],
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name") if data.get("license") else None,
                "default_branch": data["default_branch"],
                "open_issues": data["open_issues_count"],
                "has_issues": data["has_issues"],
                "has_wiki": data["has_wiki"],
                "has_pages": data["has_pages"]
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=repo_info,
                metadata={
                    "rate_limit_remaining": self.rate_limit_remaining
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Repository lookup failed: {str(e)}"
            )
    
    async def _get_user_info(self, params: Dict[str, Any]) -> ToolResult:
        """Get user information."""
        url = f"{self.base_url}/users/{params['username']}"
        
        try:
            data = await self._make_request(url)
            
            user_info = {
                "login": data["login"],
                "name": data.get("name"),
                "bio": data.get("bio"),
                "company": data.get("company"),
                "location": data.get("location"),
                "email": data.get("email"),
                "blog": data.get("blog"),
                "avatar_url": data["avatar_url"],
                "followers": data["followers"],
                "following": data["following"],
                "public_repos": data["public_repos"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "url": data["html_url"]
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=user_info,
                metadata={
                    "rate_limit_remaining": self.rate_limit_remaining
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"User lookup failed: {str(e)}"
            )
    
    async def _list_repository_commits(self, params: Dict[str, Any]) -> ToolResult:
        """List commits in a repository."""
        url = f"{self.base_url}/repos/{params['owner']}/{params['repo']}/commits"
        
        commit_params = {
            "per_page": min(params.get("per_page", 10), 100)
        }
        
        try:
            data = await self._make_request(url, commit_params)
            
            commits = []
            for commit in data:
                commit_info = {
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "author": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"],
                    "url": commit["html_url"]
                }
                commits.append(commit_info)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "commits": commits,
                    "repository": f"{params['owner']}/{params['repo']}",
                    "count": len(commits)
                },
                metadata={
                    "rate_limit_remaining": self.rate_limit_remaining
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Commit listing failed: {str(e)}"
            )
    
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
        if capability == "search_repositories":
            per_page = parameters.get("per_page", 10)
            if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
                return False, "per_page must be an integer between 1 and 100"
        
        elif capability == "list_repository_commits":
            per_page = parameters.get("per_page", 10)
            if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
                return False, "per_page must be an integer between 1 and 100"
        
        return True, None
    
    def validate_api_key(self) -> bool:
        """Validate GitHub API token."""
        if not self.token:
            return False  # Token is optional for public endpoints
        
        # Basic validation - GitHub tokens start with specific prefixes
        return (
            self.token.startswith("ghp_") or 
            self.token.startswith("gho_") or
            self.token.startswith("ghu_") or
            self.token.startswith("ghs_") or
            self.token.startswith("ghr_")
        )
