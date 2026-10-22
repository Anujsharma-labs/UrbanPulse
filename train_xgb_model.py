
import pandas as pd
import numpy as np
import time

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# 1. Load cleaned dataset
ROOT = Path(__file__).resolve().parents[1]
df = pd.read_parquet(ROOT / "data" / "urbanpulse_clean.parquet")

# 2. Same outlier filter used in previous ML work
df = df[df["trip_duration_min"] <= 300].copy()

# 2.5
df["tpep_pickup_datetime"] = pd.to_datetime(
    df["tpep_pickup_datetime"]
)

df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour

# 3. Features and target
X = df[
    ["trip_distance", "pickup_hour", "PULocationID", "DOLocationID"]
].copy()

y = df["trip_duration_min"].copy()

# 4. Same split settings as previous experiments
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 5. Encode locations as categories
preprocessor = ColumnTransformer(
    transformers=[
        (
            "locations",
            OneHotEncoder(handle_unknown="ignore"),
            ["PULocationID", "DOLocationID"],
        )
    ],
    remainder="passthrough",
)

# 6. XGBoost model
xgb = XGBRegressor(
    n_estimators=300,
    max_depth=8,
    learning_rate=0.08,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    eval_metric="mae",
    tree_method="hist",
    random_state=42,
    n_jobs=-1,
)

model = Pipeline([
    ("preprocessing", preprocessor),
    ("regression", xgb),
])

# 7. Train and measure time
print("Training XGBoost... please wait!")
start = time.time()
model.fit(X_train, y_train)
print(f"Training time: {(time.time() - start) / 60:.2f} minutes")

# 8. Evaluate
predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

print("\n===== XGBOOST RESULTS =====")
print(f"MAE  : {mae:.3f} minutes")
print(f"RMSE : {rmse:.3f} minutes")
print(f"R2   : {r2:.4f} ({r2 * 100:.2f}%)")

# 9. Save model
import pickle

output_path = ROOT / "urbanpulse_xgboost.pkl"
with open(output_path, "wb") as file:
    pickle.dump(model, file)

print(f"\nModel saved at: {output_path}")
