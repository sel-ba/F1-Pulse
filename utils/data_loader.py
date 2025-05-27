import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_all_data():
    """Load all F1 datasets and return as dictionary"""
    
    data_files = {
        'driver_standings': 'attached_assets/driver_standings.csv',
        'qualifying': 'attached_assets/qualifying.csv',
        'races': 'attached_assets/races.csv',
        'results': 'attached_assets/results.csv',
        'weather': 'attached_assets/weather.csv'
    }
    
    data = {}
    
    for key, file_path in data_files.items():
        try:
            if os.path.exists(file_path):
                data[key] = pd.read_csv(file_path)
            else:
                st.error(f"File not found: {file_path}")
                return None
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")
            return None
    
    # Data cleaning and preprocessing
    data = clean_data(data)
    
    return data

def clean_data(data):
    """Clean and preprocess the loaded data"""
    
    # Clean driver standings
    if 'driver_standings' in data:
        df = data['driver_standings']
        # Convert numeric columns
        numeric_cols = ['driver_points_after_race', 'driver_wins_after_race', 
                       'driver_standings_pos_after_race', 'driver_points', 
                       'driver_wins', 'driver_standings_pos']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing essential data
        df = df.dropna(subset=['season', 'round', 'driver'])
        data['driver_standings'] = df
    
    # Clean qualifying data
    if 'qualifying' in data:
        df = data['qualifying']
        # Convert grid position to numeric
        df['grid_position'] = pd.to_numeric(df['grid_position'], errors='coerce')
        # Clean driver names (remove extra spaces and formatting)
        if 'driver_name' in df.columns:
            df['driver_name'] = df['driver_name'].str.strip()
            # Extract main driver name (remove codes in parentheses)
            df['driver'] = df['driver_name'].str.replace(r'\s+[A-Z]{3}$', '', regex=True)
            df['driver'] = df['driver'].str.replace(r'\s+', ' ', regex=True)
        data['qualifying'] = df
    
    # Clean results data
    if 'results' in data:
        df = data['results']
        # Convert numeric columns
        numeric_cols = ['grid', 'points']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert date of birth to datetime
        if 'date_of_birth' in df.columns:
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
        
        # Create win indicator
        df['is_win'] = (df['status'] == 'Finished') & (df['grid'] <= 50) & (df['points'] > 0)
        # More accurate win detection based on common F1 point systems
        df['is_win'] = df['points'] >= 25  # Assuming modern point system where win = 25 points
        
        # Create podium indicator (1st, 2nd, 3rd place)
        df['is_podium'] = df['podium'].isin([1, 2, 3]) if 'podium' in df.columns else False
        
        data['results'] = df
    
    # Clean races data
    if 'races' in data:
        df = data['races']
        # Convert date to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        data['races'] = df
    
    # Clean weather data
    if 'weather' in data:
        df = data['weather']
        # Convert boolean columns
        bool_cols = ['weather_warm', 'weather_cold', 'weather_dry', 'weather_wet', 'weather_cloudy']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        data['weather'] = df
    
    return data

def get_driver_list(data):
    """Get list of unique drivers from the data"""
    drivers = set()
    
    if 'driver_standings' in data:
        drivers.update(data['driver_standings']['driver'].unique())
    
    if 'results' in data:
        drivers.update(data['results']['driver'].unique())
    
    return sorted(list(drivers))

def get_constructor_list(data):
    """Get list of unique constructors from the data"""
    if 'results' in data:
        return sorted(data['results']['constructor'].unique())
    return []

def get_circuit_list(data):
    """Get list of unique circuits from the data"""
    circuits = set()
    
    if 'races' in data:
        circuits.update(data['races']['circuit_id'].unique())
    
    if 'results' in data:
        circuits.update(data['results']['circuit_id'].unique())
    
    return sorted(list(circuits))

def get_season_range(data):
    """Get the range of available seasons"""
    seasons = set()
    
    for dataset in ['driver_standings', 'results', 'races']:
        if dataset in data:
            seasons.update(data[dataset]['season'].unique())
    
    if seasons:
        return min(seasons), max(seasons)
    return None, None
