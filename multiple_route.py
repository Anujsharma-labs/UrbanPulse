import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import *
from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV
import matplotlib.pyplot as plt
import seaborn as sns

# Data set load
df = pd.read_parquet('data/jaipur_ml_data.parquet')

print('dataset shape:', df.shape)
print(df.head())

#features

X = df[["hdist", "lat_orig", "lon_orig", "lat_dest", "lon_dest"]]
y = df["trip_duration_min"]

print("Features shape:", X.shape)
print("Target shape:", y.shape)

# test train validation split
X_temp, X_test, y_temp, y_test = train_test_split(X,y, 
        test_size=0.15, random_state=42)

X_train, X_val, y_train, y_val  = train_test_split(X_temp, y_temp,
        test_size=0.15, random_state=42)


print("Training rows:", len(X_train))
print("Validation rows:", len(X_val))
print("Testing rows:", len(X_test))


## baseline XGBoost

model = XGBRegressor(
    n_estimators = 100,
    max_depth = 6,
    learning_rate = 0.1,
    random_state = 42,
    n_jobs = -1
)

model.fit(X_train, y_train)

# prediction 
train_pred = model.predict(X_train)
val_pred = model.predict(X_val)



print("Training MAE:", mean_absolute_error(y_train, train_pred))
print("Validation MAE:", mean_absolute_error(y_val, val_pred))

print("Training R2:", r2_score(y_train, train_pred))
print("Validation R2:", r2_score(y_val, val_pred))


## hyperparameter tunning using randomsearch cv

param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [3, 5, 7],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0]
}


random_search = RandomizedSearchCV(
    estimator=XGBRegressor(
        random_state=42,
        n_jobs=1
    ),
    param_distributions=param_grid,
    n_iter=15,
    scoring="neg_mean_absolute_error",
    cv=3,
    random_state=42,
    n_jobs=-1
)


random_search.fit(X_train, y_train)

print("Best Parameters:", random_search.best_params_)
print("Best CV MAE:", -random_search.best_score_)

best_model = random_search.best_estimator_

val_pred = best_model.predict(X_val)

print("Tuned Validation MAE:",
      mean_absolute_error(y_val, val_pred))

print("Tuned Validation RMSE:",
      np.sqrt(mean_squared_error(y_val, val_pred)))

print("Tuned Validation R2:",
      r2_score(y_val, val_pred))



# Final test evaluation
best_model = random_search.best_estimator_

test_pred = best_model.predict(X_test)

print("\n--- FINAL TEST RESULTS ---")
print("Test MAE:", mean_absolute_error(y_test, test_pred))
print("Test RMSE:", np.sqrt(mean_squared_error(y_test, test_pred)))
print("Test R2:", r2_score(y_test, test_pred))


## overfitting check

# Overfitting check
train_pred = best_model.predict(X_train)
val_pred = best_model.predict(X_val)

print("\n--- OVERFITTING CHECK ---")
print("Training MAE:", mean_absolute_error(y_train, train_pred))
print("Validation MAE:", mean_absolute_error(y_val, val_pred))
print("Training R2:", r2_score(y_train, train_pred))
print("Validation R2:", r2_score(y_val, val_pred))


print("\n--- TARGET SKEWNESS ---")
print("Trip duration skewness:", y.skew())

## plot

plt.figure(figsize=(8, 5))
sns.kdeplot(data=df, x="trip_duration_min", fill=True)
plt.title("Trip Duration Distribution (KDE)")
plt.xlabel("Trip Duration (minutes)")
plt.ylabel("Density")
plt.tight_layout()
plt.show()


import os
import pickle

# Models folder create karo
os.makedirs("models", exist_ok=True)

# Trained XGBoost model save karo
with open("models/xgboost_route_model.pkl", "wb") as file:
    pickle.dump(best_model, file)

print("XGBoost model successfully saved!")
