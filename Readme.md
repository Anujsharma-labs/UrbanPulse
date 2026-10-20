# 🚑 UrbanPulse — Emergency Route Intelligence

### *Faster Routes. Smarter Decisions. Every Second Matters.*

UrbanPulse is a smart emergency route planning application designed to simplify journey planning through interactive route visualization, road distance calculation, and estimated travel time (ETA).

Built using **Python, Streamlit, SQL Server, and OSRM**, UrbanPulse combines routing services, interactive maps, and database integration in a modern dashboard to support smarter emergency journey planning.

## 🖥️ Dashboard Preview

![UrbanPulse Dashboard](screenshots/urbanpulse_dashboard.png)

## ✨ Key Features

- 🚑 **Emergency Route Planning** — Select pickup and destination locations to find a suggested road route.
- 🗺️ **Interactive Route Map** — Visualize the route with pickup and destination markers.
- ⏱️ **ETA Estimation** — Estimate travel duration using routing service data.
- 📏 **Road Distance Calculation** — Calculate the driving distance between selected locations.
- 📍 **Location Selection** — Choose from predefined locations in Jaipur.
- 💾 **Trip History Management** — Save trip details to SQL Server and review previous journeys.
- 🌌 **Modern Dashboard UI** — Dark-themed interface with a background image and glass-style panels.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web application |
| OSRM | Road routing and travel-time estimates |
| Folium | Interactive map visualization |
| Streamlit-Folium | Integrating maps into Streamlit |
| SQL Server | Persistent trip history storage |
| PyODBC | Database connectivity |
| Pandas | Tabular data handling |
| Requests | Routing API communication |

## 🔄 How It Works

1. **Select Locations:** Choose a pickup point and destination.
2. **Calculate Route:** The application requests a driving route from OSRM.
3. **Estimate Journey:** Retrieve the road distance and estimated travel duration.
4. **Visualize Route:** Display the suggested route on an interactive map.
5. **Save Trip:** Store the trip details in SQL Server.
6. **Review History:** View previously saved trips in the dashboard.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or a compatible version
- SQL Server
- Microsoft ODBC Driver 17 for SQL Server
- Internet connection for routing and map tiles

### 1. Clone the Repository

```bash
git clone https://github.com/Anujsharma-labs/UrbanPulse.git
cd UrbanPulse
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure `requirements.txt` contains:

```text
streamlit
pandas
pyodbc
requests
folium
streamlit-folium
```

### 4. Configure SQL Server

Make sure SQL Server is running and the `UrbanPulse` database and required `dbo.jaipur_trip_predictions` table exist.

Update the database connection in `app.py` to match your local SQL Server instance. The current configuration uses Windows Trusted Authentication.

### 5. Run UrbanPulse

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal to access the dashboard.

## 📂 Project Structure

```text
UrbanPulse/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── screenshots/
    └── urbanpulse_dashboard.png
```

## 📊 Project Highlights

- Integration of a real road-routing service.
- End-to-end route calculation and interactive visualization.
- SQL Server integration for persistent trip records.
- A user-friendly dashboard built with Streamlit.
- A modular foundation for future emergency mobility features.

## 🔮 Future Enhancements

- 🚦 Live traffic integration for more realistic ETA estimates.
- 🏥 Nearby hospital discovery and expanded location coverage.
- 🚨 Ambulance-aware routing using suitable routing services and road data.
- 📈 Trip analytics and journey insights.
- ☁️ Cloud deployment with securely hosted database infrastructure.

## ⚠️ Limitations

- The current version uses predefined locations in Jaipur.
- ETA is an estimate from the routing service and is not guaranteed to reflect live traffic conditions.
- Live traffic analysis, ambulance-priority signals, and emergency dispatch are not currently implemented.
- The SQL Server connection is configured for a local environment and requires separate configuration for cloud deployment.

## 👨‍💻 Author

**Anuj Sharma**

GitHub: [@Anujsharma-labs](https://github.com/Anujsharma-labs)

---

*UrbanPulse — building smarter journeys through routing technology and data-driven applications.* 🚑
