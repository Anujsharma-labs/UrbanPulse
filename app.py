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
        "Destination": route["destination"],
        "Distance (km)": round(route["distance_km"], 2),
        "ETA (min)": round(route["eta_min"], 1),
    }
    st.session_state.trip_history.insert(0, record)


def show_route_map(route):
    center = [
        (route["origin_lat"] + route["destination_lat"]) / 2,
        (route["origin_lon"] + route["destination_lon"]) / 2,
    ]
    m = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    # OSRM GeoJSON route coordinates are [lon, lat]; Folium expects [lat, lon].
    route_points = [[lat, lon] for lon, lat in route["geometry"]]
    folium.PolyLine(
        route_points,
        color="#00d4ff",
        weight=6,
        opacity=0.9,
        tooltip="Suggested driving route",
    ).add_to(m)

    folium.Marker(
        [route["origin_lat"], route["origin_lon"]],
        tooltip=f"Pickup: {route['origin']}",
        popup=f"Pickup: {route['origin']}",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)

    folium.Marker(
        [route["destination_lat"], route["destination_lon"]],
        tooltip=f"Destination: {route['destination']}",
        popup=f"Destination: {route['destination']}",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(m)

    if route_points:
        m.fit_bounds(route_points)

    st_folium(m, use_container_width=True, height=480, key="urbanpulse_route_map")


# -------------------- HEADER --------------------
st.title("🚑 UrbanPulse")
st.caption("Emergency Route Planning Dashboard")
st.info(
    "Demo limitation: routes and ETA come from OSRM. Trip history is stored only "
    "for the current browser session and is not saved to a permanent database."
)

# -------------------- ROUTE PLANNER --------------------
st.subheader("Plan an Emergency Route")
left, right = st.columns(2)

with left:
    origin_name = st.selectbox("Pickup location", list(locations.keys()), key="origin_select")

with right:
    destination_options = [name for name in locations if name != origin_name]
    destination_name = st.selectbox(
        "Destination",
        destination_options,
        key="destination_select",
    )

plan_col, save_col, history_col = st.columns([2, 1, 1])

with plan_col:
    plan_clicked = st.button("🗺️ Calculate Route", use_container_width=True, type="primary")
with save_col:
    save_clicked = st.button("💾 Save Trip", use_container_width=True)
with history_col:
    history_clicked = st.button("📜 Show History", use_container_width=True)

if plan_clicked:
    try:
        with st.spinner("Calculating route..."):
            route = get_route(origin_name, destination_name)
        st.session_state.current_route = route
        st.success("Route calculated successfully!")
    except requests.RequestException:
        st.error("Route service is temporarily unavailable. Please try again.")
    except (ValueError, KeyError) as exc:
        st.error(f"Could not calculate route: {exc}")

if save_clicked:
    route = st.session_state.current_route
    if route is None:
        st.warning("Pehle Calculate Route button dabao, phir Save Trip.")
    else:
        # Avoid duplicate saves if Streamlit reruns after the button click.
        route_signature = (
            route["origin"],
            route["destination"],
            route["created_at"],
        )
        if st.session_state.get("last_saved_signature") == route_signature:
            st.info("Ye trip already current session ki history mein hai.")
        else:
            add_to_history(route)
            st.session_state.last_saved_signature = route_signature
            st.success("Trip current session ki history mein add ho gayi!")

if history_clicked:
    st.session_state.show_history = True

# -------------------- CURRENT ROUTE --------------------
route = st.session_state.current_route
if route:
    st.divider()
    st.subheader(f"Route: {route['origin']} → {route['destination']}")
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Distance", f"{route['distance_km']:.2f} km")
    metric2.metric("Estimated travel time", f"{route['eta_min']:.1f} min")
    metric3.metric("Route service", "OSRM")

    show_route_map(route)

# -------------------- HISTORY --------------------
if st.session_state.get("show_history", False):
    st.divider()
    st.subheader("📜 Trip History")
    if st.session_state.trip_history:
        history_df = pd.DataFrame(st.session_state.trip_history)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        csv_data = history_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download History CSV",
            data=csv_data,
            file_name="urbanpulse_trip_history.csv",
            mime="text/csv",
        )
        if st.button("🧹 Clear Session History"):
            st.session_state.trip_history = []
            st.session_state.show_history = True
            st.rerun()
    else:
        st.info("Abhi history empty hai. Route calculate karke Save Trip dabao.")

st.divider()
st.caption("UrbanPulse demo • Routes/ETAs are estimates, not live traffic or ambulance-priority routing.")
