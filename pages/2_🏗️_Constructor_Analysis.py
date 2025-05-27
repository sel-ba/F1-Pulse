import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os

# Add parent directory to path to import utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_all_data, get_constructor_list
from utils.visualization import create_constructor_performance_timeline
from utils.statistics import calculate_constructor_stats

st.set_page_config(
    page_title="Constructor Analysis - F1 Analytics",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Constructor Analysis")
st.markdown("### Team performance analysis and championship insights")

# Load data
@st.cache_data
def get_data():
    return load_all_data()

try:
    data = get_data()
    driver_standings = data['driver_standings']
    qualifying = data['qualifying']
    races = data['races']
    results = data['results']
    weather = data['weather']
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Constructor Filters")

# Constructor selection
available_constructors = get_constructor_list(data)
selected_constructors = st.sidebar.multiselect(
    "Select Constructors for Analysis",
    available_constructors,
    default=available_constructors[:8] if len(available_constructors) >= 8 else available_constructors[:5]
)

if not selected_constructors:
    st.warning("Please select at least one constructor to analyze.")
    st.stop()

# Season filter
available_seasons = sorted(results['season'].unique())
season_range = st.sidebar.select_slider(
    "Season Range",
    options=available_seasons,
    value=(available_seasons[-10] if len(available_seasons) >= 10 else available_seasons[0], available_seasons[-1])
)

selected_seasons = [s for s in available_seasons if season_range[0] <= s <= season_range[1]]

# Filter data
filtered_results = results[
    (results['constructor'].isin(selected_constructors)) & 
    (results['season'].isin(selected_seasons))
]

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Performance Timeline", "🆚 Constructor Comparison", "🔍 Detailed Analysis"])

with tab1:
    st.header("📊 Constructor Overview")
    
    # Calculate constructor statistics
    constructor_stats = calculate_constructor_stats(filtered_results)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if not constructor_stats.empty:
        total_points = constructor_stats['total_points'].sum()
        total_wins = constructor_stats['total_wins'].sum()
        total_podiums = constructor_stats['total_podiums'].sum()
        total_races = constructor_stats['total_races'].sum()
        
        with col1:
            st.metric("Total Points", f"{total_points:,.0f}")
        with col2:
            st.metric("Total Wins", f"{total_wins:.0f}")
        with col3:
            st.metric("Total Podiums", f"{total_podiums:.0f}")
        with col4:
            st.metric("Total Races", f"{total_races:.0f}")
    
    # Constructor statistics table
    st.subheader("📋 Constructor Statistics")
    
    if not constructor_stats.empty:
        # Select key columns for display
        display_stats = constructor_stats[[
            'constructor', 'total_points', 'total_wins', 'total_podiums', 
            'total_races', 'win_rate', 'podium_rate', 'avg_points_per_race',
            'unique_drivers', 'seasons_active'
        ]].copy()
        
        # Sort by total points
        display_stats = display_stats.sort_values('total_points', ascending=False)
        
        st.dataframe(
            display_stats,
            use_container_width=True,
            column_config={
                "constructor": "Constructor",
                "total_points": st.column_config.NumberColumn("Total Points", format="%.0f"),
                "total_wins": st.column_config.NumberColumn("Wins", format="%.0f"),
                "total_podiums": st.column_config.NumberColumn("Podiums", format="%.0f"),
                "total_races": st.column_config.NumberColumn("Races", format="%.0f"),
                "win_rate": st.column_config.NumberColumn("Win Rate (%)", format="%.1f"),
                "podium_rate": st.column_config.NumberColumn("Podium Rate (%)", format="%.1f"),
                "avg_points_per_race": st.column_config.NumberColumn("Avg Points/Race", format="%.1f"),
                "unique_drivers": st.column_config.NumberColumn("Unique Drivers", format="%.0f"),
                "seasons_active": st.column_config.NumberColumn("Seasons", format="%.0f")
            }
        )
    
    # Top performers visualization
    st.subheader("🏆 Top Performing Constructors")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Total points comparison
        if not constructor_stats.empty:
            top_by_points = constructor_stats.nlargest(10, 'total_points')
            fig_points = px.bar(
                top_by_points,
                x='constructor',
                y='total_points',
                title="Total Points by Constructor",
                labels={'total_points': 'Total Points', 'constructor': 'Constructor'}
            )
            fig_points.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_points, use_container_width=True)
    
    with col2:
        # Win rate comparison
        if not constructor_stats.empty:
            # Filter constructors with meaningful race count for win rate
            meaningful_constructors = constructor_stats[constructor_stats['total_races'] >= 10]
            if not meaningful_constructors.empty:
                top_by_winrate = meaningful_constructors.nlargest(10, 'win_rate')
                fig_winrate = px.bar(
                    top_by_winrate,
                    x='constructor',
                    y='win_rate',
                    title="Win Rate by Constructor (Min 10 races)",
                    labels={'win_rate': 'Win Rate (%)', 'constructor': 'Constructor'}
                )
                fig_winrate.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_winrate, use_container_width=True)

