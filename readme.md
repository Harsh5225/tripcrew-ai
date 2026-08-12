# ✈️ TripCrew AI — LangGraph Multi-Agent Travel Planner

A multi-agent travel planning system built with LangGraph. Turns a natural-language
trip request into flight suggestions, hotel options, and a day-by-day itinerary —
coordinated across four specialized agents sharing a single persistent state.

### 🛠️ Tech Stack & Dependencies

This project relies on several key libraries to orchestrate the multi-agent system, manage persistent memory, and serve the application.

**Core AI & Multi-Agent Orchestration**

* **`langgraph`**: The backbone of the project. Used to build the fan-out/fan-in parallel agent architecture and manage the `TravelState`.
* **`langchain` & `langchain-community**`: The foundational framework for building LLM applications and integrating tools.
* **`langchain-groq`**: Connects the agents to Groq's blazing-fast inference engine (powering the Llama 3 models).

**State Persistence & Database**

* **`langgraph-checkpoint-postgres`**: LangGraph's checkpointer that saves the agent state and conversation history to a PostgreSQL database.
* **`psycopg[binary]` & `psycopg-pool**`: The modern Python adapter for PostgreSQL, enabling a fast and persistent connection to the Neon cloud database.

**Search & External APIs**

* **`tavily-python` & `langchain-tavily**`: Powers the web search capabilities for the Flight, Hotel, and Itinerary agents to fetch real-time data.
* **`requests`**: Handles direct HTTP requests to external APIs (like AviationStack and Google Places).

**Backend API & Serving**

* **`fastapi`**: Used to build the web framework and API layer for the AI planner.
* **`uvicorn`**: The lightning-fast ASGI server used to run the FastAPI application.
* **`jinja2`**: Used for templating capabilities within the web serving layer.

**Travel Data & Utilities**

* **`airportsdata`**: Provides accurate lookup data for airport IATA codes, names, and locations for the Flight Agent.
* **`pycountry`**: Standardizes country codes, names, and currencies to ensure clean data parsing between APIs.
* **`python-dotenv`**: Securely loads environment variables (API keys and Database URLs) from the local `.env` file.