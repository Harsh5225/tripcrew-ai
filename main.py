import os
import markdown
import uvicorn
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# Project Imports
from graph import graph, MCP_TOOLS
from checkpointer import get_async_checkpointer

# Global variable to hold our compiled LangGraph application
travel_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global travel_app
    async with AsyncExitStack() as stack:
        print("🚀 Booting up TripCrew AI Systems...")

        # 1. Connect to Neon Postgres Database
        checkpointer, db_pool = await get_async_checkpointer()
        stack.push_async_callback(db_pool.close) # Ensures safe shutdown

        # 2. Compile LangGraph with our long-term database memory
        travel_app = graph.compile(checkpointer=checkpointer)

        # 3. Start the background MCP Server
        print("🔌 Starting MCP Server...")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server.py"]
        )
        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        # 4. Load Tools dynamically for the agents to use
        tools = await load_mcp_tools(session)
        for tool in tools:
            MCP_TOOLS[tool.name] = tool
            
        print(f"✅ Systems Go! MCP Tools loaded: {list(MCP_TOOLS.keys())}")

        yield # The Web API runs while this block is paused

        print("🛑 Shutting down systems gracefully...")

# Initialize FastAPI with the lifespan manager
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    """Loads the search interface."""
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        # Match the variables your HTML expects
        context={"final_response": None, "user_query": None}
    )

@app.post("/")
async def generate_itinerary(request: Request, user_query: str = Form(...)):
    """Handles form submissions and triggers the AI graph."""
    
    # Create a dynamic thread ID based on their query for the database
    thread_id = f"web_session_{user_query[:10].replace(' ', '_').lower()}"

    print(f"🌍 Received web request: {user_query}")

    # Run the async multi-agent graph
    final_state = await travel_app.ainvoke(
        {"user_query": user_query},
        config={"configurable": {"thread_id": thread_id}}
    )

    # Parse the raw markdown into clean HTML for the webpage
    raw_markdown = final_state.get("itinerary", "Error generating itinerary.")
    html_itinerary = markdown.markdown(raw_markdown)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        # Send the generated HTML and the original query back to the page
        context={"final_response": html_itinerary, "user_query": user_query}
    )
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)