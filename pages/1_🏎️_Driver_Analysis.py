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

from utils.data_loader import load_all_data, get_driver_list
from utils.visualization import create_championship_evolution_chart, create_performance_comparison, create_qualifying_vs_race_analysis, create_3d_championship_evolution, create_performance_radar_3d
from utils.statistics import calculate_driver_stats, calculate_head_to_head_stats, calculate_season_progression

st.set_page_config(
    page_title="Driver Analysis - F1 Analytics",
    page_icon="🏎️",
    layout="wide"
)

st.title("🏎️ Driver Analysis")
st.markdown("### Comprehensive driver performance analysis and comparisons")

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
st.sidebar.header("🔍 Analysis Filters")

# Driver selection
available_drivers = get_driver_list(data)
selected_drivers = st.sidebar.multiselect(
    "Select Drivers for Analysis",
    available_drivers,
    default=available_drivers[:5] if len(available_drivers) >= 5 else available_drivers[:3]
)

if not selected_drivers:
    st.warning("Please select at least one driver to analyze.")
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
    (results['driver'].isin(selected_drivers)) & 
    (results['season'].isin(selected_seasons))
]

filtered_standings = driver_standings[
    (driver_standings['driver'].isin(selected_drivers)) & 
    (driver_standings['season'].isin(selected_seasons))
]

# Tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🆚 Head-to-Head", "📈 Season Progression", "🎯 Performance Details", "🏎️ 3D Analysis"])

