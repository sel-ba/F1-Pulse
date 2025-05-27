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

from utils.data_loader import load_all_data, get_driver_list, get_constructor_list
from utils.visualization import create_weather_impact_chart
from utils.statistics import calculate_weather_impact

st.set_page_config(
    page_title="Weather Impact Analysis - F1 Analytics",
    page_icon="🌦️",
    layout="wide"
)

st.title("🌦️ Weather Impact Analysis")
st.markdown("### Understanding how weather conditions affect F1 performance")

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

# Check if weather data is available
if weather.empty:
    st.error("No weather data available for analysis.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Weather Analysis Filters")

# Season filter
available_seasons = sorted(results['season'].unique())
selected_seasons = st.sidebar.multiselect(
    "Select Seasons",
    available_seasons,
    default=available_seasons[-10:] if len(available_seasons) >= 10 else available_seasons
)

if not selected_seasons:
    st.warning("Please select at least one season to analyze.")
    st.stop()

# Filter data based on selected seasons
filtered_results = results[results['season'].isin(selected_seasons)]
filtered_weather = weather[weather['season'].isin(selected_seasons)]

# Merge weather data with results
merged_data = pd.merge(
    filtered_results,
    filtered_weather,
    on=['season', 'round', 'circuit_id'],
    how='inner'
)

if merged_data.empty:
    st.error("No matching weather and race result data found for the selected seasons.")
    st.stop()

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🌧️ Condition Analysis", "🏎️ Driver Performance", "🏗️ Constructor Impact"])

with tab1:
    st.header("📊 Weather Impact Overview")
    
    # Weather condition distribution
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        wet_races = merged_data['weather_wet'].sum()
        st.metric("Wet Races", wet_races)
    
    with col2:
        dry_races = merged_data['weather_dry'].sum()
        st.metric("Dry Races", dry_races)
    
    with col3:
        warm_races = merged_data['weather_warm'].sum()
        st.metric("Warm Races", warm_races)
    
    with col4:
        cold_races = merged_data['weather_cold'].sum()
        st.metric("Cold Races", cold_races)
    
    # Weather conditions distribution
    st.subheader("🌤️ Weather Conditions Distribution")
    
    # Create weather condition summary
    weather_summary = {
        'Condition': ['Wet', 'Dry', 'Warm', 'Cold', 'Cloudy'],
        'Count': [
            merged_data['weather_wet'].sum(),
            merged_data['weather_dry'].sum(),
            merged_data['weather_warm'].sum(),
            merged_data['weather_cold'].sum(),
            merged_data['weather_cloudy'].sum()
        ]
    }
    
    weather_df = pd.DataFrame(weather_summary)
    weather_df = weather_df[weather_df['Count'] > 0]  # Remove conditions with no data
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Weather distribution pie chart
        if not weather_df.empty:
            fig_weather_dist = px.pie(
                weather_df,
                values='Count',
                names='Condition',
                title="Weather Conditions Distribution"
            )
            st.plotly_chart(fig_weather_dist, use_container_width=True)
    
    with col2:
        # Weather by season
        weather_by_season = merged_data.groupby('season')[
            ['weather_wet', 'weather_dry', 'weather_warm', 'weather_cold', 'weather_cloudy']
        ].sum().reset_index()
        
        # Melt for easier plotting
        weather_melted = weather_by_season.melt(
            id_vars=['season'],
            value_vars=['weather_wet', 'weather_dry', 'weather_warm', 'weather_cold', 'weather_cloudy'],
            var_name='condition',
            value_name='count'
        )
        weather_melted['condition'] = weather_melted['condition'].str.replace('weather_', '')
        
        fig_weather_season = px.bar(
            weather_melted,
            x='season',
            y='count',
            color='condition',
            title="Weather Conditions by Season",
            labels={'count': 'Number of Races', 'season': 'Season'}
        )
        st.plotly_chart(fig_weather_season, use_container_width=True)
    
    # Overall weather impact on performance
    st.subheader("⚡ Weather Impact on Performance")
    
    # Calculate weather impact statistics
    weather_impact_stats = calculate_weather_impact(filtered_results, filtered_weather)
    
    if weather_impact_stats:
        impact_summary = []
        for condition, stats in weather_impact_stats.items():
            condition_name = condition.replace('weather_', '').title()
            impact_summary.append({
                'Condition': condition_name,
                'Avg Points With': f"{stats['mean_points_with_condition']:.2f}",
                'Avg Points Without': f"{stats['mean_points_without_condition']:.2f}",
                'Difference': f"{stats['difference']:.2f}",
                'P-Value': f"{stats['p_value']:.4f}",
                'Significant': "Yes" if stats['p_value'] < 0.05 else "No"
            })
        
        impact_df = pd.DataFrame(impact_summary)
        st.dataframe(impact_df, use_container_width=True)
        
        st.info("💡 **Interpretation**: A positive difference means better performance with the condition. P-value < 0.05 indicates statistical significance.")

