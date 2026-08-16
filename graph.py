import os
import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

# Import the MCP Client tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from state import TravelState


load_dotenv()

# We will store the dynamically loaded tools in this dictionary
# so all our agents can access them while the graph is running!
MCP_TOOLS = {}

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

async def flight_agent(state: TravelState):
    print("✈️ Flight agent running...")

    sys_msg = SystemMessage(content="You are a flight booking assistant. Extract the destination city's 3-letter IATA code from the user's query and use the search_flights tool. If you can't determine the IATA code, guess the closest major airport IATA. Do not output any conversational text, ONLY use the tool.")
    
    # Dynamically grab the tool from our MCP dictionary
    flight_tool = MCP_TOOLS["search_flights"]
    
    agent_llm = llm.bind_tools([flight_tool], tool_choice="any")

    # We must AWAIT the LLM response now
    response = await agent_llm.ainvoke([sys_msg, HumanMessage(content=state["user_query"])]) 

    flight_data = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            # We must AWAIT the tool execution over the MCP protocol
            tool_result = await flight_tool.ainvoke(tool_call["args"])
            
            # search_flights returns a list, so we extend
            if isinstance(tool_result, list):
                flight_data.extend(tool_result)
            else:
                flight_data.append(tool_result)
            
    return {"flight_results": flight_data}


async def hotel_agent(state: TravelState):
    print("🏨 Hotel agent analyzing query...")
    
    sys_msg = SystemMessage(content="You are a hotel booking assistant. Extract the destination city name from the user query and use the search_hotels tool. Do not output any conversational text, ONLY use the tool.")
    
    # Dynamically grab the tool from our MCP dictionary
    hotel_tool = MCP_TOOLS["search_hotels"]
    agent_llm = llm.bind_tools([hotel_tool], tool_choice="any")
    
    response = await agent_llm.ainvoke([sys_msg, HumanMessage(content=state["user_query"])])
    
    hotel_data = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            tool_result = await hotel_tool.ainvoke(tool_call["args"])
            
            # Append the string result
            hotel_data.append(tool_result)
            
    return {"hotel_results": hotel_data}


async def itinerary_agent(state: TravelState):
    print("📍 Itinerary agent running...")
    
    sys_msg_research = SystemMessage(content="You are a travel researcher. Extract the destination city from the user query and use the search_activities tool. Do not output conversational text, ONLY use the tool.")

    activities_tool = MCP_TOOLS["search_activities"]
    research_llm = llm.bind_tools([activities_tool], tool_choice="any")
    
    research_response = await research_llm.ainvoke([sys_msg_research, HumanMessage(content=state["user_query"])])
    
    activities_data = ""
    if research_response.tool_calls:
        for tool_call in research_response.tool_calls:
            print(f"   Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            activities_data = await activities_tool.ainvoke(tool_call["args"])

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
    final_response = await llm.ainvoke([sys_msg_writer, HumanMessage(content=drafting_prompt)])
    
    return {"itinerary": final_response.content}


async def final_response_agent(state: TravelState):
    print("💬 Final response agent running...")
    final_text = state.get("itinerary", "No itinerary was generated.")
    
    # Just to print it out beautifully in the terminal
    print("\n\n" + "="*50)
    print(final_text)
    print("="*50 + "\n\n")
    
    return {"final_response": final_text}


# --- GRAPH COMPILATION ---
graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_response_agent", final_response_agent)

# Parallel fan-out execution
graph.add_edge(START, "flight_agent")
graph.add_edge(START, "hotel_agent")

# Both must finish before Itinerary can start
graph.add_edge("flight_agent", "itinerary_agent")
graph.add_edge("hotel_agent", "itinerary_agent")

graph.add_edge("itinerary_agent", "final_response_agent")
graph.add_edge("final_response_agent", END)

