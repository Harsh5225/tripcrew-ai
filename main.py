import uuid
import markdown
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Import your compiled graph from Day 2 & 3
from graph import travel_app 

app = FastAPI(title="TripCrew AI")

# Tell FastAPI where to find our HTML files
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the home page with the search box."""
    # Explicitly define request, name, and context
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "final_response": None}
    )

@app.post("/", response_class=HTMLResponse)
async def generate_plan(request: Request, user_query: str = Form(...)):
    """Takes the form submission, runs the AI agents, and returns the result."""
    
    print(f"\n🚀 Received web request for: {user_query}")
    
    # Generate a random thread ID for this user session
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    initial_state = {
        "user_query": user_query,
        "flight_results": [],
        "hotel_results": [],
        "itinerary": "",
        "final_response": "",
        "messages": [],
    }
    
    # Run your LangGraph agents!
    result = travel_app.invoke(initial_state, config=config)
    
    # Convert the LLM's Markdown response into HTML so it renders nicely in the browser
    raw_itinerary = result.get("final_response", "No plan generated.")
    html_itinerary = markdown.markdown(raw_itinerary)
    
    # Send the result back to the HTML page
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request": request, 
            "final_response": html_itinerary, 
            "user_query": user_query
        }
    )