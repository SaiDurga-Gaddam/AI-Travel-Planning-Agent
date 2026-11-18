import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
st.set_page_config(page_title="AI Travel Planning Agent", page_icon="✈️", layout="wide")

def client():
    key = os.getenv("GROQ_API_KEY", "")
    try:
        key = st.secrets.get("GROQ_API_KEY", key)
    except Exception:
        pass
    if not key:
        st.error("Set GROQ_API_KEY in .env or Streamlit Secrets.")
        st.stop()
    return Groq(api_key=key)

def ask(prompt, system):
    result = client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
        temperature=0.5
    )
    return result.choices[0].message.content

def create_plan(origin, destination, days, people, budget, interests, style, needs):
    system = "You are a practical travel planning assistant. Clearly label estimates and uncertainty. Never claim live availability."
    places = ask(f"Suggest attractions and experiences in {destination} for interests: {interests}. Travel style: {style}. Group nearby places. Do not claim live opening hours or prices.", system)
    costs = ask(f"Estimate a budget for {people} traveler(s), {days} days, from {origin or 'unspecified origin'} to {destination}. Total budget: {budget}. Interests: {interests}; style: {style}. Break down transport, stay, food, local travel and activities. State assumptions and label all costs as estimates. Do not invent live prices.", system)
    itinerary = ask(f"Create a practical {days}-day day-wise itinerary for {destination}, for {people} travelers. Budget: {budget}. Interests: {interests}. Style: {style}. Special needs: {needs or 'none'}. Use these suggested places:\n{places}\nInclude morning, afternoon and evening. Keep nearby places together. No live availability or exact current prices.", system)
    return places, costs, itinerary

st.title("✈️ AI Travel Planning Agent")
st.write("Plan a personalized trip with destination ideas, estimated costs and a day-wise itinerary.")

with st.sidebar:
    st.header("Trip details")
    origin = st.text_input("Starting city", "Hyderabad")
    destination = st.text_input("Destination", placeholder="e.g. Goa")
    days = st.number_input("Duration (days)", 1, 30, 3)
    people = st.number_input("Number of travelers", 1, 20, 2)
    budget = st.text_input("Total budget", "₹20,000")
    interests = st.multiselect("Interests", ["Nature", "Beaches", "Adventure", "History", "Food", "Shopping", "Culture", "Family activities"], default=["Nature", "Food"])
    style = st.selectbox("Travel style", ["Budget", "Balanced", "Comfort", "Luxury"])
    needs = st.text_area("Special requirements", placeholder="e.g. vegetarian food, children, avoid long walks")

st.info("Agent workflow: attraction discovery → budget estimation → itinerary planning.")
if st.button("Plan My Trip", type="primary", use_container_width=True):
    if not destination.strip():
        st.warning("Enter a destination.")
    else:
        with st.spinner("Travel agent is preparing your plan..."):
            try:
                p, b, i = create_plan(origin, destination, int(days), int(people), budget, ", ".join(interests) or "general sightseeing", style, needs)
                st.session_state.trip = {"places":p, "budget":b, "itinerary":i, "destination":destination}
            except Exception as e:
                st.error(f"Could not create plan: {e}")

if "trip" in st.session_state:
    trip = st.session_state.trip
    st.success(f"Trip plan for {trip['destination']} is ready.")
    t1, t2, t3, t4 = st.tabs(["Itinerary", "Budget", "Places", "Ask Agent"])
    with t1:
        st.markdown(trip["itinerary"])
    with t2:
        st.markdown(trip["budget"])
    with t3:
        st.markdown(trip["places"])
    with t4:
        question = st.text_input("Request a change", placeholder="Make this trip more budget-friendly")
        if st.button("Ask Travel Agent"):
            if question:
                with st.spinner("Updating travel advice..."):
                    st.markdown(ask(f"Current itinerary:\n{trip['itinerary']}\nBudget:\n{trip['budget']}\nUser request: {question}. Suggest practical changes.", "You are a travel planning agent. Do not claim live bookings or availability."))
    st.download_button("Download trip plan", f"# {trip['destination']} Trip Plan\n\n## Itinerary\n{trip['itinerary']}\n\n## Budget\n{trip['budget']}\n\n## Places\n{trip['places']}", "travel_plan.md", "text/markdown")

st.caption("This app does not book flights or hotels or access live inventory. Verify prices, schedules, safety advice and travel requirements before booking.")
