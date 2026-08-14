# ✈️ TripCrew AI — LangGraph Multi-Agent Travel Planner

![Flow Architecture](https://github.com/Harsh5225/tripcrew-ai/blob/main/Flow_Architecture.png?raw=true)

A multi-agent travel planning system built with LangGraph. Turns a natural-language
trip request into flight suggestions, hotel options, and a day-by-day itinerary —
coordinated across four specialized agents sharing a single persistent state.

### 🛠️ Tech Stack & Dependencies

This project relies on several key libraries to orchestrate the multi-agent system, manage persistent memory, and serve the application.

**Core AI & Multi-Agent Orchestration**

* **`langgraph`**: The backbone of the project. Used to build the fan-out/fan-in parallel agent architecture and manage the `TravelState`.
* **`langchain`** & **`langchain-community`**: The foundational framework for building LLM applications and integrating tools.
* **`langchain-groq`**: Connects the agents to Groq's blazing-fast inference engine (powering the Llama 3 models).

**State Persistence & Database**

* **`langgraph-checkpoint-postgres`**: LangGraph's checkpointer that saves the agent state and conversation history to a PostgreSQL database.
* **`psycopg[binary]`** & **`psycopg-pool`**: The modern Python adapter for PostgreSQL, enabling a fast and persistent connection to the Neon cloud database.

**Search & External APIs**

* **`tavily-python`** & **`langchain-tavily`**: Powers the web search capabilities for the Flight, Hotel, and Itinerary agents to fetch real-time data.
* **`requests`**: Handles direct HTTP requests to external APIs (like AviationStack and Google Places).

**Backend API & Serving**

* **`fastapi`**: Used to build the web framework and API layer for the AI planner.
* **`uvicorn`**: The lightning-fast ASGI server used to run the FastAPI application.
* **`jinja2`**: Used for templating capabilities within the web serving layer.

**Travel Data & Utilities**

* **`airportsdata`**: Provides accurate lookup data for airport IATA codes, names, and locations for the Flight Agent.
* **`pycountry`**: Standardizes country codes, names, and currencies to ensure clean data parsing between APIs.
* **`python-dotenv`**: Securely loads environment variables (API keys and Database URLs) from the local `.env` file.

---

### 🧠 Core Concepts & Architecture

**1. Parallel Multi-Agent Execution (Fan-Out / Fan-In)**
Unlike standard sequential ReAct agents, this project utilizes a parallel execution graph. The **Flight Agent** and **Hotel Agent** are triggered simultaneously from the `START` node. The graph waits for both independent network requests to resolve before moving to the **Itinerary Agent**, significantly reducing total generation time.

**2. Strict Tool Calling (Forced JSON Execution)**
Open-source models (like Llama-3) can sometimes hallucinate XML/JSON syntax when deciding *if* they should use a tool. This project implements **Strict Tool Calling** by bypassing the LLM's conversational generation step entirely. By forcing the LLM to output only within the tool schema, we eliminate `400 Bad Request` parsing errors.

**3. Global State Management (`TypedDict`)**
Instead of passing messages back and forth, all agents share a single `TravelState` dictionary. As agents complete their tasks, they append their specific JSON arrays (e.g., `flight_results`, `hotel_results`) to the global state, allowing downstream agents to access the complete context.

---

### 🔑 Key Framework Methods Used

**LangGraph Methods:**

* `StateGraph(TravelState)`: Initializes the core graph mapped to our custom state schema.
* `.add_node(name, function)`: Registers our distinct Python functions (Flight, Hotel, Itinerary) as independent agents.
* `.add_edge(START, "flight_agent")` & `.add_edge(START, "hotel_agent")`: Creates the parallel fan-out architecture.
* `.compile(checkpointer=...)`: Freezes the graph structure and attaches the PostgreSQL database for thread-level memory tracking.
* `.invoke(initial_state, config={"configurable": {"thread_id": ...}})`: Triggers the full agent workflow while tracking the specific user session.

**LangChain Methods:**

* `.bind_tools([tool], tool_choice="any")`: The critical method used to bind Python functions to the LLM and strictly force tool execution over conversational text.
* `@tool`: Decorator used in `tools.py` to seamlessly convert standard Python functions (like `search_activities`) into LLM-readable schemas with type hints and docstrings.
* `SystemMessage` & `HumanMessage`: Used to strictly define agent personas and inject the `TravelState` data into the prompts.

---

### ✨ Key Functionalities

* **Live Web Scraping & Orchestration:** The Itinerary Agent doesn't just rely on internal knowledge; it uses Tavily to search the web for the absolute latest tourist attractions and restaurant recommendations.
* **Thread Persistence:** Thanks to the Postgres checkpointer, every travel plan is saved. You can recall previous `thread_id` configurations, and the AI will remember the exact flights and hotels it found for that specific session.
* **Markdown to HTML Rendering:** The final LLM response is generated in rich Markdown, which the FastAPI backend dynamically parses into semantic HTML before serving it to the Jinja2 template.

---

### 💡 Major Learnings & Challenges Solved

* **Overcoming LLM Syntax Hallucinations:** Discovered that Llama-3 8B occasionally dropped closing brackets (e.g., `>`) when trying to generate tool calls, breaking the backend. Solved by upgrading to the `Llama-3.3-70B-versatile` model and utilizing `tool_choice="any"` for constrained decoding.
* **Parsing Complex API Responses:** Learned to properly extract nested arrays from third-party APIs. For example, Tavily returns a dictionary with metadata, so `.extend(tool_result.get("results", []))` was required to prevent the state from saving dictionary keys instead of the actual hotel data.
* **Modern FastAPI Template Handling:** Adapted to the latest Starlette/FastAPI updates by explicitly defining `request=`, `name=`, and `context=` kwargs to resolve `TypeError: unhashable type: 'dict'` errors during Jinja2 template rendering.
* **Cloud Deployment Security:** Successfully deployed the full-stack web application to Render while utilizing `.gitignore` to prevent sensitive API keys and database URLs from being exposed to the public GitHub repository.