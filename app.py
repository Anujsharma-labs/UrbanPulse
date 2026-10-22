from datetime import datetime
from urllib.parse import urlencode
import math
import os
import pickle

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="UrbanPulse | Emergency Route Planner",
    page_icon="🚑",
    layout="wide",
)

OSRM_BASE = "https://router.project-osrm.org"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANN_MODEL_PATH = os.path.join(BASE_DIR, "jaipur_model.pkl")
ANN_SCALER_PATH = os.path.join(BASE_DIR, "jaipur_scaler.pkl")
XGB_MODEL_PATH = os.path.join(
    BASE_DIR, "models", "xgboost_route_model.pkl"
)
FEATURES = ["hdist", "lat_orig", "lon_orig", "lat_dest", "lon_dest"]


@st.cache_resource
def load_pickle(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as model_file:
        return pickle.load(model_file)


def haversine_km(origin, destination):
    """Straight-line distance in km, matching the training hdist feature."""
    lat1, lon1 = map(math.radians, origin)
    lat2, lon2 = map(math.radians, destination)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def make_features(pickup, destination, hdist=None):
    # Same five feature names/order as jaipur_model.py training.
    return pd.DataFrame([{
        "hdist": haversine_km(pickup, destination) if hdist is None else hdist,
        "lat_orig": pickup[0],
        "lon_orig": pickup[1],
        "lat_dest": destination[0],
        "lon_dest": destination[1],
    }], columns=FEATURES)


@st.cache_resource
def load_models():
    return (
        load_pickle(ANN_MODEL_PATH),
        load_pickle(ANN_SCALER_PATH),
        load_pickle(XGB_MODEL_PATH),
    )


try:
    ann_model, ann_scaler, xgb_model = load_models()
except Exception as exc:
    ann_model, ann_scaler, xgb_model = None, None, None
    st.warning(f"Unable to load models: {exc}")


def predict_ann_eta(pickup, destination):
    """ANN ETA for the pickup-destination pair using the saved scaler."""
    if ann_model is None or ann_scaler is None:
        return None
    features = make_features(pickup, destination)
    scaled = ann_scaler.transform(features)
    prediction = ann_model.predict(scaled, verbose=0).flatten()[0]
    return max(0.0, float(prediction))


def score_route_with_xgb(route, pickup, destination):
    """Prototype route score. Uses route road distance as a route-specific hdist proxy.

    Important: training hdist is straight-line distance, so this is a heuristic use
    of the existing model, not a validated route-specific ETA prediction.
    """
    if xgb_model is None:
        return None
    features = make_features(pickup, destination, hdist=route["distance_km"])
    return max(0.0, float(xgb_model.predict(features)[0]))

# Approximate place-level coordinates, not verified ambulance-gate coordinates.
# Verify each marker against OpenStreetMap/official hospital entry before real-world use.
HOSPITALS = {
    "SMS Hospital": (26.905641, 75.815549),
    "Fortis Escorts Hospital": (26.846381, 75.803627),
    "Narayana Multispeciality Hospital": (26.795142, 75.824734),
    "Eternal Hospital (EHCC)": (26.840169, 75.805876),
    "Apex Hospital": (26.854751, 75.825271),
    "Jaipur Hospital": (26.892544, 75.804537),
    "Santokba Durlabhji Memorial Hospital": (26.893678, 75.812472),
    "Mahatma Gandhi Hospital": (26.769982, 75.854502),
    "Bhagwan Mahaveer Cancer Hospital": (26.863498, 75.805754),
}

if "trip_history" not in st.session_state:
    st.session_state.trip_history = []
if "pickup" not in st.session_state:
    st.session_state.pickup = None
if "ranked_hospitals" not in st.session_state:
    st.session_state.ranked_hospitals = []
if "current_routes" not in st.session_state:
    st.session_state.current_routes = []

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(rgba(7,18,36,.91), rgba(7,18,36,.94)),
    url("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=2000&q=80");
    background-size: cover; background-attachment: fixed; color: #f5f7fb; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stMetric"] { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); padding: 14px; border-radius: 14px; }
    div.stButton > button { border-radius: 10px; font-weight: 600; min-height: 2.7rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

def geocode_pickup(address: str):
    """Convert a user-entered address/landmark into (lat, lon) with Nominatim."""
    response = requests.get(
        NOMINATIM_URL,
        params={"q": address, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
        headers={"User-Agent": "UrbanPulse-Demo/1.0 (emergency-route-planning prototype)"},
        timeout=20,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise ValueError("Address not found. Try a landmark with Jaipur, Rajasthan.")
    item = results[0]
    return (float(item["lat"]), float(item["lon"])), item.get("display_name", address)


def rank_hospitals(pickup):
    """Rank hospitals by OSRM road distance using one Table API request."""
    hospital_names = list(HOSPITALS.keys())
    all_coords = [pickup] + [HOSPITALS[name] for name in hospital_names]
    coord_string = ";".join(f"{lon},{lat}" for lat, lon in all_coords)
    url = f"{OSRM_BASE}/table/v1/driving/{coord_string}"
    response = requests.get(
        url,
        params={
            "sources": "0",
            "destinations": ";".join(str(i) for i in range(1, len(all_coords))),
            "annotations": "distance,duration",
        },
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok" or not data.get("distances") or not data.get("durations"):
        raise ValueError("OSRM could not rank the hospitals.")

    distances = data["distances"][0]
    durations = data["durations"][0]
    rows = []
    for i, name in enumerate(hospital_names):
        if distances[i] is None or durations[i] is None:
            continue
        rows.append({
            "name": name,
            "lat": HOSPITALS[name][0],
            "lon": HOSPITALS[name][1],
            "distance_km": distances[i] / 1000,
            "osrm_minutes": durations[i] / 60,
        })
    return sorted(rows, key=lambda x: x["distance_km"])


def get_route(pickup, pickup_label, hospital):
    """Return all alternative OSRM routes for one pickup-to-hospital journey."""
    destination = (hospital["lat"], hospital["lon"])
    coord_string = f"{pickup[1]},{pickup[0]};{destination[1]},{destination[0]}"
    response = requests.get(
        f"{OSRM_BASE}/route/v1/driving/{coord_string}",
        params={"overview": "full", "geometries": "geojson", "alternatives": 3},
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("OSRM did not return a route for this destination.")

    routes = []
    for i, route in enumerate(data["routes"]):
        routes.append({
            "route_name": f"Route {i + 1}",
            "origin": pickup_label,
            "destination": hospital["name"],
            "origin_lat": pickup[0],
            "origin_lon": pickup[1],
            "destination_lat": destination[0],
            "destination_lon": destination[1],
            "distance_km": route["distance"] / 1000,
            "eta_min": route["duration"] / 60,
            "geometry": route["geometry"]["coordinates"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return routes


def show_route_map(route, map_key="urbanpulse_route_map"):
    center = [
        (route["origin_lat"] + route["destination_lat"]) / 2,
        (route["origin_lon"] + route["destination_lon"]) / 2,
    ]
    map_obj = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")
    points = [[lat, lon] for lon, lat in route["geometry"]]
    folium.PolyLine(
        points, color="#00d4ff", weight=6, opacity=0.9,
        tooltip=f"{route['route_name']} — OSRM driving route",
    ).add_to(map_obj)
    folium.Marker(
        [route["origin_lat"], route["origin_lon"]],
        tooltip=f"Pickup: {route['origin']}",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(map_obj)
    folium.Marker(
        [route["destination_lat"], route["destination_lon"]],
        tooltip=f"Hospital: {route['destination']}",
        icon=folium.Icon(color="red", icon="plus-sign"),
    ).add_to(map_obj)
    if points:
        map_obj.fit_bounds(points)
    st_folium(map_obj, use_container_width=True, height=460, key=map_key)


st.title("🚑 UrbanPulse")
st.caption("Emergency Hospital Finder and Route Planner")
st.subheader("1. Enter pickup location")
st.write("Enter an address, area, landmark, or place name. Example: Jaipur Railway Station, Jaipur.")

PICKUP_PRESETS = [
    "Jaipur Railway Station",
    "Jaipur International Airport",
    "World Trade Park, Jaipur",
    "Sindhi Camp Bus Stand, Jaipur",
    "Ajmer Road, Jaipur",
    "Hawa Mahal, Jaipur",
    "MI Road, Jaipur",
    "Custom address or landmark",
]

with st.form("pickup_form"):
    pickup_choice = st.selectbox("Choose a pickup location", PICKUP_PRESETS, index=0)
    custom_pickup = ""
    if pickup_choice == "Custom address or landmark":
        custom_pickup = st.text_input(
            "Enter pickup address or landmark",
            placeholder="e.g. Tonk Road, Jaipur, Rajasthan",
        )
    find_clicked = st.form_submit_button(
        "📍 Find Nearby Hospitals", type="primary", use_container_width=True
    )

if find_clicked:
    pickup_query = (
        custom_pickup.strip()
        if pickup_choice == "Custom address or landmark"
        else f"{pickup_choice}, Jaipur, Rajasthan, India"
    )
    if not pickup_query:
        st.warning("Select or enter a pickup location first.")
    else:
        try:
            with st.spinner("Finding the pickup location and ranking hospitals..."):
                pickup_coords, pickup_label = geocode_pickup(pickup_query)
                ranked = rank_hospitals(pickup_coords)
            st.session_state.pickup = {
                "coords": pickup_coords,
                "label": pickup_label,
                "query": pickup_query,
            }
            st.session_state.ranked_hospitals = ranked
            st.session_state.current_routes = []
            st.success("Pickup location found. Hospitals are ranked by road distance.")
        except requests.RequestException:
            st.error("The geocoding or routing service is currently unavailable. Please try again later.")
        except (ValueError, KeyError) as exc:
            st.error(str(exc))

pickup_state = st.session_state.pickup
ranked = st.session_state.ranked_hospitals

if pickup_state and ranked:
    st.divider()
    st.subheader("2. Choose a destination hospital")
    st.caption(f"Matched pickup location: {pickup_state['label']}")
    nearest = ranked[:3]
    remaining = ranked[3:]

    st.markdown("### ⭐ Nearest Hospitals")
    st.caption("Ranked by OSRM road distance. Live traffic is not included in this demo.")
    for i, hospital in enumerate(nearest, 1):
        col1, col2, col3 = st.columns([4, 1.4, 1.5])
        col1.markdown(f"**{i}. {hospital['name']}**")
        col2.write(f"{hospital['distance_km']:.2f} km")
        col3.write(f"~{hospital['osrm_minutes']:.0f} min*")

    st.markdown("### 🏥 All Remaining Hospitals")
    for hospital in remaining:
        col1, col2, col3 = st.columns([4, 1.4, 1.5])
        col1.write(hospital["name"])
        col2.write(f"{hospital['distance_km']:.2f} km")
        col3.write(f"~{hospital['osrm_minutes']:.0f} min*")

    options = [f"{h['name']} — {h['distance_km']:.2f} km" for h in ranked]
    selected_label = st.selectbox("Select a destination hospital", options, key="hospital_choice")
    selected_index = options.index(selected_label)
    selected_hospital = ranked[selected_index]

    if st.button("🗺️ Calculate & Compare Routes", type="primary", use_container_width=True):
        try:
            with st.spinner("Finding alternative road routes..."):
                st.session_state.current_routes = get_route(
                    pickup_state["coords"], pickup_state["label"], selected_hospital
                )
            st.success(f"{len(st.session_state.current_routes)} route option(s) mil gaye.")
        except requests.RequestException:
            st.error("The OSRM routing service is currently unavailable. Please try again.")
        except ValueError as exc:
            st.error(str(exc))

routes = st.session_state.current_routes
if routes:
    st.divider()
    st.subheader(f"3. Route Comparison: {routes[0]['destination']}")
    st.caption(f"Pickup: {routes[0]['origin']}")

    pickup_coords = (routes[0]["origin_lat"], routes[0]["origin_lon"])
    destination_coords = (routes[0]["destination_lat"], routes[0]["destination_lon"])

    # ANN predicts one ETA for the complete pickup-to-hospital trip.
    ann_eta = None
    try:
        ann_eta = predict_ann_eta(pickup_coords, destination_coords)
    except Exception as exc:
        st.warning(f"ANN ETA prediction failed: {exc}")

    if ann_eta is not None:
        st.metric("ANN Predicted Trip ETA", f"{ann_eta:.1f} min")
    else:
        st.warning(
            "ANN model or scaler files were not found. Place `jaipur_model.pkl` and `jaipur_scaler.pkl` "
            "in the same folder as `app.py`."
        )

    # Keep XGBoost ranking for this prototype, but do not expose its raw score.
    for route in routes:
        try:
            route["xgb_route_score"] = score_route_with_xgb(
                route, pickup_coords, destination_coords
            )
        except Exception:
            route["xgb_route_score"] = None

    if xgb_model is not None and all(
        route.get("xgb_route_score") is not None for route in routes
    ):
        ranked_routes = sorted(
            routes,
            key=lambda r: (r["xgb_route_score"], r["distance_km"]),
        )
        recommendation_label = "XGBoost prototype ranking"
    else:
        ranked_routes = sorted(routes, key=lambda r: r["distance_km"])
        recommendation_label = "Shortest road distance (fallback)"
        st.info("XGBoost model is unavailable. Routes are ranked by road distance instead.")

    for rank, route in enumerate(ranked_routes, start=1):
        route["xgb_rank"] = rank

    best_route = ranked_routes[0]
    st.success(f"Recommended route: {best_route['route_name']} · {recommendation_label}")

    # Route table intentionally excludes OSRM duration and XGBoost raw score.
    comparison_rows = []
    for route in ranked_routes:
        comparison_rows.append({
            "Rank": route["xgb_rank"],
            "Route": route["route_name"],
            "Road distance (km)": round(route["distance_km"], 2),
            "ANN predicted ETA (min)": round(ann_eta, 1) if ann_eta is not None else "Unavailable",
            "Recommendation": "Recommended" if route is best_route else "",
        })
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

    route_labels = [
        f"Rank {r['xgb_rank']} · {r['route_name']} · {r['distance_km']:.2f} km"
        for r in ranked_routes
    ]
    chosen_route_label = st.selectbox(
        "Select a route to view on the map",
        route_labels,
        index=0,
        key="route_map_choice",
    )
    chosen_route = ranked_routes[route_labels.index(chosen_route_label)]

    st.metric("Selected route distance", f"{chosen_route['distance_km']:.2f} km")
    if ann_eta is not None:
        st.metric("ANN predicted full-trip ETA", f"{ann_eta:.1f} min")

    google_maps_url = "https://www.google.com/maps/dir/?" + urlencode({
        "api": "1",
        "origin": f"{chosen_route['origin_lat']},{chosen_route['origin_lon']}",
        "destination": f"{chosen_route['destination_lat']},{chosen_route['destination_lon']}",
        "travelmode": "driving",
    })
    st.link_button(
        "📍 Open Pickup-to-Hospital Directions in Google Maps",
        google_maps_url,
        use_container_width=True,
    )
    show_route_map(chosen_route, map_key="urbanpulse_route_map")

    if st.button("💾 Save Selected Route to Trip History"):
        st.session_state.trip_history.insert(0, {
            "Time": chosen_route["created_at"],
            "Pickup": chosen_route["origin"],
            "Destination": chosen_route["destination"],
            "Route": chosen_route["route_name"],
            "Rank": chosen_route["xgb_rank"],
            "ANN ETA (min)": round(ann_eta, 1) if ann_eta is not None else None,
            "Distance (km)": round(chosen_route["distance_km"], 2),
        })
        st.success("Selected route saved to the current session history.")

    st.caption(
        "ANN estimates the complete pickup-to-hospital journey, not each alternative route individually. "
        "XGBoost route ranking is experimental and has not been validated for route-specific predictions. "
        "OSRM provides alternative route geometry and road distances; live traffic is not included."
    )

if st.session_state.trip_history:
    st.divider()
    st.subheader("📜 Trip History")
    history_df = pd.DataFrame(st.session_state.trip_history)
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download History CSV",
        history_df.to_csv(index=False).encode("utf-8"),
        "urbanpulse_trip_history.csv",
        "text/csv",
    )

st.divider()
st.caption(
    "UrbanPulse • Pickup locations are geocoded with OpenStreetMap Nominatim; hospital road-distance ranking "
    "and alternative route geometry are provided by OSRM. Prototype only; verify routes before real-world use."
)