with tab1:
    st.header("📊 Driver Overview")
    
    # Calculate driver statistics
    driver_stats = calculate_driver_stats(filtered_results)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if not driver_stats.empty:
        total_points = driver_stats['total_points'].sum()
        total_wins = driver_stats['total_wins'].sum()
        total_podiums = driver_stats['total_podiums'].sum()
        total_races = driver_stats['total_races'].sum()
        
        with col1:
            st.metric("Total Points", f"{total_points:,.0f}")
        with col2:
            st.metric("Total Wins", f"{total_wins:.0f}")
        with col3:
            st.metric("Total Podiums", f"{total_podiums:.0f}")
        with col4:
            st.metric("Total Races", f"{total_races:.0f}")
    
    # Driver statistics table
    st.subheader("📋 Driver Statistics")
    
    if not driver_stats.empty:
        # Select key columns for display
        display_stats = driver_stats[[
            'driver', 'total_points', 'total_wins', 'total_podiums', 
            'total_races', 'win_rate', 'podium_rate', 'avg_points_per_race',
            'avg_grid_position', 'seasons_active'
        ]].copy()
        
        # Sort by total points
        display_stats = display_stats.sort_values('total_points', ascending=False)
        
        st.dataframe(
            display_stats,
            use_container_width=True,
            column_config={
                "driver": "Driver",
                "total_points": st.column_config.NumberColumn("Total Points", format="%.0f"),
                "total_wins": st.column_config.NumberColumn("Wins", format="%.0f"),
                "total_podiums": st.column_config.NumberColumn("Podiums", format="%.0f"),
                "total_races": st.column_config.NumberColumn("Races", format="%.0f"),
                "win_rate": st.column_config.NumberColumn("Win Rate (%)", format="%.1f"),
                "podium_rate": st.column_config.NumberColumn("Podium Rate (%)", format="%.1f"),
                "avg_points_per_race": st.column_config.NumberColumn("Avg Points/Race", format="%.1f"),
                "avg_grid_position": st.column_config.NumberColumn("Avg Grid Position", format="%.1f"),
                "seasons_active": st.column_config.NumberColumn("Seasons", format="%.0f")
            }
        )
    
    # Performance comparison charts
    st.subheader("📈 Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Points comparison
        if not driver_stats.empty:
            fig_points = px.bar(
                driver_stats.sort_values('total_points', ascending=True),
                x='total_points',
                y='driver',
                orientation='h',
                title="Total Points Comparison",
                labels={'total_points': 'Total Points', 'driver': 'Driver'}
            )
            fig_points.update_layout(height=400)
            st.plotly_chart(fig_points, use_container_width=True)
    
    with col2:
        # Win rate comparison
        if not driver_stats.empty:
            fig_winrate = px.bar(
                driver_stats.sort_values('win_rate', ascending=True),
                x='win_rate',
                y='driver',
                orientation='h',
                title="Win Rate Comparison",
                labels={'win_rate': 'Win Rate (%)', 'driver': 'Driver'}
            )
            fig_winrate.update_layout(height=400)
            st.plotly_chart(fig_winrate, use_container_width=True)
    
    # Championship evolution
    st.subheader("🏆 Championship Points Evolution")
    
    if not filtered_standings.empty:
        evolution_fig = create_championship_evolution_chart(
            filtered_standings, 
            selected_drivers, 
            selected_seasons
        )
        st.plotly_chart(evolution_fig, use_container_width=True)
    else:
        st.info("No championship standings data available for the selected drivers and seasons.")

with tab2:
    st.header("🆚 Head-to-Head Analysis")
    
    if len(selected_drivers) >= 2:
        # Driver selection for head-to-head
        col1, col2 = st.columns(2)
        
        with col1:
            driver1 = st.selectbox("Driver 1", selected_drivers, key="h2h_driver1")
        with col2:
            driver2 = st.selectbox("Driver 2", [d for d in selected_drivers if d != driver1], key="h2h_driver2")
        
        if driver1 and driver2:
            # Calculate head-to-head stats
            h2h_stats = calculate_head_to_head_stats(filtered_results, driver1, driver2)
            
            if h2h_stats:
                st.subheader(f"📊 {driver1} vs {driver2}")
                
                # Head-to-head metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Common Races", h2h_stats['total_common_races'])
                with col2:
                    st.metric(f"{driver1} Better Finishes", h2h_stats['driver1_better_finish'])
                with col3:
                    st.metric(f"{driver2} Better Finishes", h2h_stats['driver2_better_finish'])
                with col4:
                    win_percentage = (h2h_stats['driver1_better_finish'] / h2h_stats['total_common_races'] * 100) if h2h_stats['total_common_races'] > 0 else 0
                    st.metric(f"{driver1} Win %", f"{win_percentage:.1f}%")
                
                # Detailed comparison
                comparison_data = {
                    'Metric': ['Total Points', 'Points/Race Average', 'Wins', 'Podiums', 'Avg Finish Position'],
                    driver1: [
                        h2h_stats['driver1_total_points'],
                        h2h_stats['driver1_total_points'] / h2h_stats['total_common_races'] if h2h_stats['total_common_races'] > 0 else 0,
                        h2h_stats['driver1_wins'],
                        h2h_stats['driver1_podiums'],
                        h2h_stats['avg_finishing_position_d1']
                    ],
                    driver2: [
                        h2h_stats['driver2_total_points'],
                        h2h_stats['driver2_total_points'] / h2h_stats['total_common_races'] if h2h_stats['total_common_races'] > 0 else 0,
                        h2h_stats['driver2_wins'],
                        h2h_stats['driver2_podiums'],
                        h2h_stats['avg_finishing_position_d2']
                    ]
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
                
                # Visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    # Points comparison
                    fig_points = go.Figure(data=[
                        go.Bar(name=driver1, x=['Total Points'], y=[h2h_stats['driver1_total_points']]),
                        go.Bar(name=driver2, x=['Total Points'], y=[h2h_stats['driver2_total_points']])
                    ])
                    fig_points.update_layout(
                        title="Head-to-Head Points Comparison",
                        barmode='group'
                    )
                    st.plotly_chart(fig_points, use_container_width=True)
                
                with col2:
                    # Win/Podium comparison
                    categories = ['Wins', 'Podiums']
                    driver1_values = [h2h_stats['driver1_wins'], h2h_stats['driver1_podiums']]
                    driver2_values = [h2h_stats['driver2_wins'], h2h_stats['driver2_podiums']]
                    
                    fig_achievements = go.Figure(data=[
                        go.Bar(name=driver1, x=categories, y=driver1_values),
                        go.Bar(name=driver2, x=categories, y=driver2_values)
                    ])
                    fig_achievements.update_layout(
                        title="Wins and Podiums Comparison",
                        barmode='group'
                    )
                    st.plotly_chart(fig_achievements, use_container_width=True)
            else:
                st.info(f"No common races found between {driver1} and {driver2} in the selected period.")
    else:
        st.info("Please select at least 2 drivers for head-to-head analysis.")

with tab3:
    st.header("📈 Season Progression Analysis")
    
    # Season and driver selection for progression
    col1, col2 = st.columns(2)
    
    with col1:
        progression_driver = st.selectbox("Select Driver", selected_drivers, key="progression_driver")
    with col2:
        progression_season = st.selectbox("Select Season", selected_seasons, key="progression_season")
    
    if progression_driver and progression_season:
        # Calculate season progression
        progression = calculate_season_progression(filtered_standings, progression_driver, progression_season)
        
        if progression:
            st.subheader(f"📊 {progression_driver} - {progression_season} Season")
            
            # Final season stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Final Position", f"{progression['final_position']}")
            with col2:
                st.metric("Final Points", f"{progression['final_points']}")
            with col3:
                st.metric("Total Wins", f"{progression['total_wins']}")
            
            # Progression charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Points progression
                fig_points = go.Figure()
                fig_points.add_trace(go.Scatter(
                    x=progression['rounds'],
                    y=progression['points'],
                    mode='lines+markers',
                    name='Points',
                    line=dict(color='blue')
                ))
                fig_points.update_layout(
                    title="Points Progression Throughout Season",
                    xaxis_title="Round",
                    yaxis_title="Cumulative Points"
                )
                st.plotly_chart(fig_points, use_container_width=True)
            
            with col2:
                # Position progression
                fig_position = go.Figure()
                fig_position.add_trace(go.Scatter(
                    x=progression['rounds'],
                    y=progression['position'],
                    mode='lines+markers',
                    name='Championship Position',
                    line=dict(color='red')
                ))
                fig_position.update_layout(
                    title="Championship Position Throughout Season",
                    xaxis_title="Round",
                    yaxis_title="Championship Position",
                    yaxis=dict(autorange='reversed')  # Lower position numbers are better
                )
                st.plotly_chart(fig_position, use_container_width=True)
        else:
            st.info(f"No championship data found for {progression_driver} in {progression_season}.")

with tab4:
    st.header("🎯 Performance Details")
    
    # Performance metric selection
    metric_choice = st.selectbox(
        "Select Performance Metric",
        ["Points Distribution", "Grid Position Distribution", "Qualifying vs Race Performance"],
        key="performance_metric"
    )
    
    if metric_choice == "Points Distribution":
        if not filtered_results.empty:
            fig = create_performance_comparison(filtered_results, selected_drivers, 'points')
            st.plotly_chart(fig, use_container_width=True)
            
            # Points statistics
            points_stats = filtered_results.groupby('driver')['points'].describe()
            st.subheader("📊 Points Statistics")
            st.dataframe(points_stats, use_container_width=True)
    
    elif metric_choice == "Grid Position Distribution":
        if not filtered_results.empty:
            fig = create_performance_comparison(filtered_results, selected_drivers, 'grid')
            st.plotly_chart(fig, use_container_width=True)
            
            # Grid position statistics
            grid_stats = filtered_results.groupby('driver')['grid'].describe()
            st.subheader("📊 Grid Position Statistics")
            st.dataframe(grid_stats, use_container_width=True)
    
    elif metric_choice == "Qualifying vs Race Performance":
        selected_driver_for_qual = st.selectbox(
            "Select Driver for Qualifying Analysis",
            selected_drivers,
            key="qual_analysis_driver"
        )
        
        if selected_driver_for_qual:
            fig = create_qualifying_vs_race_analysis(qualifying, filtered_results, selected_driver_for_qual)
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("This chart shows the correlation between qualifying position (x-axis) and race finish position (y-axis). Points closer to the diagonal line indicate consistent performance from qualifying to race.")
    
    # Race results table
    st.subheader("🏁 Recent Race Results")
    
    # Show recent results for selected drivers
    recent_results = filtered_results.sort_values(['season', 'round'], ascending=[False, False]).head(50)
    
    display_results = recent_results[[
        'season', 'round', 'circuit_id', 'driver', 'constructor', 
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
            "constructor": "Constructor",
            "grid": st.column_config.NumberColumn("Finish Position", format="%.0f"),
            "points": st.column_config.NumberColumn("Points", format="%.1f"),
            "status": "Status"
        }
    )

with tab5:
    st.header("🏎️ 3D Performance Analysis")
    
    # 3D Championship Evolution
    st.subheader("🌟 3D Championship Evolution")
    st.info("💡 This 3D visualization shows how drivers' championship points evolved across rounds and seasons in three-dimensional space.")
    
    if not filtered_standings.empty and len(selected_drivers) > 0:
        evolution_3d_fig = create_3d_championship_evolution(
            filtered_standings, 
            selected_drivers[:5], 
            selected_seasons
        )
        st.plotly_chart(evolution_3d_fig, use_container_width=True)
    else:
        st.info("Select drivers and seasons to view 3D championship evolution.")
    
    # 3D Performance Radar
    st.subheader("🎯 3D Performance Radar")
    st.info("💡 Multi-dimensional radar chart comparing driver performance across key metrics.")
    
    if not filtered_results.empty and len(selected_drivers) > 0:
        driver_stats = calculate_driver_stats(filtered_results)
        
        if not driver_stats.empty:
            radar_3d_fig = create_performance_radar_3d(driver_stats, selected_drivers)
            st.plotly_chart(radar_3d_fig, use_container_width=True)
        else:
            st.info("No performance statistics available for selected drivers.")
    else:
        st.info("Select drivers to view 3D performance radar comparison.")
    
    # 3D Controls Guide
    st.subheader("🎮 3D Interaction Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Navigation Controls:**")
        st.write("• **Rotate:** Click and drag to rotate the 3D view")
        st.write("• **Zoom:** Use mouse wheel or pinch to zoom in/out")
        st.write("• **Pan:** Hold Shift and drag to pan the view")
        st.write("• **Reset:** Double-click to reset to default view")
        
    with col2:
        st.write("**Visualization Features:**")
        st.write("• **Championship Evolution:** Shows points progression in 3D space")
        st.write("• **Performance Radar:** Multi-metric comparison")
        st.write("• **Interactive Tooltips:** Hover for detailed information")
        st.write("• **Legend:** Click to show/hide specific drivers")

# Export data option
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export Analysis Data"):
    # Prepare export data
    export_data = calculate_driver_stats(filtered_results)
    csv = export_data.to_csv(index=False)
    
    st.sidebar.download_button(
        label="Download Driver Statistics CSV",
        data=csv,
        file_name=f"driver_analysis_{'-'.join(map(str, selected_seasons))}.csv",
        mime="text/csv"
    )
