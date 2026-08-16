import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# Load API keys
load_dotenv()

async def main():
    print("🔌 1. Booting up the MCP Server connection...")
    
    # Define how the client should start the server in the background
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_server.py"]
    )

    # Open the STDIO connection to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the protocol session
            await session.initialize()
            
            print("✅ Connection established! Fetching tools...")
            
            # 🪄 THE MAGIC: Dynamically load tools from the server
            tools = await load_mcp_tools(session)
            print(f"🛠️ Tools discovered: {[t.name for t in tools]}")
            
            # Initialize our Groq LLM
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            
            # Bind the discovered tools to the LLM
            llm_with_tools = llm.bind_tools(tools, tool_choice="any")
            
            print("\n🧠 2. Asking the AI to plan a quick query...")
            user_query = "Find me some flights to BOM (Mumbai)"
            print(f"User: {user_query}")
            
            # Trigger the AI
            response = await llm_with_tools.ainvoke(user_query)
            
            print("\n🤖 3. AI Decision (Tool Call generated):")
            for tool_call in response.tool_calls:
                print(f"Tool Name: {tool_call['name']}")
                print(f"Arguments: {tool_call['args']}")

if __name__ == "__main__":
    # MCP requires asynchronous execution, so we use asyncio.run
    asyncio.run(main())