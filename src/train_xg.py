import pandas as pd
import numpy as np
import requests
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss
import os

BASE_URL = "https://premier.72-60-245-2.sslip.io"

def fetch_shots():
    """Fetches all shots from the API."""
    print("Fetching shots...")
    # Using the /events query with is_shot=true
    # The API seems to return JSON by default
    resp = requests.get(f"{BASE_URL}/events?is_shot=true&limit=10000")
    data = resp.json()
    shots = pd.DataFrame(data['events'])
    print(f"Total shots fetched: {len(shots)}")
    return shots

def calculate_features(df):
    """Calculates distance and angle from (x, y) coordinates."""
    # Pitch is 100x100, goal center is at (100, 50)
    df['dist'] = np.sqrt((100 - df['x'])**2 + (50 - df['y'])**2)
    # Avoid division by zero
    df['angle'] = np.arctan(np.abs(50 - df['y']) / np.maximum(100 - df['x'], 0.1))
    # Convert angle to degrees for interpretability (optional)
    df['angle_deg'] = np.degrees(df['angle'])
    
    # Target variable
    df['goal'] = df['is_goal'].astype(int)
    
    return df

def train_xg_model(df):
    """Trains a Logistic Regression model for xG."""
    X = df[['dist', 'angle']]
    y = df['goal']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    probs = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)
    
    print(f"xG Model Trained. AUC-ROC: {auc:.3f}, Brier Score: {brier:.3f}")
    
    return model

if __name__ == "__main__":
    shots_raw = fetch_shots()
    shots_feat = calculate_features(shots_raw)
    
    # Remove outliers or invalid shots (e.g., from very far back if they are errors)
    shots_feat = shots_feat[shots_feat['x'] > 50] # Only shots in attacking half
    
    xg_model = train_xg_model(shots_feat)
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    import pickle
    with open('models/xg_model.pkl', 'wb') as f:
        pickle.dump(xg_model, f)
    
    # Save a sample of shots for the dashboard storytelling
    os.makedirs('data/processed', exist_ok=True)
    shots_feat.sample(min(1000, len(shots_feat))).to_csv('data/processed/shots_sample.csv', index=False)
    
    print("Model saved to models/xg_model.pkl")
