from langgraph.graph import StateGraph, START,END
from state import TravelState
from checkpointer import get_checkpointer


def flight_agent(state: TravelState):
    print("✈️ Flight agent running...")
    return {"flight_results": [{"airline": "Placeholder Airlines", "price": 450}]}

def hotel_agent(state: TravelState):
    print("🏨 Hotel agent running...")
    return {"hotel_results": [{"name": "Placeholder Hotel", "price": 120}]}

def itinerary_agent(state: TravelState):
    print("📍 Itinerary agent running...")
    # Itinerary agent needs both flight and hotel info to build the plan
    return {"itinerary": "Day 1: Fly in. Check into hotel. Day 2: Explore."}

def final_response_agent(state: TravelState):
    print("💬 Final response agent running...")
    return {"final_response": f"Trip plan ready for: {state['user_query']}"}

graph=StateGraph(TravelState)

graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("itinerary_agent",itinerary_agent)
graph.add_node("final_response_agent",final_response_agent)

# Flight and Hotel run at the SAME time from START
graph.add_edge(START,"flight_agent")
graph.add_edge(START,"hotel_agent")

# Both must finish before Itinerary can start
graph.add_edge("flight_agent", "itinerary_agent")
graph.add_edge("hotel_agent", "itinerary_agent")

graph.add_edge("itinerary_agent", "final_response_agent")
graph.add_edge("final_response_agent", END)

checkpointer = get_checkpointer()
travel_app = graph.compile(checkpointer=checkpointer)