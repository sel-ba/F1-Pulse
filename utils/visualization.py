import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_championship_evolution_chart(standings_data, drivers, seasons):
    """Create a line chart showing championship points evolution over rounds"""
    
    fig = go.Figure()
    
    # Color palette for drivers
    colors = px.colors.qualitative.Set1
    
    for i, driver in enumerate(drivers):
        driver_data = standings_data[
            (standings_data['driver'] == driver) & 
            (standings_data['season'].isin(seasons))
        ]
        
        if not driver_data.empty:
            # Group by season and round to get cumulative points
            for season in seasons:
                season_data = driver_data[driver_data['season'] == season]
                if not season_data.empty:
                    season_data = season_data.sort_values('round')
                    
                    fig.add_trace(go.Scatter(
                        x=season_data['round'],
                        y=season_data['driver_points_after_race'],
                        mode='lines+markers',
                        name=f"{driver} ({season})",
                        line=dict(color=colors[i % len(colors)]),
                        hovertemplate=f"<b>{driver}</b><br>Round: %{{x}}<br>Points: %{{y}}<extra></extra>"
                    ))
    
    fig.update_layout(
        title="Championship Points Evolution",
        xaxis_title="Round",
        yaxis_title="Cumulative Points",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_performance_comparison(data, drivers, metric='points'):
    """Create a comparison chart for selected drivers"""
    
    driver_data = data[data['driver'].isin(drivers)]
    
    if metric == 'points':
        fig = px.box(
            driver_data,
            x='driver',
            y='points',
            title="Points Distribution by Driver",
            labels={'points': 'Points per Race', 'driver': 'Driver'}
        )
    elif metric == 'grid':
        fig = px.box(
            driver_data,
            x='driver',
            y='grid',
            title="Grid Position Distribution by Driver",
            labels={'grid': 'Grid Position', 'driver': 'Driver'}
        )
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_qualifying_vs_race_analysis(qualifying_data, results_data, driver=None):
    """Create analysis comparing qualifying performance to race results"""
    
    # Merge qualifying and race data
    merged_data = pd.merge(
        qualifying_data,
        results_data,
        on=['season', 'round', 'circuit_id'],
        how='inner',
        suffixes=('_qual', '_race')
    )
    
    if driver:
        # For specific driver analysis, match driver names
        if 'driver_qual' in merged_data.columns and 'driver_race' in merged_data.columns:
            merged_data = merged_data[
                (merged_data['driver_race'] == driver) |
                (merged_data['driver_qual'].str.contains(driver, case=False, na=False))
            ]
    
    if merged_data.empty:
        return go.Figure().add_annotation(
            text="No matching data found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    # Create scatter plot
    fig = px.scatter(
        merged_data,
        x='grid_position',
        y='grid',
        color='points',
        title="Qualifying vs Race Performance",
        labels={
            'grid_position': 'Qualifying Position',
            'grid': 'Race Finish Position',
            'points': 'Points Scored'
        },
        hover_data=['season', 'circuit_id']
    )
    
    # Add diagonal line for reference (perfect correlation)
    max_pos = max(merged_data['grid_position'].max(), merged_data['grid'].max())
    fig.add_trace(go.Scatter(
        x=[1, max_pos],
        y=[1, max_pos],
        mode='lines',
        name='Perfect Correlation',
        line=dict(dash='dash', color='red')
    ))
    
    return fig

def create_constructor_performance_timeline(results_data, constructors, seasons):
    """Create timeline showing constructor performance over seasons"""
    
    constructor_season_stats = []
    
    for constructor in constructors:
        for season in seasons:
            season_data = results_data[
                (results_data['constructor'] == constructor) & 
                (results_data['season'] == season)
            ]
            
            if not season_data.empty:
                stats = {
                    'constructor': constructor,
                    'season': season,
                    'total_points': season_data['points'].sum(),
                    'total_wins': season_data['is_win'].sum() if 'is_win' in season_data.columns else 0,
                    'total_podiums': season_data['is_podium'].sum() if 'is_podium' in season_data.columns else 0,
                    'races': len(season_data)
                }
                constructor_season_stats.append(stats)
    
    if not constructor_season_stats:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    stats_df = pd.DataFrame(constructor_season_stats)
    
    fig = px.line(
        stats_df,
        x='season',
        y='total_points',
        color='constructor',
        title="Constructor Points by Season",
        labels={'total_points': 'Total Points', 'season': 'Season'},
        markers=True
    )
    
    return fig

def create_weather_impact_chart(results_data, weather_data):
    """Create chart showing weather impact on race performance"""
    
    # Merge results with weather data
    merged_data = pd.merge(
        results_data,
        weather_data,
        on=['season', 'round', 'circuit_id'],
        how='inner'
    )
    
    if merged_data.empty:
        return go.Figure().add_annotation(
            text="No weather data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    # Create weather categories
    weather_conditions = []
    for _, row in merged_data.iterrows():
        conditions = []
        if row.get('weather_wet', False):
            conditions.append('Wet')
        if row.get('weather_dry', False):
            conditions.append('Dry')
        if row.get('weather_warm', False):
            conditions.append('Warm')
        if row.get('weather_cold', False):
            conditions.append('Cold')
        if row.get('weather_cloudy', False):
            conditions.append('Cloudy')
        
        weather_conditions.append(', '.join(conditions) if conditions else 'Unknown')
    
    merged_data['weather_condition'] = weather_conditions
    
    # Calculate average points by weather condition
    weather_performance = merged_data.groupby('weather_condition').agg({
        'points': 'mean',
        'is_win': 'mean',
        'is_podium': 'mean'
    }).reset_index()
    
    weather_performance = weather_performance[weather_performance['weather_condition'] != 'Unknown']
    
    if weather_performance.empty:
        return go.Figure().add_annotation(
            text="No valid weather data found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    fig = px.bar(
        weather_performance,
        x='weather_condition',
        y='points',
        title="Average Points by Weather Condition",
        labels={'points': 'Average Points', 'weather_condition': 'Weather Condition'}
    )
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_circuit_performance_map(races_data, results_data, metric='points'):
    """Create a map showing performance by circuit"""
    
    # Calculate circuit statistics
    circuit_stats = results_data.groupby('circuit_id').agg({
        'points': 'mean',
        'is_win': 'sum',
        'is_podium': 'sum'
    }).reset_index()
    
    # Merge with race location data
    circuit_map_data = pd.merge(
        circuit_stats,
        races_data[['circuit_id', 'lat', 'long', 'country']].drop_duplicates(),
        on='circuit_id',
        how='inner'
    )
    
    if circuit_map_data.empty:
        return go.Figure().add_annotation(
            text="No circuit location data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    fig = px.scatter_mapbox(
        circuit_map_data,
        lat='lat',
        lon='long',
        size=metric,
        color=metric,
        hover_name='circuit_id',
        hover_data=['country'],
        mapbox_style='open-street-map',
        title=f"Circuit Performance Map - {metric.title()}",
        zoom=1
    )
    
    return fig

def create_3d_championship_evolution(standings_data, drivers, seasons):
    """Create 3D championship evolution visualization"""
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, driver in enumerate(drivers):
        driver_data = standings_data[
            (standings_data['driver'] == driver) & 
            (standings_data['season'].isin(seasons))
        ]
        
        if not driver_data.empty:
            for season in seasons:
                season_data = driver_data[driver_data['season'] == season]
                if not season_data.empty:
                    season_data = season_data.sort_values('round')
                    
                    fig.add_trace(go.Scatter3d(
                        x=season_data['round'],
                        y=[season] * len(season_data),
                        z=season_data['driver_points_after_race'],
                        mode='lines+markers',
                        name=f"{driver}",
                        line=dict(color=colors[i % len(colors)], width=4),
                        marker=dict(size=4, color=colors[i % len(colors)]),
                        hovertemplate=f"<b>{driver}</b><br>Season: {season}<br>Round: %{{x}}<br>Points: %{{z}}<extra></extra>"
                    ))
    
    fig.update_layout(
        title="3D Championship Evolution Across Seasons",
        scene=dict(
            xaxis_title="Round",
            yaxis_title="Season",
            zaxis_title="Cumulative Points",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        height=600
    )
    
    return fig

def create_performance_radar_3d(driver_stats, drivers):
    """Create 3D radar chart for driver performance comparison"""
    
    if len(drivers) == 0 or driver_stats.empty:
        return go.Figure().add_annotation(
            text="No driver data available for radar chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    # Filter data for selected drivers
    filtered_stats = driver_stats[driver_stats['driver'].isin(drivers)]
    
    if filtered_stats.empty:
        return go.Figure().add_annotation(
            text="No statistics available for selected drivers",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    # Normalize metrics for comparison
    metrics = ['win_rate', 'podium_rate', 'avg_points_per_race']
    available_metrics = [m for m in metrics if m in filtered_stats.columns]
    
    if not available_metrics:
        return go.Figure().add_annotation(
            text="Required metrics not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, driver in enumerate(drivers):
        driver_data = filtered_stats[filtered_stats['driver'] == driver]
        if not driver_data.empty:
            values = []
            for metric in available_metrics:
                max_val = filtered_stats[metric].max()
                normalized_val = (driver_data[metric].iloc[0] / max_val * 100) if max_val > 0 else 0
                values.append(normalized_val)
            
            # Close the radar chart
            values.append(values[0])
            metric_labels = [m.replace('_', ' ').title() for m in available_metrics] + [available_metrics[0].replace('_', ' ').title()]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metric_labels,
                fill='toself',
                name=driver,
                line_color=colors[i % len(colors)]
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="Multi-Dimensional Driver Performance Comparison",
        height=500
    )
    
    return fig
