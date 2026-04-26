import pandas as pd
import numpy as np
import json
import pickle
import os

def export_data():
    print("Exporting data for dashboard...")
    
    # 1. Load Data
    matches = pd.read_csv('data/processed/matches_v2.csv')
    shots = pd.read_csv('data/processed/shots_sample.csv')
    reg_importance = pd.read_csv('data/processed/regression_importance.csv')
    with open('data/processed/classification_stats.json', 'r') as f:
        class_stats = json.load(f)
    
    # 2. Load Models
    with open('models/xg_model.pkl', 'rb') as f:
        xg_model = pickle.load(f)
    with open('models/regression_home.pkl', 'rb') as f:
        reg_h = pickle.load(f)
    with open('models/regression_away.pkl', 'rb') as f:
        reg_a = pickle.load(f)
    with open('models/match_predictor.pkl', 'rb') as f:
        clf = pickle.load(f)
        
    # 3. Prepare Team Stats (Latest form)
    teams = matches['home_team'].unique()
    team_stats = {}
    for team in teams:
        latest = matches[(matches['home_team'] == team) | (matches['away_team'] == team)].iloc[-1]
        is_home = latest['home_team'] == team
        prefix = 'home_rolling_' if is_home else 'away_rolling_'
        team_stats[team] = {
            'goals': latest[f'{prefix}goals'],
            'shots': latest[f'{prefix}shots'],
            'sot': latest[f'{prefix}sot']
        }
        
    # 4. Generate All Possible Matchups (for the simulator)
    # Actually, we can just export the team stats and do the calculation in JS
    # But we need the model coefficients
    model_data = {
        'regression': {
            'home_coef': reg_h.coef_.tolist(),
            'home_intercept': reg_h.intercept_,
            'away_coef': reg_a.coef_.tolist(),
            'away_intercept': reg_a.intercept_,
            'features': class_stats['features']
        },
        'classification': {
            'coef': clf.coef_.tolist(),
            'intercept': clf.intercept_.tolist(),
            'classes': clf.classes_.tolist()
        },
        'xg': {
            'coef': xg_model.coef_.tolist(),
            'intercept': xg_model.intercept_.tolist()
        }
    }
    
    # 5. Dashboard JSON
    dashboard_data = {
        'teams': list(teams),
        'team_stats': team_stats,
        'shots_sample': shots.head(200).to_dict(orient='records'),
        'metrics': {
            'accuracy': class_stats['accuracy'],
            'baseline': class_stats['baseline_accuracy'],
            'regression_importance': reg_importance.to_dict(orient='records')
        },
        'models': model_data
    }
    
    os.makedirs('dashboard/data', exist_ok=True)
    with open('dashboard/data/data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
        
    print("Dashboard data exported to dashboard/data/data.json")

if __name__ == "__main__":
    export_data()
