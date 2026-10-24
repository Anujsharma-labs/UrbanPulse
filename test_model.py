
import pandas as pd
from pathlib import Path
from xgboost import XGBRanker
from sklearn.model_selection import GroupShuffleSplit

# 1. Dataset load karo

BASE_DIR = Path(__file__).resolve().parent.parent

data = pd.read_csv(
    BASE_DIR / "data" / "route_training_data.csv"
)

features = [
    "route_distance_km",
    "straight_line_km",
    "detour_ratio",
    "num_turns"
]

print("Total routes:", len(data))
print("Total trips:", data["trip_id"].nunique())

# 2. Check karo: har trip mein 2 routes aur ek best route hai

for trip_id, routes in data.groupby("trip_id"):
    if len(routes) != 2 or routes["is_best_route"].sum() != 1:
        raise ValueError("Kisi trip ka data sahi nahi hai!")

# 3. Data ko training aur testing mein divide karo

split = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_index, test_index = next(
    split.split(data, groups=data["trip_id"])
)

train_data = data.iloc[train_index].copy()
test_data = data.iloc[test_index].copy()

# 4. Training data mein se validation data alag karo

split2 = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

train_index2, val_index = next(
    split2.split(train_data, groups=train_data["trip_id"])
)

fit_data = train_data.iloc[train_index2].copy()
val_data = train_data.iloc[val_index].copy()

# 5. Har trip ke routes ko saath rakho

fit_data = fit_data.sort_values("trip_id").reset_index(drop=True)
val_data = val_data.sort_values("trip_id").reset_index(drop=True)
test_data = test_data.sort_values("trip_id").reset_index(drop=True)

X_train = fit_data[features]
y_train = fit_data["is_best_route"].astype(int)

X_val = val_data[features]
y_val = val_data["is_best_route"].astype(int)

X_test = test_data[features]

# Har trip mein 2 routes hain
train_groups = [2] * fit_data["trip_id"].nunique()
val_groups = [2] * val_data["trip_id"].nunique()

print("Training trips:", len(train_groups))
print("Validation trips:", len(val_groups))
print("Testing trips:", test_data["trip_id"].nunique())

# 6. XGBoost Ranking model train karo

model = XGBRanker(
    objective="rank:pairwise",
    eval_metric="ndcg",
    n_estimators=500,
    learning_rate=0.03,
    max_depth=2,
    min_child_weight=1,
    reg_alpha=0.5,
    reg_lambda=5,
    subsample=0.8,
    colsample_bytree=0.8,
    early_stopping_rounds=30,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train,
    group=train_groups,
    eval_set=[(X_val, y_val)],
    eval_group=[val_groups],
    verbose=False
)

print("Best iteration:", model.best_iteration)

# 7. Model se routes ke scores nikalo

train_scores = model.predict(X_train)
val_scores = model.predict(X_val)
test_scores = model.predict(X_test)

# 8. Check karo model ne kitne trips mein sahi route chuna

def check_accuracy(data, scores):

    result = data[["trip_id", "is_best_route"]].copy()
    result["score"] = scores

    correct = 0
    total = 0

    for trip_id, routes in result.groupby("trip_id"):

        # Jis route ka score zyada hai, model usko choose karega
        chosen_route = routes.loc[routes["score"].idxmax()]

        if chosen_route["is_best_route"] == 1:
            correct += 1

        total += 1

    accuracy = correct / total if total > 0 else 0

    return correct, total, accuracy


train_correct, train_total, train_accuracy = check_accuracy(
    fit_data, train_scores
)

val_correct, val_total, val_accuracy = check_accuracy(
    val_data, val_scores
)

test_correct, test_total, test_accuracy = check_accuracy(
    test_data, test_scores
)

# 9. Results print karo

print("\n===== ROUTE SELECTION RESULTS =====")

print(
    f"Training Accuracy: {train_accuracy:.1%} "
    f"({train_correct}/{train_total})"
)

print(
    f"Validation Accuracy: {val_accuracy:.1%} "
    f"({val_correct}/{val_total})"
)

print(
    f"Testing Accuracy: {test_accuracy:.1%} "
    f"({test_correct}/{test_total})"
)

print("\nModel testing complete!")



import pickle

# Model ko pickle file mein save karo
model_path = BASE_DIR / "models" / "xgb_ranker.pkl"

model_path.parent.mkdir(parents=True, exist_ok=True)

with open(model_path, "wb") as file:
    pickle.dump(model, file)

print("XGBRanker model saved successfully!")
print("Saved at:", model_path)