with tab2:
    st.header("🌧️ Detailed Condition Analysis")
    
    # Weather condition selector
    condition_choice = st.selectbox(
        "Select Weather Condition to Analyze",
        ["Wet vs Dry", "Warm vs Cold", "Cloudy vs Clear"],
        key="condition_analysis"
    )
    
    if condition_choice == "Wet vs Dry":
        # Wet vs Dry analysis
        st.subheader("💧 Wet vs Dry Race Analysis")
        
        wet_data = merged_data[merged_data['weather_wet'] == True]
        dry_data = merged_data[merged_data['weather_dry'] == True]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wet_avg_points = wet_data['points'].mean()
            st.metric("Avg Points (Wet)", f"{wet_avg_points:.2f}")
        
        with col2:
            dry_avg_points = dry_data['points'].mean()
            st.metric("Avg Points (Dry)", f"{dry_avg_points:.2f}")
        
        with col3:
            difference = wet_avg_points - dry_avg_points
            st.metric("Difference", f"{difference:.2f}")
        
        # Points distribution comparison
        col1, col2 = st.columns(2)
        
        with col1:
            # Box plot comparison
            comparison_data = pd.concat([
                pd.DataFrame({'Points': wet_data['points'], 'Condition': 'Wet'}),
                pd.DataFrame({'Points': dry_data['points'], 'Condition': 'Dry'})
            ])
            
            fig_comparison = px.box(
                comparison_data,
                x='Condition',
                y='Points',
                title="Points Distribution: Wet vs Dry"
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with col2:
            # Win rate comparison
            wet_wins = wet_data['is_win'].sum() if 'is_win' in wet_data.columns else 0
            dry_wins = dry_data['is_win'].sum() if 'is_win' in dry_data.columns else 0
            wet_win_rate = (wet_wins / len(wet_data) * 100) if len(wet_data) > 0 else 0
            dry_win_rate = (dry_wins / len(dry_data) * 100) if len(dry_data) > 0 else 0
            
            win_rate_data = pd.DataFrame({
                'Condition': ['Wet', 'Dry'],
                'Win_Rate': [wet_win_rate, dry_win_rate]
            })
            
            fig_winrate = px.bar(
                win_rate_data,
                x='Condition',
                y='Win_Rate',
                title="Win Rate: Wet vs Dry (%)"
            )
            st.plotly_chart(fig_winrate, use_container_width=True)
    
    elif condition_choice == "Warm vs Cold":
        # Warm vs Cold analysis
        st.subheader("🌡️ Warm vs Cold Weather Analysis")
        
        warm_data = merged_data[merged_data['weather_warm'] == True]
        cold_data = merged_data[merged_data['weather_cold'] == True]
        
        if not warm_data.empty and not cold_data.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                warm_avg_points = warm_data['points'].mean()
                st.metric("Avg Points (Warm)", f"{warm_avg_points:.2f}")
            
            with col2:
                cold_avg_points = cold_data['points'].mean()
                st.metric("Avg Points (Cold)", f"{cold_avg_points:.2f}")
            
            with col3:
                difference = warm_avg_points - cold_avg_points
                st.metric("Difference", f"{difference:.2f}")
            
            # Temperature impact visualization
            comparison_data = pd.concat([
                pd.DataFrame({'Points': warm_data['points'], 'Temperature': 'Warm'}),
                pd.DataFrame({'Points': cold_data['points'], 'Temperature': 'Cold'})
            ])
            
            fig_temp = px.violin(
                comparison_data,
                x='Temperature',
                y='Points',
                title="Points Distribution by Temperature"
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Insufficient data for warm vs cold comparison.")
    
    elif condition_choice == "Cloudy vs Clear":
        # Cloudy vs Clear analysis
        st.subheader("☁️ Cloudy vs Clear Weather Analysis")
        
        cloudy_data = merged_data[merged_data['weather_cloudy'] == True]
        clear_data = merged_data[merged_data['weather_cloudy'] == False]
        
        if not cloudy_data.empty and not clear_data.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cloudy_avg_points = cloudy_data['points'].mean()
                st.metric("Avg Points (Cloudy)", f"{cloudy_avg_points:.2f}")
            
            with col2:
                clear_avg_points = clear_data['points'].mean()
                st.metric("Avg Points (Clear)", f"{clear_avg_points:.2f}")
            
            with col3:
                difference = cloudy_avg_points - clear_avg_points
                st.metric("Difference", f"{difference:.2f}")
            
            # Cloud cover impact
            comparison_data = pd.concat([
                pd.DataFrame({'Points': cloudy_data['points'], 'Sky': 'Cloudy'}),
                pd.DataFrame({'Points': clear_data['points'], 'Sky': 'Clear'})
            ])
            
            fig_cloud = px.histogram(
                comparison_data,
                x='Points',
                color='Sky',
                title="Points Distribution: Cloudy vs Clear",
                barmode='overlay',
                opacity=0.7
            )
            st.plotly_chart(fig_cloud, use_container_width=True)
        else:
            st.info("Insufficient data for cloudy vs clear comparison.")

with tab3:
    st.header("🏎️ Driver Performance in Different Conditions")
    
    # Driver selection
    available_drivers = get_driver_list(data)
    # Filter drivers who have races in wet conditions
    wet_drivers = merged_data[merged_data['weather_wet'] == True]['driver'].unique()
    relevant_drivers = [d for d in available_drivers if d in wet_drivers]
    
    selected_drivers = st.multiselect(
        "Select Drivers for Weather Analysis",
        relevant_drivers,
        default=relevant_drivers[:5] if len(relevant_drivers) >= 5 else relevant_drivers
    )
    
    if selected_drivers:
        # Driver weather performance analysis
        driver_weather_stats = []
        
        for driver in selected_drivers:
            driver_data = merged_data[merged_data['driver'] == driver]
            
            wet_races = driver_data[driver_data['weather_wet'] == True]
            dry_races = driver_data[driver_data['weather_dry'] == True]
            
            stats = {
                'Driver': driver,
                'Wet_Races': len(wet_races),
                'Dry_Races': len(dry_races),
                'Wet_Avg_Points': wet_races['points'].mean() if len(wet_races) > 0 else 0,
                'Dry_Avg_Points': dry_races['points'].mean() if len(dry_races) > 0 else 0,
                'Wet_Wins': wet_races['is_win'].sum() if 'is_win' in wet_races.columns and len(wet_races) > 0 else 0,
                'Dry_Wins': dry_races['is_win'].sum() if 'is_win' in dry_races.columns and len(dry_races) > 0 else 0
            }
            
            # Calculate wet weather advantage
            if stats['Dry_Avg_Points'] > 0:
                stats['Wet_Advantage'] = (stats['Wet_Avg_Points'] - stats['Dry_Avg_Points']) / stats['Dry_Avg_Points'] * 100
            else:
                stats['Wet_Advantage'] = 0
            
            driver_weather_stats.append(stats)
        
        driver_weather_df = pd.DataFrame(driver_weather_stats)
        
        st.subheader("💧 Driver Wet Weather Performance")
        
        # Driver statistics table
        display_cols = ['Driver', 'Wet_Races', 'Dry_Races', 'Wet_Avg_Points', 'Dry_Avg_Points', 'Wet_Advantage']
        display_df = driver_weather_df[display_cols].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Driver": "Driver",
                "Wet_Races": st.column_config.NumberColumn("Wet Races", format="%.0f"),
                "Dry_Races": st.column_config.NumberColumn("Dry Races", format="%.0f"),
                "Wet_Avg_Points": st.column_config.NumberColumn("Avg Points (Wet)", format="%.2f"),
                "Dry_Avg_Points": st.column_config.NumberColumn("Avg Points (Dry)", format="%.2f"),
                "Wet_Advantage": st.column_config.NumberColumn("Wet Weather Advantage (%)", format="%.1f")
            }
        )
        
        # Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Wet weather specialists
            fig_wet_specialist = px.bar(
                driver_weather_df.sort_values('Wet_Advantage', ascending=False),
                x='Wet_Advantage',
                y='Driver',
                orientation='h',
                title="Wet Weather Advantage by Driver (%)",
                labels={'Wet_Advantage': 'Advantage (%)', 'Driver': 'Driver'}
            )
            fig_wet_specialist.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_wet_specialist, use_container_width=True)
        
        with col2:
            # Wet vs dry points comparison
            comparison_data = pd.melt(
                driver_weather_df,
                id_vars=['Driver'],
                value_vars=['Wet_Avg_Points', 'Dry_Avg_Points'],
                var_name='Condition',
                value_name='Avg_Points'
            )
            comparison_data['Condition'] = comparison_data['Condition'].str.replace('_Avg_Points', '').str.replace('_', ' ')
            
            fig_comparison = px.bar(
                comparison_data,
                x='Driver',
                y='Avg_Points',
                color='Condition',
                title="Average Points: Wet vs Dry",
                barmode='group'
            )
            fig_comparison.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.info("Please select drivers to analyze their weather performance.")

