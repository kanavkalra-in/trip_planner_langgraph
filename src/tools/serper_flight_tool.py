"""
Flight search tool using Google Serper API.

This module provides a flight search tool that follows SOLID principles:
- Single Responsibility: Separate classes for API client, response parser, and tool
- Open/Closed: Extensible design for different flight search providers
- Liskov Substitution: Properly implements LangChain tool interface
- Interface Segregation: Focused interfaces for each component
- Dependency Inversion: Depends on abstractions (config, logging)
"""
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests
from langchain_core.tools import tool


class AviationQueryClient(ABC):
    """
    Abstract base class for flight search API clients.
    Follows Dependency Inversion Principle - depends on abstraction.
    """
    
    @abstractmethod
    def query_route(
        self,
        origin_city: str,
        arrival_city: str,
        origin_country_code: str,
    ) -> Dict:
        """
        Search for flights between two cities.
        
        Args:
            origin_city: The starting city for the flight
            arrival_city: The destination city for the flight
            origin_country_code: The ISO country code of the starting location
            
        Returns:
            Dictionary containing the API response
        """
        pass


class GoogleSerperClient(AviationQueryClient):
    """
    Google Serper API client for flight searches.
    Single Responsibility: Only handles API communication with Serper.
    """
    
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper API client.
        
        Args:
            api_key: Serper API key. If None, uses SERPER_API_KEY from environment.
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SERPER_API_KEY is required. Set SERPER_API_KEY environment variable."
            )
    
    def query_route(
        self,
        origin_city: str,
        arrival_city: str,
        origin_country_code: str,
    ) -> Dict:
        """
        Search for flights using Google Serper API.
        
        Args:
            origin_city: The starting city for the flight
            arrival_city: The destination city for the flight
            origin_country_code: The ISO country code of the starting location
            
        Returns:
            Dictionary containing the API response
            
        Raises:
            requests.RequestException: If API request fails
        """
        payload = json.dumps({
            "q": f"{origin_city} to {arrival_city} prices of flights",
            "location": origin_country_code,
            "gl": origin_country_code,
            "engine": "google_flights",
            "departure_id": origin_city,
            "arrival_id": arrival_city,
        })
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        
        response = requests.post(
            self.BASE_URL,
            headers=headers,
            data=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


class AviationDataParser(ABC):
    """
    Abstract base class for parsing flight search responses.
    Follows Dependency Inversion Principle.
    """
    
    @abstractmethod
    def format_response(self, response: Dict) -> str:
        """
        Parse API response into a human-readable summary.
        
        Args:
            response: The API response dictionary
            
        Returns:
            Formatted string summary of flight information
        """
        pass


class SerperDataFormatter(AviationDataParser):
    """
    Parser for Google Serper API flight search responses.
    Single Responsibility: Only responsible for parsing Serper API responses.
    """
    
    def format_response(self, response: Dict) -> str:
        """
        Parse Serper API response into a formatted summary.
        
        Args:
            response: The Serper API response dictionary
            
        Returns:
            Formatted string with flight information and Google Flights link
        """
        formatted_results = []
        booking_url = ""
        
        search_results = response.get("organic", [])
        for item in search_results:
            url = item.get("link", "")
            if not booking_url and url.startswith("https://www.google.com/travel/flights"):
                booking_url = f"Get flight details from Google Flights: {url}"
            
            description = item.get("snippet")
            if description:
                formatted_results.append(description)
        
        if booking_url:
            formatted_results.append(booking_url)
        
        if not formatted_results:
            return "No flight information found for the specified route."
        
        return "\n\n".join(formatted_results)


def format_aviation_results(api_response: dict) -> str:
    """
    Extract flight information from Serper API response.
    
    Args:
        api_response: The API response dictionary
        
    Returns:
        Formatted string with flight information
    """
    formatter = SerperDataFormatter()
    return formatter.format_response(api_response)


def query_route_pricing(
    origin_country_code: str,
    origin_city: str,
    arrival_city: str,
) -> str:
    """
    Get flight data from Serper API.
    
    Args:
        origin_country_code: The ISO country code of the starting location (e.g., "pt")
        origin_city: The starting city for the flight (e.g., "Lisbon, Portugal")
        arrival_city: The destination city for the flight (e.g., "Paris, France")
        
    Returns:
        Formatted string with flight information
    """
    client = GoogleSerperClient()
    api_response = client.query_route(
        origin_city=origin_city,
        arrival_city=arrival_city,
        origin_country_code=origin_country_code,
    )
    return format_aviation_results(api_response)


@tool
def aviation_route_search_tool(
    origin_country_code: str,
    origin_city: str,
    arrival_city: str,
) -> str:
    """
    Retrieve flight pricing and availability information for a specified travel route.
    
    This tool performs a single search operation per user query. It must be invoked
    only once per request using the exact origin city provided by the user. Do not
    initiate multiple searches with alternative city names or variations.
    
    The tool analyzes the search results to extract estimated flight prices and
    generates a direct link to Google Flights for detailed booking information.
    Only include flight data that precisely matches the provided origin city and
    destination. Filter out any results that do not correspond to these specific
    locations.

    Args:
        origin_country_code: ISO 3166-1 alpha-2 country code for the origin (e.g., "pt" for Portugal)
        origin_city: Full name of the departure city including country (e.g., "Lisbon, Portugal")
        arrival_city: Full name of the arrival city including country (e.g., "Paris, France")
        
    Returns:
        A formatted text string containing flight price estimates, availability details,
        and a clickable Google Flights URL for the specified route
    """
    return query_route_pricing(origin_country_code, origin_city, arrival_city)
