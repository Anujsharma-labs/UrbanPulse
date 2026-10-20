# 🚑 UrbanPulse — Emergency Route Intelligence

### *Faster Routes. Smarter Decisions. Every Second Matters.*

UrbanPulse is a smart emergency route planning application designed to help users identify road routes to hospitals, estimate travel time, and visualize journeys through an interactive map.

Built with **Python, Streamlit, SQL Server, and OSRM**, UrbanPulse combines route calculation, ETA estimation, interactive mapping, and trip history in one dashboard.

---

## ✨ Key Features

- 🗺️ **Interactive Route Visualization** — View road routes between selected pickup and destination locations.
- 🚑 **Emergency Route Planning** — Select locations and calculate a suggested driving route.
- ⏱️ **ETA Estimation** — Estimate travel duration using routing engine data.
- 📏 **Road Distance Calculation** — Get the calculated road distance in kilometers.
- 📍 **Location Selection** — Choose from predefined locations in Jaipur.
- 💾 **Trip History** — Save trip details to SQL Server and review previously saved journeys.
- 🌌 **Modern Dashboard UI** — Dark-themed interface with a background image and glass-style panels.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web dashboard |
| OSRM | Road route and travel-time estimates |
| Folium | Interactive route maps |
| Streamlit-Folium | Map integration with Streamlit |
| SQL Server | Trip history storage |
| PyODBC | Python–SQL Server connectivity |
| Requests | Routing API communication |
| Pandas | Trip history data handling |

---

## ⚙️ How It Works

1. Select a pickup location and destination.
2. UrbanPulse sends the coordinates to the OSRM routing service.
3. The routing service returns a road route, distance, and estimated duration.
4. The application displays the route, pickup/destination markers, distance, and ETA.
5. Save the trip to store its details in SQL Server.
6. View previously saved trips from the trip history section.

---

## 🖥️ Application Preview

Add a screenshot of your dashboard here:

```markdown
![UrbanPulse Dashboard](screenshots/urbanpulse_dashboard.png)
```

Create a `screenshots` folder in the repository and add your dashboard screenshot using the filename shown above.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Anujsharma-labs/UrbanPulse.git
cd UrbanPulse
```

If your repository uses a different URL or capitalization, use its actual GitHub URL.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure SQL Server

Ensure SQL Server is running and create the required database and table. Update the connection settings in `app.py` to match your local SQL Server configuration.

The application currently uses Windows Trusted Authentication with ODBC Driver 17.

### 5. Run the application

```bash
streamlit run app.py
```

Open the local URL shown in your terminal.

---

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

---

## ⚠️ Important Notes

- Route calculations use the public OSRM routing service and require an internet connection.
- ETA is an estimate returned by the routing service, not a guarantee of real-world arrival time.
- The current application uses predefined Jaipur locations.
- The current implementation does not provide live traffic analysis, ambulance-priority signals, or emergency dispatch.
- SQL Server must be configured separately; the local database connection will not automatically work on a cloud host.

---

## 🔮 Future Improvements

- Integrate live traffic information for more realistic ETA estimates.
- Expand location coverage beyond predefined locations.
- Add hospital search and nearby hospital discovery.
- Introduce ambulance-aware routing where supported by available road data and services.
- Deploy the application with a securely hosted database.
- Add trip analytics and route performance insights.

---

## 👨‍💻 Author

**Anuj Sharma**

GitHub: [@Anujsharma-labs](https://github.com/Anujsharma-labs)

---

*UrbanPulse — using technology to support smarter emergency journey planning.* 🚑