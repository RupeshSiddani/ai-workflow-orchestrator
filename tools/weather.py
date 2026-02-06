"""
Weather API Tool - Integration with OpenWeatherMap API
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseTool, ToolResult, ToolStatus, ToolCapability, ToolParameter


class WeatherTool(BaseTool):
    """Weather API integration tool using OpenWeatherMap."""
    
    def __init__(self):
        """Initialize weather tool."""
        super().__init__(
            name="weather",
            description="Integration with OpenWeatherMap API for weather information"
        )
        
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Define capabilities
        self.capabilities = [
            ToolCapability(
                name="get_current_weather",
                description="Get current weather for a city",
                parameters=[
                    ToolParameter(
                        name="city",
                        type="string",
                        description="City name (e.g., 'London', 'New York', 'Tokyo')",
                        required=True
                    ),
                    ToolParameter(
                        name="country_code",
                        type="string",
                        description="ISO 3166 country code (e.g., 'US', 'GB', 'JP')",
                        required=False
                    ),
                    ToolParameter(
                        name="units",
                        type="string",
                        description="Temperature units (metric, imperial, kelvin)",
                        required=False,
                        default="metric",
                        enum=["metric", "imperial", "kelvin"]
                    )
                ],
                examples=[
                    "get_current_weather(city='London')",
                    "get_current_weather(city='New York', country_code='US')",
                    "get_current_weather(city='Tokyo', units='imperial')"
                ]
            ),
            ToolCapability(
                name="get_weather_forecast",
                description="Get 5-day weather forecast for a city",
                parameters=[
                    ToolParameter(
                        name="city",
                        type="string",
                        description="City name",
                        required=True
                    ),
                    ToolParameter(
                        name="country_code",
                        type="string",
                        description="ISO 3166 country code",
                        required=False
                    ),
                    ToolParameter(
                        name="units",
                        type="string",
                        description="Temperature units",
                        required=False,
                        default="metric",
                        enum=["metric", "imperial", "kelvin"]
                    )
                ],
                examples=[
                    "get_weather_forecast(city='London')",
                    "get_weather_forecast(city='Paris', country_code='FR')"
                ]
            ),
            ToolCapability(
                name="get_weather_by_coordinates",
                description="Get weather by geographic coordinates",
                parameters=[
                    ToolParameter(
                        name="lat",
                        type="number",
                        description="Latitude",
                        required=True
                    ),
                    ToolParameter(
                        name="lon",
                        type="number",
                        description="Longitude",
                        required=True
                    ),
                    ToolParameter(
                        name="units",
                        type="string",
                        description="Temperature units",
                        required=False,
                        default="metric",
                        enum=["metric", "imperial", "kelvin"]
                    )
                ],
                examples=[
                    "get_weather_by_coordinates(lat=40.7128, lon=-74.0060)",
                    "get_weather_by_coordinates(lat=51.5074, lon=-0.1278, units='imperial')"
                ]
            )
        ]
    
    async def execute(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a weather API capability."""
        try:
            # Validate API key
            if not self.validate_api_key():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="WEATHER_API_KEY not configured or invalid"
                )
            
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(capability, parameters)
            if not is_valid:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Invalid parameters: {error_msg}"
                )
            
            # Execute the specific capability
            if capability == "get_current_weather":
                return await self._get_current_weather(parameters)
            elif capability == "get_weather_forecast":
                return await self._get_weather_forecast(parameters)
            elif capability == "get_weather_by_coordinates":
                return await self._get_weather_by_coordinates(parameters)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Weather API error: {str(e)}"
            )
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to OpenWeatherMap API."""
        params["appid"] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise Exception("Invalid API key")
                elif response.status == 404:
                    raise Exception("City not found")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def _get_current_weather(self, params: Dict[str, Any]) -> ToolResult:
        """Get current weather for a city."""
        location = params["city"]
        if params.get("country_code"):
            location += f",{params['country_code']}"
        
        request_params = {
            "q": location,
            "units": params.get("units", "metric")
        }
        
        try:
            data = await self._make_request("weather", request_params)
            
            weather_info = {
                "location": {
                    "name": data["name"],
                    "country": data["sys"]["country"],
                    "coordinates": {
                        "lat": data["coord"]["lat"],
                        "lon": data["coord"]["lon"]
                    }
                },
                "current": {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                    "uv_index": data.get("uvi", 0)  # Not always available
                },
                "weather": {
                    "main": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"]
                },
                "wind": {
                    "speed": data["wind"]["speed"],
                    "direction": data["wind"].get("deg", 0)
                },
                "clouds": data["clouds"]["all"],
                "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).isoformat(),
                "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).isoformat(),
                "timestamp": datetime.fromtimestamp(data["dt"]).isoformat(),
                "units": params.get("units", "metric")
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=weather_info,
                metadata={
                    "api_source": "OpenWeatherMap",
                    "location_query": location
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Current weather lookup failed: {str(e)}"
            )
    
    async def _get_weather_forecast(self, params: Dict[str, Any]) -> ToolResult:
        """Get 5-day weather forecast for a city."""
        location = params["city"]
        if params.get("country_code"):
            location += f",{params['country_code']}"
        
        request_params = {
            "q": location,
            "units": params.get("units", "metric")
        }
        
        try:
            data = await self._make_request("forecast", request_params)
            
            # Process forecast data (group by day)
            daily_forecasts = {}
            for item in data["list"]:
                date = datetime.fromtimestamp(item["dt"]).date().isoformat()
                
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        "date": date,
                        "temperatures": [],
                        "conditions": [],
                        "humidity": [],
                        "wind_speeds": []
                    }
                
                day_data = daily_forecasts[date]
                day_data["temperatures"].append(item["main"]["temp"])
                day_data["conditions"].append(item["weather"][0]["description"])
                day_data["humidity"].append(item["main"]["humidity"])
                day_data["wind_speeds"].append(item["wind"]["speed"])
            
            # Calculate daily summaries
            forecasts = []
            for date, day_data in daily_forecasts.items():
                forecast = {
                    "date": date,
                    "temperature": {
                        "min": min(day_data["temperatures"]),
                        "max": max(day_data["temperatures"]),
                        "avg": sum(day_data["temperatures"]) / len(day_data["temperatures"])
                    },
                    "condition": max(set(day_data["conditions"]), key=day_data["conditions"].count),
                    "humidity": sum(day_data["humidity"]) / len(day_data["humidity"]),
                    "wind_speed": sum(day_data["wind_speeds"]) / len(day_data["wind_speeds"])
                }
                forecasts.append(forecast)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "location": {
                        "name": data["city"]["name"],
                        "country": data["city"]["country"]
                    },
                    "forecasts": forecasts[:5],  # Limit to 5 days
                    "units": params.get("units", "metric")
                },
                metadata={
                    "api_source": "OpenWeatherMap",
                    "location_query": location,
                    "forecast_days": len(forecasts)
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Weather forecast lookup failed: {str(e)}"
            )
    
    async def _get_weather_by_coordinates(self, params: Dict[str, Any]) -> ToolResult:
        """Get weather by geographic coordinates."""
        request_params = {
            "lat": params["lat"],
            "lon": params["lon"],
            "units": params.get("units", "metric")
        }
        
        try:
            data = await self._make_request("weather", request_params)
            
            weather_info = {
                "location": {
                    "name": data["name"],
                    "country": data["sys"]["country"],
                    "coordinates": {
                        "lat": data["coord"]["lat"],
                        "lon": data["coord"]["lon"]
                    }
                },
                "current": {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "visibility": data.get("visibility", 0) / 1000
                },
                "weather": {
                    "main": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"]
                },
                "wind": {
                    "speed": data["wind"]["speed"],
                    "direction": data["wind"].get("deg", 0)
                },
                "clouds": data["clouds"]["all"],
                "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).isoformat(),
                "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).isoformat(),
                "timestamp": datetime.fromtimestamp(data["dt"]).isoformat(),
                "units": params.get("units", "metric")
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=weather_info,
                metadata={
                    "api_source": "OpenWeatherMap",
                    "coordinates": f"{params['lat']}, {params['lon']}"
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Coordinate weather lookup failed: {str(e)}"
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
        if capability in ["get_current_weather", "get_weather_forecast"]:
            city = parameters.get("city", "")
            if not isinstance(city, str) or len(city.strip()) == 0:
                return False, "city must be a non-empty string"
        
        elif capability == "get_weather_by_coordinates":
            lat = parameters.get("lat")
            lon = parameters.get("lon")
            
            if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
                return False, "lat must be a number between -90 and 90"
            
            if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
                return False, "lon must be a number between -180 and 180"
        
        return True, None
    
    def validate_api_key(self) -> bool:
        """Validate OpenWeatherMap API key."""
        if not self.api_key:
            return False
        
        # OpenWeatherMap API keys are typically 32 characters long
        return len(self.api_key) == 32 and self.api_key.isalnum()
