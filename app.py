import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(
    page_title="UrbanPulse | Emergency Route Planner",
    page_icon="🚑",
    layout="wide",
)

# -------------------- SESSION STATE --------------------
if "trip_history" not in st.session_state:
    st.session_state.trip_history = []

if "current_route" not in st.session_state:
    st.session_state.current_route = None

# -------------------- LOCATIONS --------------------
locations = {
    "SMS Hospital": (26.9124, 75.7873),
    "Jaipur Railway Station": (26.9196, 75.7878),
    "Jaipur Airport": (26.8242, 75.8122),
    "World Trade Park": (26.8530, 75.8050),
    "Sindhi Camp Bus Stand": (26.9239, 75.7990),
    "Ajmer Road": (26.9000, 75.7500),
}

# -------------------- STYLING --------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
          linear-gradient(rgba(7, 18, 36, 0.86), rgba(7, 18, 36, 0.90)),
          url("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=2000&q=80");
        background-size: cover;
        background-attachment: fixed;
        color: #f5f7fb;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        padding: 14px;
        border-radius: 14px;
    }
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 2.7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- HELPERS --------------------
def get_route(origin_name, destination_name):
    """Get a driving route from OSRM. Coordinates are (lat, lon)."""
    origin = locations[origin_name]
    destination = locations[destination_name]

    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}"
    params = {"overview": "full", "geometries": "geojson"}

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("OSRM did not return a route for these locations.")

    route = data["routes"][0]
    return {
        "origin": origin_name,
        "destination": destination_name,
        "origin_lat": origin[0],
        "origin_lon": origin[1],
        "destination_lat": destination[0],
        "destination_lon": destination[1],
        "distance_km": route["distance"] / 1000,
        "eta_min": route["duration"] / 60,
        "geometry": route["geometry"]["coordinates"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def add_to_history(route):
    """Store trips only in this user's current Streamlit session."""
    record = {
        "Time": route["created_at"],
        "Pickup": route["origin"],
