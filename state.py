from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class TravelState(TypedDict):
    user_query: str
    flight_results: list[dict]
    hotel_results: list[dict]
    itinerary: str
    final_response: str
    messages: Annotated[list[BaseMessage], add_messages]
