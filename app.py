import streamlit as st
import pandas as pd
import requests
import folium

from streamlit_folium import st_folium

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="UrbanPulse",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= CUSTOM UI =================
st.markdown(
    """
    <style>
    .stApp {
        background:
            linear-gradient(rgba(4, 12, 25, 0.72),
                            rgba(4, 12, 25, 0.86)),
            url("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=2000&q=90")
            center center / cover fixed no-repeat;
        color: #f4f7fb;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero, .glass-card {
        background: rgba(10, 25, 42, 0.78);
        border: 1px solid rgba(100, 220, 255, 0.35);
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(8px);
    }
    .hero h1 {
        color: white;
        font-size: 2.8rem;
        margin-bottom: 5px;
    }
    .hero p {
        color: #c9eaff;
        font-size: 1.05rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(10, 25, 42, 0.90);
        border: 1px solid rgba(100, 220, 255, 0.3);
        border-radius: 14px;
        padding: 18px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #00b89c, #00a8c8);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        min-height: 42px;
    }
    .stButton > button:hover {
        color: white;
        border: 1px solid #a3fff0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================= HERO =================
st.markdown(
    """
    <div class="hero">
        <h1>🚑 UrbanPulse</h1>
        <p>Faster Routes. Safer Journeys. Every Second Matters.</p>
        <p>⚡ Smart Routing &nbsp; • &nbsp; ⏱ Estimated ETA
        &nbsp; • &nbsp; 🏥 Emergency Support</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================= SQL CONNECTION =================
def get_connection():
    import pyodbc

    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=DESKTOP-MFO7PT7\ANUJ;"
        "DATABASE=UrbanPulse;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


# ================= LOCATION OPTIONS =================
# Sample locations. Coordinates are (latitude, longitude).
locations = {
    "SMS Hospital": (26.9124, 75.7873),
    "Jaipur Railway Station": (26.9196, 75.7878),
    "Jaipur Airport": (26.8242, 75.8122),
    "World Trade Park": (26.8530, 75.8050),
    "Sindhi Camp Bus Stand": (26.9239, 75.7990),
    "Ajmer Road": (26.9000, 75.7500),
}

# ================= OSRM ROUTING =================
def get_route(origin, destination):
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{origin[1]},{origin[0]};"
        f"{destination[1]},{destination[0]}"
    )

    response = requests.get(
        url,
        params={"overview": "full", "geometries": "geojson"},
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("No road route found for these locations.")

    route = data["routes"][0]
    return (
        route["distance"] / 1000,
        route["duration"] / 60,
        route["geometry"]["coordinates"],
    )


# ================= SAVE TRIP =================
def save_trip(origin, destination, distance, eta):
    query = """
    INSERT INTO dbo.jaipur_trip_predictions
    (distance_km, origin_lat, origin_lon,
     destination_lat, destination_lon,
     predicted_duration_min)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    with get_connection() as conn:
        conn.cursor().execute(
            query,
            float(distance),
            float(origin[0]),
            float(origin[1]),
            float(destination[0]),
            float(destination[1]),
            float(eta),
        )
        conn.commit()


# ================= TRIP FORM =================
st.markdown(
    """
    <div class="glass-card">
        <h3>📍 Plan Your Emergency Trip</h3>
        <p>Select your pickup and destination to find a road route.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    pickup_name = st.selectbox(
        "🟢 Pickup Location",
        list(locations.keys()),
        index=1,
    )

with col2:
    destination_name = st.selectbox(
        "🔴 Hospital / Destination",
        list(locations.keys()),
        index=0,
    )

if st.button("🚑 Find Route & Estimate ETA", type="primary"):
    if pickup_name == destination_name:
        st.warning("Please select two different locations.")
    else:
        try:
            origin = locations[pickup_name]
            destination = locations[destination_name]

            with st.spinner("Calculating road route..."):
                distance, eta, coordinates = get_route(origin, destination)

            st.session_state["trip"] = {
                "origin": origin,
                "destination": destination,
                "pickup_name": pickup_name,
                "destination_name": destination_name,
                "distance": distance,
                "eta": eta,
                "coordinates": coordinates,
            }
            st.session_state.pop("trip_saved", None)

        except Exception as e:
            st.error(f"Route calculation failed: {e}")


# ================= ROUTE MAP & ETA =================
if "trip" in st.session_state:
    trip = st.session_state["trip"]

    st.markdown(
        """
        <div class="glass-card">
            <h3>🗺️ Your Route</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    route_points = [(lat, lon) for lon, lat in trip["coordinates"]]

    # OpenStreetMap tiles replace CARTO tiles to avoid CARTO's API-key watermark.
    route_map = folium.Map(
        location=trip["origin"],
        zoom_start=13,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    folium.Marker(
        trip["origin"],
        tooltip="Pickup",
        popup=trip["pickup_name"],
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(route_map)

    folium.Marker(
        trip["destination"],
        tooltip="Destination",
        popup=trip["destination_name"],
        icon=folium.Icon(color="red", icon="plus"),
    ).add_to(route_map)

    folium.PolyLine(
        route_points,
        color="#00b89c",
        weight=6,
        opacity=0.95,
        tooltip="Suggested road route",
    ).add_to(route_map)

    route_map.fit_bounds(route_points)

    st_folium(
        route_map,
        use_container_width=True,
        height=460,
        key="urbanpulse_route_map",
    )

    metric1, metric2 = st.columns(2)
    metric1.metric("🛣️ Road Distance", f"{trip['distance']:.2f} km")
    metric2.metric("⏱️ Estimated Arrival", f"{trip['eta']:.1f} minutes")

    st.write(f"**Pickup:** {trip['pickup_name']}")
    st.write(f"**Destination:** {trip['destination_name']}")

    if st.button("💾 Save Your Trip"):
        try:
            save_trip(
                trip["origin"],
                trip["destination"],
                trip["distance"],
                trip["eta"],
            )
            st.success("Your trip has been saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Could not save trip: {e}")


# ================= TRIP HISTORY =================
st.divider()

st.markdown(
    """
    <div class="glass-card">
        <h3>📋 Your Trip History</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("View Your Trip History"):
    try:
        with get_connection() as conn:
            history = pd.read_sql_query(
                """
                SELECT TOP 20
                    prediction_id AS [Trip ID],
                    distance_km AS [Distance (km)],
                    predicted_duration_min AS [Estimated ETA (min)],
                    created_at AS [Created At]
                FROM dbo.jaipur_trip_predictions
                ORDER BY prediction_id DESC
                """,
                conn,
            )

        if history.empty:
            st.info("No saved trips yet.")
        else:
            st.dataframe(history, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Could not load trip history: {e}")

st.divider()
st.caption("🚑 URBANPULSE • Smart Emergency Route Planning")
