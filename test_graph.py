from graph import travel_app
config={"configurable":{"thread_id": "test-session-1"}}

initial_state = {
    "user_query": "5 days in Goa, December",
    "flight_results": [],
    "hotel_results": [],
    "itinerary": "",
    "final_response": "",
    "messages": [],
}

print(" Starting parallel graph execution...\n")

result = travel_app.invoke(initial_state, config=config)

print("\n✅ Execution complete. Final State saved to Neon:")
print(f"User Query: {result.get('user_query')}")
print(f"Flights Found: {result.get('flight_results')}")
print(f"Hotels Found: {result.get('hotel_results')}")
print(f"Final Response: {result.get('final_response')}")