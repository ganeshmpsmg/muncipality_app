import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os

# ---------------- BASE PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(BASE_DIR, "ServreqPitt.csv")
model_path = os.path.join(BASE_DIR, "model.pkl")
vectorizer_path = os.path.join(BASE_DIR, "vectorizer.pkl")

# ---------------- LOAD DATA ----------------
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df = df[["REQUEST_TYPE"]].dropna()
else:
    print(f"Warning: {csv_path} not found. Using small fallback dataset to create model files.")
    df = pd.DataFrame(
        {
            "REQUEST_TYPE": [
                "Water leak reported on Elm Street",
                "Broken streetlight at 5th Ave",
                "Pipe burst causing flooding in basement",
                "Garbage not collected for 2 weeks",
                "Sewer smell and clogged drain near park",
            ]
        }
    )

df["label"] = df["REQUEST_TYPE"].str.contains(
    "Water|Leak|Pipe", case=False, na=False
).astype(int)

X = df["REQUEST_TYPE"]
y = df["label"]

# ---------------- TRAIN ----------------
vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
X_vec = vectorizer.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

# ---------------- SAVE ----------------
with open(model_path, "wb") as f:
    pickle.dump(model, f)

with open(vectorizer_path, "wb") as f:
    pickle.dump(vectorizer, f)

print("✅ model.pkl and vectorizer.pkl CREATED SUCCESSFULLY")
