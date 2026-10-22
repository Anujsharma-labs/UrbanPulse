# 🚑 UrbanPulse — Emergency Hospital Finder & Route Planner

UrbanPulse is a machine learning-based emergency route planning prototype designed to help users identify nearby hospitals, compare alternative driving routes, and estimate travel time.

## ✨ Features

- **Pickup Location Search:** Enter a location, address, or landmark.
- **Nearby Hospital Finder:** Identify and rank hospitals by road distance.
- **Alternative Route Comparison:** Retrieve available driving routes using OSRM.
- **ANN-Based ETA Prediction:** Predict the estimated travel time for the complete pickup-to-hospital journey.
- **XGBoost Route Ranking:** Experimentally rank alternative routes using the existing trained model.
- **Interactive Maps:** Visualize selected routes using Folium and OpenStreetMap.
- **Google Maps Integration:** Open pickup-to-hospital directions.
- **Trip History:** Save selected routes and export trip history as CSV.

## 🛠️ Tech Stack

- Python
- Streamlit
- TensorFlow / Keras
- XGBoost
- Pandas and NumPy
- Scikit-learn
- Folium and Streamlit-Folium
- OpenStreetMap, Nominatim and OSRM

## 🧠 Machine Learning Models

### Artificial Neural Network (ANN)
Predicts the complete trip duration using pickup and destination coordinates and straight-line distance (`hdist`).

### XGBoost Regressor
Uses the same five input features for travel-duration prediction. In this prototype, it is experimentally used to rank alternative routes.

**Note:** The current models were trained on trip-level data rather than individual alternative-route data. Therefore, route-specific ranking has not been independently validated.

## 📁 Project Structure

```text
UrbanPulse/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── jaipur_model.pkl
├── jaipur_scaler.pkl
├── data/
│   └── jaipur_ml_data.parquet
├── models/
│   └── xgboost_route_model.pkl
└── src/
    └── multiple_route.py
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd UrbanPulse
```

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

### 4. Run the application

```bash
streamlit run app.py
```

Ensure that the trained model files are present at the paths expected by `app.py`.

## 📊 Model Evaluation

The XGBoost model achieved the following results on the held-out test dataset:

- **MAE:** Approximately 1.39 minutes
- **RMSE:** Approximately 2.10 minutes
- **R² Score:** Approximately 96.47%

These results describe the existing trip-duration prediction task. They do not establish the accuracy of alternative-route ranking.

## ⚠️ Limitations

- Live traffic conditions are not included.
- Alternative routes depend on OSRM availability.
- Hospital coordinates are approximate and should be verified.
- Ambulance-specific restrictions and road closures are not verified.
- Route-specific ETA and ranking require further validation.

UrbanPulse is an educational portfolio prototype and is not intended to replace verified emergency dispatch or navigation systems.

## 👨‍💻 Project Goal

To demonstrate the integration of machine learning, geospatial routing, interactive maps, and a web-based interface in an emergency hospital route planning prototype.
