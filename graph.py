import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tools import search_flights, search_hotels, search_activities
from langgraph.graph import StateGraph, START,END
from state import TravelState
from checkpointer import get_checkpointer


# graph.py

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def flight_agent(state: TravelState):
    print("✈️ Flight agent running...")

    #  system prompt
    sys_msg = SystemMessage(content="You are a flight booking assistant. Extract the destination city's 3-letter IATA code from the user's query and use the search_flights tool. If you can't determine the IATA code, guess the closest major airport IATA. Do not output any conversational text, ONLY use the tool.")
    
    # FORCING the tool choice here
    agent_llm = llm.bind_tools([search_flights], tool_choice="any")

    response = agent_llm.invoke([sys_msg, HumanMessage(content=state["user_query"])]) 

    flight_data = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            tool_result = search_flights.invoke(tool_call["args"])
            flight_data.extend(tool_result)
            
    return {"flight_results": flight_data}

def hotel_agent(state: TravelState):
    print("🏨 Hotel agent analyzing query...")
    
    # Tightened system prompt
    sys_msg = SystemMessage(content="You are a hotel booking assistant. Extract the destination city name from the user query and use the search_hotels tool. Do not output any conversational text, ONLY use the tool.")
    
    # FORCING the tool choice here
    agent_llm = llm.bind_tools([search_hotels], tool_choice="any")
    
    response = agent_llm.invoke([sys_msg, HumanMessage(content=state["user_query"])])
    
    hotel_data = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            tool_result = search_hotels.invoke(tool_call["args"])
            hotel_data.extend(tool_result)
            
    return {"hotel_results": hotel_data}


def itinerary_agent(state: TravelState):
    print("📍 Itinerary agent running...")
    # Itinerary agent needs both flight and hotel info to build the plan
    sys_msg_research = SystemMessage(content="You are a travel researcher. Extract the destination city from the user query and use the search_activities tool. Do not output conversational text, ONLY use the tool.")

    research_llm = llm.bind_tools([search_activities], tool_choice="any")
    research_response = research_llm.invoke([sys_msg_research, HumanMessage(content=state["user_query"])])
    
    activities_data = ""
    if research_response.tool_calls:
        for tool_call in research_response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            activities_data = search_activities.invoke(tool_call["args"])

    print("📝 Drafting the day-by-day itinerary...")
    
    sys_msg_writer = SystemMessage(content="You are an expert, enthusiastic travel planner. Create a detailed day-by-day itinerary using the provided flights, hotels, and activities. Format the response beautifully using Markdown headings and bullet points.")

    drafting_prompt = f"""
    User Request: {state['user_query']}
    
    [AVAILABLE FLIGHTS]
    {state['flight_results']}
    
    [HOTEL OPTIONS]
    {state['hotel_results']}
    
    [THINGS TO DO]
    {activities_data}
    
    Please write a comprehensive itinerary. Recommend a specific hotel from the options, include flight times, and plan out the daily activities.
    """
    final_response = llm.invoke([sys_msg_writer, HumanMessage(content=drafting_prompt)])
    
    return {"itinerary": final_response.content}

def final_response_agent(state: TravelState):
    print("💬 Final response agent running...")
    
    final_text = state.get("itinerary", "No itinerary was generated.")
    
    return {"final_response": final_text}

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