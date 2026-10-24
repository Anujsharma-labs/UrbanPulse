
# UrbanPulse - XGBoost Route Selection

import pandas as pd
import requests
import math
import time
from pathlib import Path

from xgboost import XGBClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# 1. Dataset load karo

BASE_DIR = Path(__file__).resolve().parent.parent

df = pd.read_parquet(
    BASE_DIR / "data" / "jaipur_ml_data.parquet"
)

df = df.dropna(
    subset=["lat_orig", "lon_orig", "lat_dest", "lon_dest"]
)

df = df.drop_duplicates(
    subset=["lat_orig", "lon_orig", "lat_dest", "lon_dest"]
).head(1000)

# Dataset mein time column dhoondo
time_column = None

for column in ["pickup_datetime", "start_time", "pickup_time",
               "tpep_pickup_datetime", "trip_start_timestamp"]:
    if column in df.columns:
        time_column = column
        break

if time_column is not None:
    df[time_column] = pd.to_datetime(
        df[time_column], errors="coerce"
    )

    df["pickup_hour"] = df[time_column].dt.hour

training_data = []

# 2. OSRM se routes collect karo

for trip_id, row in df.reset_index(drop=True).iterrows():

    lat1 = row["lat_orig"]
    lon1 = row["lon_orig"]
    lat2 = row["lat_dest"]
    lon2 = row["lon_dest"]

    # Straight-line distance

    lat1r, lon1r, lat2r, lon2r = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    a = (
        math.sin((lat2r - lat1r) / 2) ** 2
        + math.cos(lat1r) * math.cos(lat2r)
        * math.sin((lon2r - lon1r) / 2) ** 2
    )

    straight_km = 6371 * 2 * math.asin(
        math.sqrt(max(0, min(1, a)))
    )

    if straight_km < 0.1:
        continue

    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
    )

    try:
        response = requests.get(
            url,
            params={
                "alternatives": "true",
                "overview": "full",
                "steps": "true",
                "geometries": "geojson"
            },
            timeout=20
        )

        response.raise_for_status()
        routes = response.json().get("routes", [])

    except requests.RequestException:
        print("Route request failed. Skipping trip.")
        continue

    if len(routes) < 2:
        continue

    # Sabse kam OSRM duration wala route best hai

    best_index = 0

    for i in range(len(routes)):
        if routes[i]["duration"] < routes[best_index]["duration"]:
            best_index = i

    # Har route ka data save karo

    for i, route in enumerate(routes):

        road_km = route["distance"] / 1000

        # Route geometry se approximate turns count karo
        coordinates = route["geometry"]["coordinates"]
        num_turns = 0

        for j in range(1, len(coordinates) - 1):

            lon_a, lat_a = coordinates[j - 1]
            lon_b, lat_b = coordinates[j]
            lon_c, lat_c = coordinates[j + 1]

            angle1 = math.degrees(math.atan2(
                lat_b - lat_a, lon_b - lon_a
            ))

            angle2 = math.degrees(math.atan2(
                lat_c - lat_b, lon_c - lon_b
            ))

            angle_change = abs(angle2 - angle1)

            if angle_change > 180:
                angle_change = 360 - angle_change

            if angle_change > 30:
                num_turns += 1

        route_data = {
            "trip_id": trip_id,
            "route_distance_km": road_km,
            "straight_line_km": straight_km,
            "detour_ratio": road_km / straight_km,
            "num_turns": num_turns,
            'osrm_duration': route['duration']/10,
            "is_best_route": int(i == best_index)
        }

        # Pickup hour tabhi add hoga jab valid time available ho
        if time_column is not None and pd.notna(row[time_column]):
            route_data["pickup_hour"] = int(row["pickup_hour"])

        training_data.append(route_data)

    time.sleep(0.2)


# 3. Training data ready karo

data = pd.DataFrame(training_data)

# Training data save karo
data.to_csv(
    BASE_DIR / "data" / "route_training_data.csv",
    index=False
)

print("Training data saved successfully!")

if data.empty or data["is_best_route"].nunique() < 2:
    raise ValueError(
        "Enough alternative routes nahi mile. Training nahi ho sakti."
    )

