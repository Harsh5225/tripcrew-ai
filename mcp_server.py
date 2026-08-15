import os
import requests
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Initialize the MCP Server
mcp = MCPServer("TripCrew Server")

@mcp.tool()
def search_flights(destination_iata: str) -> list:
    """
    Fetches live flight data for a given destination IATA code.
    Returns a list of available flights.
    """
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    default_origin = os.getenv("DEFAULT_ORIGIN_IATA", "DEL")
    
    # We are only using arr_iata now to increase our chances of finding a flight
    url = f"http://api.aviationstack.com/v1/flights?access_key={api_key}&arr_iata={destination_iata}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            return [{"error": data["error"]}]
            
        flights = data.get("data", [])
      
        if not flights:
            return [{"error": "No flights found", "raw_response": data}]
            
        return flights[:3]
    except Exception as e:
        return [{"error": f"Failed to fetch flights: {str(e)}"}]


@mcp.tool()
def search_hotels(location: str) -> str:
    """
    Searches the web for hotel options in a specific location.
    Provides current pricing and availability.
    """
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        query = f"Top highly rated hotels in {location} with current estimated prices per night"
        response = client.search(query=query, search_depth="basic")
        
        results = response.get("results", [])
        
        if not results:
            return f"No hotel data found. Raw response: {response}"
            
        formatted_results = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        return formatted_results
    except Exception as e:
        return f"Failed to fetch hotels: {str(e)}"


@mcp.tool()
def search_activities(location: str) -> str:
    """
    Searches the web for top tourist attractions and restaurants in the specified location.
    """
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        query = f"Best tourist attractions, things to do, and top restaurants in {location}"
        response = client.search(query=query, search_depth="basic")
        
        results = response.get("results", [])
        
        if not results:
            return f"No activities found. Raw response: {response}"
            
        formatted_results = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        return formatted_results
    except Exception as e:
        return f"Failed to fetch activities: {str(e)}"

if __name__ == "__main__":
    mcp.run()