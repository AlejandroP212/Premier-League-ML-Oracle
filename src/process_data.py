import requests
import pandas as pd
import numpy as np

BASE_URL = "https://premier.72-60-245-2.sslip.io"

def fetch_data():
    """Fetches matches and players data from the API."""
    print("Fetching matches...")
    matches_resp = requests.get(f"{BASE_URL}/matches?limit=500")
    matches = pd.DataFrame(matches_resp.json()["matches"])
    
    print("Fetching players...")
    players_resp = requests.get(f"{BASE_URL}/players?limit=1000")
    players = pd.DataFrame(players_resp.json()["players"])
    
    return matches, players

def preprocess_matches(matches):
    """Basic preprocessing for matches."""
    matches = matches.copy()
    matches['date'] = pd.to_datetime(matches['date'], format='%d/%m/%Y')
    matches = matches.sort_values('date')
    
    # Ensure numeric columns
    num_cols = ['fthg', 'ftag', 'hs', 'as_', 'hst', 'ast', 'hc', 'ac', 'hf', 'af', 'hy', 'ay', 'hr', 'ar']
    for col in num_cols:
        matches[col] = pd.to_numeric(matches[col], errors='coerce')
    
    return matches

def get_rolling_averages(group, cols, new_cols):
    """Calculates rolling averages for a specific team's stats."""
    group = group.sort_values('date')
    rolling_stats = group[cols].rolling(5, closed='left').mean()
    group[new_cols] = rolling_stats
    return group.dropna(subset=new_cols)

def create_features(matches):
    """Creates rolling features for both home and away teams."""
    # We need a long format to calculate rolling averages per team
    # Identify which columns belong to which team in a match
    home_cols = ['fthg', 'hs', 'hst', 'hc', 'hf', 'hy', 'hr']
    away_cols = ['ftag', 'as_', 'ast', 'ac', 'af', 'ay', 'ar']
    
    # Generic names for long format
    generic_cols = ['goals', 'shots', 'sot', 'corners', 'fouls', 'yellows', 'reds']
    
    # Map for rolling features
    rolling_feature_names = [f"rolling_{c}" for c in generic_cols]
    
    # Create rows for each team in each match
    match_list = []
    for _, row in matches.iterrows():
        # Home team entry
        match_list.append({
            'date': row['date'],
            'team': row['home_team'],
            'opponent': row['away_team'],
            'is_home': 1,
            **{generic_cols[i]: row[home_cols[i]] for i in range(len(generic_cols))}
        })
        # Away team entry
        match_list.append({
            'date': row['date'],
            'team': row['away_team'],
            'opponent': row['home_team'],
            'is_home': 0,
            **{generic_cols[i]: row[away_cols[i]] for i in range(len(generic_cols))}
        })
    
    df_long = pd.DataFrame(match_list)
    
    # Apply rolling average per team
    rolling_groups = []
    for team, group in df_long.groupby('team'):
        res = get_rolling_averages(group, generic_cols, rolling_feature_names)
        rolling_groups.append(res)
    
    df_rolling = pd.concat(rolling_groups).reset_index(drop=True)
    
    # Pivot back to match level (wide format)
    home_rolling = df_rolling[df_rolling['is_home'] == 1].copy()
    away_rolling = df_rolling[df_rolling['is_home'] == 0].copy()
    
    # Rename columns for merging
    h_rolling_cols = {c: f"home_{c}" for c in rolling_feature_names}
    a_rolling_cols = {c: f"away_{c}" for c in rolling_feature_names}
    
    home_rolling = home_rolling.rename(columns=h_rolling_cols)
    away_rolling = away_rolling.rename(columns=a_rolling_cols)
    
    # Merge back to matches
    # Use date, home_team, away_team to join
    final_df = matches.merge(
        home_rolling[['date', 'team', 'opponent'] + list(h_rolling_cols.values())],
        left_on=['date', 'home_team', 'away_team'],
        right_on=['date', 'team', 'opponent']
    ).drop(['team', 'opponent'], axis=1)
    
    final_df = final_df.merge(
        away_rolling[['date', 'team', 'opponent'] + list(a_rolling_cols.values())],
        left_on=['date', 'away_team', 'home_team'],
        right_on=['date', 'team', 'opponent']
    ).drop(['team', 'opponent'], axis=1)
    
    # Add difference features
    for col in generic_cols:
        final_df[f'diff_{col}'] = final_df[f'home_rolling_{col}'] - final_df[f'away_rolling_{col}']
        
    return final_df

if __name__ == "__main__":
    matches_raw, players_raw = fetch_data()
    matches_pre = preprocess_matches(matches_raw)
    matches_final = create_features(matches_pre)
    
    print(f"Original matches: {len(matches_pre)}")
    print(f"Matches with rolling stats: {len(matches_final)}")
    
    # Save to data/processed (create dir if not exists)
    import os
    os.makedirs('data/processed', exist_ok=True)
    matches_final.to_csv('data/processed/matches_v2.csv', index=False)
    players_raw.to_csv('data/processed/players_raw.csv', index=False)
    print("Saved processed data to data/processed/matches_v2.csv")