with tab2:
    st.header("📈 Performance Timeline")
    
    # Constructor performance over time
    if not filtered_results.empty:
        timeline_fig = create_constructor_performance_timeline(
            filtered_results, 
            selected_constructors, 
            selected_seasons
        )
        st.plotly_chart(timeline_fig, use_container_width=True)
        
        # Seasonal breakdown
        st.subheader("📊 Season-by-Season Breakdown")
        
        # Calculate season totals
        season_stats = []
        for constructor in selected_constructors:
            for season in selected_seasons:
                season_data = filtered_results[
                    (filtered_results['constructor'] == constructor) & 
                    (filtered_results['season'] == season)
                ]
                
                if not season_data.empty:
                    stats = {
                        'Constructor': constructor,
                        'Season': season,
                        'Points': season_data['points'].sum(),
                        'Wins': season_data['is_win'].sum() if 'is_win' in season_data.columns else 0,
                        'Podiums': season_data['is_podium'].sum() if 'is_podium' in season_data.columns else 0,
                        'Races': len(season_data),
                        'Avg_Points_Per_Race': season_data['points'].mean()
                    }
                    season_stats.append(stats)
        
        if season_stats:
            season_df = pd.DataFrame(season_stats)
            
            # Pivot table for better visualization
            pivot_points = season_df.pivot(index='Season', columns='Constructor', values='Points').fillna(0)
            
            st.subheader("🏆 Points by Season")
            fig_heatmap = px.imshow(
                pivot_points.T,
                labels=dict(x="Season", y="Constructor", color="Points"),
                title="Constructor Points Heatmap",
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("No data available for the selected constructors and seasons.")

with tab3:
    st.header("🆚 Constructor Comparison")
    
    # Select specific constructors for detailed comparison
    if len(selected_constructors) >= 2:
        comparison_constructors = st.multiselect(
            "Select Constructors to Compare",
            selected_constructors,
            default=selected_constructors[:3] if len(selected_constructors) >= 3 else selected_constructors
        )
        
        if comparison_constructors:
            # Detailed comparison metrics
            comparison_data = constructor_stats[constructor_stats['constructor'].isin(comparison_constructors)]
            
            if not comparison_data.empty:
                # Radar chart for multi-dimensional comparison
                st.subheader("📊 Multi-Dimensional Performance Comparison")
                
                # Normalize metrics for radar chart
                metrics = ['win_rate', 'podium_rate', 'avg_points_per_race']
                normalized_data = comparison_data.copy()
                
                for metric in metrics:
                    max_val = normalized_data[metric].max()
                    if max_val > 0:
                        normalized_data[f'{metric}_norm'] = normalized_data[metric] / max_val * 100
                
                # Create radar chart
                fig_radar = go.Figure()
                
                colors = px.colors.qualitative.Set1
                
                for i, constructor in enumerate(comparison_constructors):
                    constructor_data = normalized_data[normalized_data['constructor'] == constructor]
                    if not constructor_data.empty:
                        values = [
                            constructor_data['win_rate_norm'].iloc[0],
                            constructor_data['podium_rate_norm'].iloc[0],
                            constructor_data['avg_points_per_race_norm'].iloc[0]
                        ]
                        values.append(values[0])  # Close the radar chart
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=['Win Rate', 'Podium Rate', 'Avg Points/Race', 'Win Rate'],
                            fill='toself',
                            name=constructor,
                            line_color=colors[i % len(colors)]
                        ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    title="Constructor Performance Radar Chart (Normalized %)"
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
                # Side-by-side comparison
                st.subheader("📋 Side-by-Side Comparison")
                
                comparison_display = comparison_data[[
                    'constructor', 'total_points', 'total_wins', 'total_podiums',
                    'win_rate', 'podium_rate', 'avg_points_per_race'
                ]].round(2)
                
                st.dataframe(comparison_display, use_container_width=True)
                
                # Performance trends
                col1, col2 = st.columns(2)
                
                with col1:
                    # Wins comparison
                    fig_wins = px.bar(
                        comparison_data,
                        x='constructor',
                        y='total_wins',
                        title="Total Wins Comparison",
                        labels={'total_wins': 'Total Wins', 'constructor': 'Constructor'}
                    )
                    st.plotly_chart(fig_wins, use_container_width=True)
                
                with col2:
                    # Points per race comparison
                    fig_ppr = px.bar(
                        comparison_data,
                        x='constructor',
                        y='avg_points_per_race',
                        title="Average Points per Race",
                        labels={'avg_points_per_race': 'Avg Points/Race', 'constructor': 'Constructor'}
                    )
                    st.plotly_chart(fig_ppr, use_container_width=True)
        else:
            st.info("Please select constructors to compare.")
    else:
        st.info("Please select at least 2 constructors for comparison.")

with tab4:
    st.header("🔍 Detailed Analysis")
    
    # Constructor-specific analysis
    selected_constructor = st.selectbox(
        "Select Constructor for Detailed Analysis",
        selected_constructors
    )
    
    if selected_constructor:
        constructor_data = filtered_results[filtered_results['constructor'] == selected_constructor]
        
        st.subheader(f"📊 {selected_constructor} - Detailed Performance")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_points = constructor_data['points'].sum()
        total_wins = constructor_data['is_win'].sum() if 'is_win' in constructor_data.columns else 0
        total_podiums = constructor_data['is_podium'].sum() if 'is_podium' in constructor_data.columns else 0
        total_races = len(constructor_data)
        
        with col1:
            st.metric("Total Points", f"{total_points:.0f}")
        with col2:
            st.metric("Total Wins", f"{total_wins:.0f}")
        with col3:
            st.metric("Total Podiums", f"{total_podiums:.0f}")
        with col4:
            st.metric("Total Races", f"{total_races}")
        
        # Driver lineup analysis
        st.subheader("👥 Driver Lineup Analysis")
        
        driver_performance = constructor_data.groupby('driver').agg({
            'points': ['sum', 'mean', 'count'],
            'is_win': 'sum' if 'is_win' in constructor_data.columns else lambda x: 0,
            'is_podium': 'sum' if 'is_podium' in constructor_data.columns else lambda x: 0
        }).round(2)
        
        # Flatten column names
        driver_performance.columns = ['_'.join(col).strip() for col in driver_performance.columns]
        driver_performance = driver_performance.reset_index()
        
        # Rename columns
        column_mapping = {
            'points_sum': 'Total_Points',
            'points_mean': 'Avg_Points',
            'points_count': 'Races',
            'is_win_sum': 'Wins',
            'is_podium_sum': 'Podiums'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in driver_performance.columns:
                driver_performance = driver_performance.rename(columns={old_col: new_col})
        
        st.dataframe(driver_performance, use_container_width=True)
        
        # Performance by season
        st.subheader("📈 Performance by Season")
        
        seasonal_performance = constructor_data.groupby('season').agg({
            'points': 'sum',
            'is_win': 'sum' if 'is_win' in constructor_data.columns else lambda x: 0,
            'is_podium': 'sum' if 'is_podium' in constructor_data.columns else lambda x: 0
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Points by season
            fig_season_points = px.line(
                seasonal_performance,
                x='season',
                y='points',
                title=f"{selected_constructor} - Points by Season",
                markers=True
            )
            st.plotly_chart(fig_season_points, use_container_width=True)
        
        with col2:
            # Wins by season
            fig_season_wins = px.bar(
                seasonal_performance,
                x='season',
                y='is_win',
                title=f"{selected_constructor} - Wins by Season"
            )
            st.plotly_chart(fig_season_wins, use_container_width=True)
        
        # Recent results
        st.subheader("🏁 Recent Results")
        
        recent_results = constructor_data.sort_values(['season', 'round'], ascending=[False, False]).head(20)
        
        display_results = recent_results[[
            'season', 'round', 'circuit_id', 'driver', 
            'grid', 'points', 'status'
        ]].copy()
        
        st.dataframe(
            display_results,
            use_container_width=True,
            column_config={
                "season": "Season",
                "round": "Round",
                "circuit_id": "Circuit",
                "driver": "Driver",
                "grid": st.column_config.NumberColumn("Finish Position", format="%.0f"),
                "points": st.column_config.NumberColumn("Points", format="%.1f"),
                "status": "Status"
            }
        )

# Export data option
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export Constructor Data"):
    # Prepare export data
    export_data = calculate_constructor_stats(filtered_results)
    csv = export_data.to_csv(index=False)
    
    st.sidebar.download_button(
        label="Download Constructor Statistics CSV",
        data=csv,
        file_name=f"constructor_analysis_{'-'.join(map(str, selected_seasons))}.csv",
        mime="text/csv"
    )
