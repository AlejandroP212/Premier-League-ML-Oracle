import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import os
import seaborn as sns
import matplotlib.pyplot as plt

def train_classification():
    print("Loading processed matches...")
    df = pd.read_csv('data/processed/matches_v2.csv')
    
    # Features
    features = [
        'home_rolling_goals', 'away_rolling_goals',
        'home_rolling_shots', 'away_rolling_shots',
        'home_rolling_sot', 'away_rolling_sot',
        'diff_goals', 'diff_shots', 'diff_sot',
        'b365h', 'b365d', 'b365a'
    ]
    
    X = df[features]
    y = df['ftr']
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Match Result Model
    model = LogisticRegression(max_iter=1000)
    cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
    
    model.fit(X, y)
    
    print(f"Match Predictor Accuracy (CV): {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Comparison with Bet365 Baseline
    # Bet365 "prediction" is the outcome with the lowest odds (highest prob)
    df['b365_pred'] = df[['b365h', 'b365d', 'b365a']].idxmin(axis=1).map({
        'b365h': 'H', 'b365d': 'D', 'b365a': 'A'
    })
    baseline_acc = accuracy_score(df['ftr'], df['b365_pred'])
    print(f"Bet365 Baseline Accuracy: {baseline_acc:.3f}")
    
    # Classification Report
    y_pred = model.predict(X)
    print("\nClassification Report (Training Data):")
    print(classification_report(y, y_pred))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    with open('models/match_predictor.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Save Confusion Matrix
    cm = confusion_matrix(y, y_pred, labels=['H', 'D', 'A'])
    cm_df = pd.DataFrame(cm, index=['H', 'D', 'A'], columns=['H', 'D', 'A'])
    os.makedirs('data/processed', exist_ok=True)
    cm_df.to_csv('data/processed/confusion_matrix.csv')
    
    # Save stats for dashboard
    stats = {
        'accuracy': cv_scores.mean(),
        'baseline_accuracy': baseline_acc,
        'features': features
    }
    with open('data/processed/classification_stats.json', 'w') as f:
        import json
        json.dump(stats, f)
        
    print("\nModel and statistics saved.")

if __name__ == "__main__":
    train_classification()
