import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os

def train_regression():
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
    y_home = df['fthg']
    y_away = df['ftag']
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # Home Goals Model
    model_home = LinearRegression()
    cv_scores_h = cross_val_score(model_home, X, y_home, cv=kf, scoring='neg_mean_absolute_error')
    model_home.fit(X, y_home)
    
    # Away Goals Model
    model_away = LinearRegression()
    cv_scores_a = cross_val_score(model_away, X, y_away, cv=kf, scoring='neg_mean_absolute_error')
    model_away.fit(X, y_away)
    
    print(f"Home Goals MAE (CV): {-cv_scores_h.mean():.3f} (+/- {cv_scores_h.std():.3f})")
    print(f"Away Goals MAE (CV): {-cv_scores_a.mean():.3f} (+/- {cv_scores_a.std():.3f})")
    
    # Feature Importance
    importance = pd.DataFrame({
        'Feature': features,
        'Coef_Home': model_home.coef_,
        'Coef_Away': model_away.coef_
    }).sort_values('Coef_Home', ascending=False)
    print("\nFeature Importance (Home Goals):")
    print(importance[['Feature', 'Coef_Home']].head(5))
    
    # Save models
    os.makedirs('models', exist_ok=True)
    with open('models/regression_home.pkl', 'wb') as f:
        pickle.dump(model_home, f)
    with open('models/regression_away.pkl', 'wb') as f:
        pickle.dump(model_away, f)
    
    # Save importance for dashboard
    importance.to_csv('data/processed/regression_importance.csv', index=False)
    print("\nModels and importance saved.")

if __name__ == "__main__":
    train_regression()
