import pandas as pd
import numpy as np
from scipy import stats

def calculate_driver_stats(results_data):
    """Calculate comprehensive driver statistics"""
    
    driver_stats = results_data.groupby('driver').agg({
        'points': ['sum', 'mean', 'count'],
        'is_win': 'sum',
        'is_podium': 'sum',
        'grid': 'mean',
        'season': 'nunique'
    }).round(2)
    
    # Flatten column names
    driver_stats.columns = ['_'.join(col).strip() for col in driver_stats.columns]
    driver_stats = driver_stats.reset_index()
    
    # Rename columns for clarity
    column_mapping = {
        'points_sum': 'total_points',
        'points_mean': 'avg_points_per_race',
        'points_count': 'total_races',
        'is_win_sum': 'total_wins',
        'is_podium_sum': 'total_podiums',
        'grid_mean': 'avg_grid_position',
        'season_nunique': 'seasons_active'
    }
    driver_stats = driver_stats.rename(columns=column_mapping)
    
    # Calculate additional metrics
    driver_stats['win_rate'] = (driver_stats['total_wins'] / driver_stats['total_races'] * 100).round(2)
    driver_stats['podium_rate'] = (driver_stats['total_podiums'] / driver_stats['total_races'] * 100).round(2)
    driver_stats['points_per_season'] = (driver_stats['total_points'] / driver_stats['seasons_active']).round(2)
    
    # Fill NaN values
    driver_stats = driver_stats.fillna(0)
    
    return driver_stats

def calculate_constructor_stats(results_data):
    """Calculate comprehensive constructor statistics"""
    
    constructor_stats = results_data.groupby('constructor').agg({
        'points': ['sum', 'mean', 'count'],
        'is_win': 'sum',
        'is_podium': 'sum',
        'driver': 'nunique',
        'season': 'nunique'
    }).round(2)
    
    # Flatten column names
    constructor_stats.columns = ['_'.join(col).strip() for col in constructor_stats.columns]
    constructor_stats = constructor_stats.reset_index()
    
    # Rename columns for clarity
    column_mapping = {
        'points_sum': 'total_points',
        'points_mean': 'avg_points_per_race',
        'points_count': 'total_races',
        'is_win_sum': 'total_wins',
        'is_podium_sum': 'total_podiums',
        'driver_nunique': 'unique_drivers',
        'season_nunique': 'seasons_active'
    }
    constructor_stats = constructor_stats.rename(columns=column_mapping)
    
    # Calculate additional metrics
    constructor_stats['win_rate'] = (constructor_stats['total_wins'] / constructor_stats['total_races'] * 100).round(2)
    constructor_stats['podium_rate'] = (constructor_stats['total_podiums'] / constructor_stats['total_races'] * 100).round(2)
    constructor_stats['points_per_season'] = (constructor_stats['total_points'] / constructor_stats['seasons_active']).round(2)
    
    # Fill NaN values
    constructor_stats = constructor_stats.fillna(0)
    
    return constructor_stats

def calculate_circuit_stats(results_data, races_data):
    """Calculate circuit-specific statistics"""
    
    circuit_stats = results_data.groupby('circuit_id').agg({
        'points': ['sum', 'mean'],
        'is_win': 'sum',
        'is_podium': 'sum',
        'driver': 'nunique',
        'season': 'nunique'
    }).round(2)
    
    # Flatten column names
    circuit_stats.columns = ['_'.join(col).strip() for col in circuit_stats.columns]
    circuit_stats = circuit_stats.reset_index()
    
    # Rename columns
    column_mapping = {
        'points_sum': 'total_points',
        'points_mean': 'avg_points_per_race',
        'is_win_sum': 'total_wins',
        'is_podium_sum': 'total_podiums',
        'driver_nunique': 'unique_drivers',
        'season_nunique': 'seasons_featured'
    }
    circuit_stats = circuit_stats.rename(columns=column_mapping)
    
    # Merge with race information
    circuit_info = races_data.groupby('circuit_id').agg({
        'country': 'first',
        'lat': 'first',
        'long': 'first'
    }).reset_index()
    
    circuit_stats = pd.merge(circuit_stats, circuit_info, on='circuit_id', how='left')
    
    return circuit_stats