print("Total route samples:", len(data))

print("\nClass distribution:")
print(data["is_best_route"].value_counts())

# 4. Features aur target

features = [
    "route_distance_km",
    "straight_line_km",
    "detour_ratio",
    "num_turns"
]

if "pickup_hour" in data.columns:
    features.append("pickup_hour")

X = data[features]
y = data["is_best_route"]

print("\nFeatures used:", features)

# 5. Group split - same rakha hai

split = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_index, test_index = next(
    split.split(X, y, groups=data["trip_id"])
)

X_train = X.iloc[train_index]
X_test = X.iloc[test_index]

y_train = y.iloc[train_index]
y_test = y.iloc[test_index]

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# 6. Model train karo

# model = XGBClassifier(
#     n_estimators=100,
#     max_depth=3,
#     learning_rate=0.1,
#     eval_metric="logloss",
#     random_state=42
# )

# model.fit(X_train, y_train)

# # 7. Predictions

# train_pred = model.predict(X_train)
# test_pred = model.predict(X_test)

# # 8. Training metrics

# print("\n===== TRAINING METRICS =====")

# print("Accuracy:", round(
#     accuracy_score(y_train, train_pred), 3
# ))

# print("F1-score:", round(
#     f1_score(y_train, train_pred, zero_division=0), 3
# ))

# # 9. Testing metrics

# print("\n===== TESTING METRICS =====")

# print("Accuracy:", round(
#     accuracy_score(y_test, test_pred), 3
# ))

# print("Precision:", round(
#     precision_score(y_test, test_pred, zero_division=0), 3
# ))

# print("Recall:", round(
#     recall_score(y_test, test_pred, zero_division=0), 3
# ))

# print("F1-score:", round(
#     f1_score(y_test, test_pred, zero_division=0), 3
# ))

# print("\nConfusion Matrix:")
# print(confusion_matrix(y_test, test_pred))

# print("\nClassification Report:")
# print(classification_report(
#     y_test, test_pred, zero_division=0
# ))

# # 10. Feature importance

# print("\n===== FEATURE IMPORTANCE =====")

# importance = pd.DataFrame({
#     "Feature": X.columns,
#     "Importance": model.feature_importances_
# })

# print(
#     importance.sort_values(
#         by="Importance", ascending=False
#     ).to_string(index=False)
# )

# print("\nTraining and evaluation complete!")




# # 6. Random Forest model banao aur train karo

# from sklearn.ensemble import RandomForestClassifier

# model = RandomForestClassifier(
#     n_estimators=100,
#     max_depth=5,
#     random_state=42,
#     class_weight="balanced"
# )

# model.fit(X_train, y_train)

# # 7. Predictions

# train_pred = model.predict(X_train)
# test_pred = model.predict(X_test)

# # 8. Training metrics

# print("\n===== RANDOM FOREST TRAINING METRICS =====")

# print("Accuracy:", round(
#     accuracy_score(y_train, train_pred), 3
# ))

# print("F1-score:", round(
#     f1_score(y_train, train_pred, zero_division=0), 3
# ))

# # 9. Testing metrics

# print("\n===== RANDOM FOREST TESTING METRICS =====")

# print("Accuracy:", round(
#     accuracy_score(y_test, test_pred), 3
# ))

# print("Precision:", round(
#     precision_score(y_test, test_pred, zero_division=0), 3
# ))

# print("Recall:", round(
#     recall_score(y_test, test_pred, zero_division=0), 3
# ))

# print("F1-score:", round(
#     f1_score(y_test, test_pred, zero_division=0), 3
# ))

# print("\nConfusion Matrix:")
# print(confusion_matrix(y_test, test_pred))

# print("\nClassification Report:")
# print(classification_report(
#     y_test, test_pred, zero_division=0
# ))

# # 10. Feature importance

# print("\n===== FEATURE IMPORTANCE =====")

# importance = pd.DataFrame({
#     "Feature": X_train.columns,
#     "Importance": model.feature_importances_
# })

# print(
#     importance.sort_values(
#         by="Importance",
#         ascending=False
#     ).to_string(index=False)
# )

# print("\nRandom Forest training and evaluation complete!")