with tab4:
    st.header("🏗️ Constructor Weather Impact")
    
    # Constructor weather performance
    available_constructors = get_constructor_list(data)
    # Filter constructors who have races in wet conditions
    wet_constructors = merged_data[merged_data['weather_wet'] == True]['constructor'].unique()
    relevant_constructors = [c for c in available_constructors if c in wet_constructors]
    
    selected_constructors = st.multiselect(
        "Select Constructors for Weather Analysis",
        relevant_constructors,
        default=relevant_constructors[:8] if len(relevant_constructors) >= 8 else relevant_constructors
    )
    
    if selected_constructors:
        # Constructor weather performance analysis
        constructor_weather_stats = []
        
        for constructor in selected_constructors:
            constructor_data = merged_data[merged_data['constructor'] == constructor]
            
            wet_races = constructor_data[constructor_data['weather_wet'] == True]
            dry_races = constructor_data[constructor_data['weather_dry'] == True]
            
            stats = {
                'Constructor': constructor,
                'Wet_Races': len(wet_races),
                'Dry_Races': len(dry_races),
                'Wet_Avg_Points': wet_races['points'].mean() if len(wet_races) > 0 else 0,
                'Dry_Avg_Points': dry_races['points'].mean() if len(dry_races) > 0 else 0,
                'Wet_Total_Points': wet_races['points'].sum(),
                'Dry_Total_Points': dry_races['points'].sum()
            }
            
            # Calculate reliability in different conditions
            if stats['Dry_Avg_Points'] > 0:
                stats['Wet_Performance_Ratio'] = stats['Wet_Avg_Points'] / stats['Dry_Avg_Points']
            else:
                stats['Wet_Performance_Ratio'] = 0
            
            constructor_weather_stats.append(stats)
        
        constructor_weather_df = pd.DataFrame(constructor_weather_stats)
        
        st.subheader("🏭 Constructor Weather Performance Analysis")
        
        # Constructor statistics
        display_df = constructor_weather_df[[
            'Constructor', 'Wet_Races', 'Dry_Races', 'Wet_Avg_Points', 
            'Dry_Avg_Points', 'Wet_Performance_Ratio'
        ]].round(3)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Constructor": "Constructor",
                "Wet_Races": st.column_config.NumberColumn("Wet Races", format="%.0f"),
                "Dry_Races": st.column_config.NumberColumn("Dry Races", format="%.0f"),
                "Wet_Avg_Points": st.column_config.NumberColumn("Avg Points (Wet)", format="%.2f"),
                "Dry_Avg_Points": st.column_config.NumberColumn("Avg Points (Dry)", format="%.2f"),
                "Wet_Performance_Ratio": st.column_config.NumberColumn("Wet/Dry Ratio", format="%.3f")
            }
        )
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Wet weather performance ratio
            fig_ratio = px.bar(
                constructor_weather_df.sort_values('Wet_Performance_Ratio', ascending=False),
                x='Constructor',
                y='Wet_Performance_Ratio',
                title="Wet/Dry Performance Ratio by Constructor",
                labels={'Wet_Performance_Ratio': 'Wet/Dry Ratio', 'Constructor': 'Constructor'}
            )
            fig_ratio.update_layout(xaxis_tickangle=-45)
            fig_ratio.add_hline(y=1, line_dash="dash", line_color="red", 
                              annotation_text="Equal Performance Line")
            st.plotly_chart(fig_ratio, use_container_width=True)
        
        with col2:
            # Total points comparison
            comparison_data = pd.melt(
                constructor_weather_df,
                id_vars=['Constructor'],
                value_vars=['Wet_Total_Points', 'Dry_Total_Points'],
                var_name='Condition',
                value_name='Total_Points'
            )
            comparison_data['Condition'] = comparison_data['Condition'].str.replace('_Total_Points', '')
            
            fig_total = px.bar(
                comparison_data,
                x='Constructor',
                y='Total_Points',
                color='Condition',
                title="Total Points: Wet vs Dry Conditions",
                barmode='group'
            )
            fig_total.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_total, use_container_width=True)
        
        # Weather impact insights
        st.subheader("💡 Weather Impact Insights")
        
        best_wet_constructor = constructor_weather_df.loc[constructor_weather_df['Wet_Performance_Ratio'].idxmax()]
        worst_wet_constructor = constructor_weather_df.loc[constructor_weather_df['Wet_Performance_Ratio'].idxmin()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Best Wet Weather Performance**: {best_wet_constructor['Constructor']} (Ratio: {best_wet_constructor['Wet_Performance_Ratio']:.3f})")
        
        with col2:
            st.info(f"**Most Affected by Wet Weather**: {worst_wet_constructor['Constructor']} (Ratio: {worst_wet_constructor['Wet_Performance_Ratio']:.3f})")
    else:
        st.info("Please select constructors to analyze their weather performance.")

# Export weather analysis
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export Weather Analysis"):
    if 'merged_data' in locals():
        # Create weather summary
        weather_summary = merged_data.groupby(['season', 'round', 'circuit_id']).agg({
            'weather_wet': 'first',
            'weather_dry': 'first',
            'weather_warm': 'first',
            'weather_cold': 'first',
            'weather_cloudy': 'first',
            'points': 'mean'
        }).reset_index()
        
        csv = weather_summary.to_csv(index=False)
        
        st.sidebar.download_button(
            label="Download Weather Analysis CSV",
            data=csv,
            file_name=f"weather_analysis_{'-'.join(map(str, selected_seasons))}.csv",
            mime="text/csv"
        )