def calculate_qualifying_vs_race_correlation(qualifying_data, results_data):
    """Calculate correlation between qualifying and race performance"""
    
    # Merge qualifying and race data
    merged_data = pd.merge(
        qualifying_data,
        results_data,
        on=['season', 'round', 'circuit_id'],
        suffixes=('_qual', '_race')
    )
    
    if merged_data.empty or 'grid_position' not in merged_data.columns or 'grid' not in merged_data.columns:
        return None
    
    # Remove rows with missing data
    clean_data = merged_data.dropna(subset=['grid_position', 'grid'])
    
    if len(clean_data) < 2:
        return None
    
    # Calculate correlation
    correlation, p_value = stats.pearsonr(clean_data['grid_position'], clean_data['grid'])
    
    return {
        'correlation': correlation,
        'p_value': p_value,
        'sample_size': len(clean_data)
    }

def calculate_weather_impact(results_data, weather_data):
    """Calculate the impact of weather conditions on race performance"""
    
    # Merge results with weather data
    merged_data = pd.merge(
        results_data,
        weather_data,
        on=['season', 'round', 'circuit_id'],
        how='inner'
    )
    
    if merged_data.empty:
        return None
    
    weather_impact = {}
    
    # Analyze different weather conditions
    weather_conditions = ['weather_wet', 'weather_dry', 'weather_warm', 'weather_cold', 'weather_cloudy']
    
    for condition in weather_conditions:
        if condition in merged_data.columns:
            condition_true = merged_data[merged_data[condition] == True]
            condition_false = merged_data[merged_data[condition] == False]
            
            if len(condition_true) > 0 and len(condition_false) > 0:
                # Perform t-test to see if there's a significant difference
                stat, p_value = stats.ttest_ind(condition_true['points'], condition_false['points'])
                
                weather_impact[condition] = {
                    'mean_points_with_condition': condition_true['points'].mean(),
                    'mean_points_without_condition': condition_false['points'].mean(),
                    'difference': condition_true['points'].mean() - condition_false['points'].mean(),
                    't_statistic': stat,
                    'p_value': p_value,
                    'sample_size_with': len(condition_true),
                    'sample_size_without': len(condition_false)
                }
    
    return weather_impact

def calculate_head_to_head_stats(results_data, driver1, driver2):
    """Calculate head-to-head statistics between two drivers"""
    
    # Filter data for both drivers in the same races
    driver1_data = results_data[results_data['driver'] == driver1]
    driver2_data = results_data[results_data['driver'] == driver2]
    
    # Find common races (same season, round, circuit)
    common_races = pd.merge(
        driver1_data[['season', 'round', 'circuit_id', 'grid', 'points', 'is_win', 'is_podium']],
        driver2_data[['season', 'round', 'circuit_id', 'grid', 'points', 'is_win', 'is_podium']],
        on=['season', 'round', 'circuit_id'],
        suffixes=('_d1', '_d2')
    )
    
    if common_races.empty:
        return None
    
    # Calculate head-to-head statistics
    stats = {
        'total_common_races': len(common_races),
        'driver1_better_finish': (common_races['grid_d1'] < common_races['grid_d2']).sum(),
        'driver2_better_finish': (common_races['grid_d2'] < common_races['grid_d1']).sum(),
        'driver1_more_points': (common_races['points_d1'] > common_races['points_d2']).sum(),
        'driver2_more_points': (common_races['points_d2'] > common_races['points_d1']).sum(),
        'driver1_total_points': common_races['points_d1'].sum(),
        'driver2_total_points': common_races['points_d2'].sum(),
        'driver1_wins': common_races['is_win_d1'].sum(),
        'driver2_wins': common_races['is_win_d2'].sum(),
        'driver1_podiums': common_races['is_podium_d1'].sum(),
        'driver2_podiums': common_races['is_podium_d2'].sum(),
        'avg_finishing_position_d1': common_races['grid_d1'].mean(),
        'avg_finishing_position_d2': common_races['grid_d2'].mean()
    }
    
    return stats

def calculate_season_progression(standings_data, driver, season):
    """Calculate how a driver's championship position changed throughout a season"""
    
    driver_season = standings_data[
        (standings_data['driver'] == driver) & 
        (standings_data['season'] == season)
    ].sort_values('round')
    
    if driver_season.empty:
        return None
    
    progression = {
        'rounds': driver_season['round'].tolist(),
        'points': driver_season['driver_points_after_race'].tolist(),
        'position': driver_season['driver_standings_pos_after_race'].tolist(),
        'wins': driver_season['driver_wins_after_race'].tolist(),
        'final_position': driver_season['driver_standings_pos_after_race'].iloc[-1],
        'final_points': driver_season['driver_points_after_race'].iloc[-1],
        'total_wins': driver_season['driver_wins_after_race'].iloc[-1]
    }
    
    return progression
