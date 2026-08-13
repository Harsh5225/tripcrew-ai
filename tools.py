import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "DEL")
@tool
def search_flights(destination_iata:str)->list[dict]:
  """
    Searches for active flights from the default origin to the specified destination.
    Args:
        destination_iata (str): The 3-letter IATA code for the destination airport (e.g., 'BKK' for Bangkok).
    """
  print(f"🔧 Tool Execution: Searching flights {DEFAULT_ORIGIN_IATA} to {destination_iata}...")
  url = "http://api.aviationstack.com/v1/flights"
  params={
    "access_key": AVIATIONSTACK_API_KEY,
    "dep_iata": DEFAULT_ORIGIN_IATA,
    "arr_iata": destination_iata,
    "limit": 5
  }
  try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    simplified_flights = []
    if "data" in data:
      for flight in data["data"]:
          simplified_flights.append({
            "airline": flight.get("airline", {}).get("name", "Unknown Airline"),
            "flight_number": flight.get("flight", {}).get("iata", "Unknown"),
            "departure_time": flight.get("departure", {}).get("estimated", "Unknown"),
            "arrival_time": flight.get("arrival", {}).get("estimated", "Unknown"),
            "status": flight.get("flight_status", "Unknown")
            })
    return simplified_flights
  except Exception as e:
     print("Error fetching flights")
     return [{"error": "Could not fetch flight data at this time."}]


@tool
def search_hotels(location:str)->list[dict]:
  """
  Searches the web for the best hotels and accommodations in a specific location.
    Args:
        location (str): The city or destination name (e.g., 'Bangkok, Thailand').
  """
  print(f"🏨 Tool Execution: Searching web for hotels in {location}...")   

  tavily_tool=TavilySearch(max_results=3,topic="general")

  try:
    query=f"best hotels to stay in {location} current prices and reviews"
    results=tavily_tool.invoke({"query":query})
    return results
  except Exception as e:
    print("Error fetching hotels")
    return [{"error": "Could not fetch hotel data at this time."}]



# Update the standalone test block at the very bottom of the file
if __name__ == "__main__":
    print("\n--- Testing Flight Tool ---")
    print(search_flights.invoke({"destination_iata": "BKK"}))
    
    print("\n--- Testing Hotel Tool ---")
    print(search_hotels.invoke({"location": "Bangkok"}))