import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from utils.data_loader import load_all_data
from utils.visualization import create_championship_evolution_chart, create_performance_comparison
from utils.statistics import calculate_driver_stats, calculate_constructor_stats

# Page configuration
st.set_page_config(
    page_title="F1 Analytics Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def get_data():
    return load_all_data()

def main():
    st.title("🏎️ Formula 1 Analytics Dashboard")
    st.markdown("### Comprehensive F1 Performance Analysis")
    
    # Load data
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
    st.sidebar.header("🔍 Filters")
    
    # Season filter
    available_seasons = sorted(driver_standings['season'].unique())
    selected_seasons = st.sidebar.multiselect(
        "Select Seasons",
        available_seasons,
        default=available_seasons[-5:] if len(available_seasons) >= 5 else available_seasons
    )
    
    if not selected_seasons:
        st.warning("Please select at least one season to display data.")
        st.stop()
    
    # Filter data based on selected seasons
    filtered_standings = driver_standings[driver_standings['season'].isin(selected_seasons)]
    filtered_results = results[results['season'].isin(selected_seasons)]
    filtered_qualifying = qualifying[qualifying['season'].isin(selected_seasons)]
    
    # Overview metrics
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_races = len(filtered_results['season'].astype(str) + '_' + filtered_results['round'].astype(str) + '_' + filtered_results['circuit_id'])
        st.metric("Total Races", f"{total_races:,}")
    
    with col2:
        unique_drivers = filtered_results['driver'].nunique()
        st.metric("Unique Drivers", unique_drivers)
    
    with col3:
        unique_constructors = filtered_results['constructor'].nunique()
        st.metric("Constructors", unique_constructors)
    
    with col4:
        unique_circuits = filtered_results['circuit_id'].nunique()
        st.metric("Circuits", unique_circuits)
    
    # Championship Evolution
    st.header("🏆 Championship Evolution")
    
    # Get final standings for selected seasons
    final_standings = []
    for season in selected_seasons:
        season_data = filtered_standings[filtered_standings['season'] == season]
        if not season_data.empty:
            max_round = season_data['round'].max()
            final_round_data = season_data[season_data['round'] == max_round]
            champions = final_round_data[final_round_data['driver_standings_pos_after_race'] == 1]
            if not champions.empty:
                champion = champions.iloc[0]
                final_standings.append({
                    'season': season,
                    'champion': champion['driver'],
                    'points': champion['driver_points_after_race'],
                    'wins': champion['driver_wins_after_race']
                })
    
    if len(final_standings) > 0:
        champions_df = pd.DataFrame(final_standings)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Champions by season
            fig_champions = px.bar(
                champions_df,
                x='season',
                y='points',
                color='champion',
                title="World Champions by Season",
                labels={'points': 'Championship Points', 'season': 'Season'}
            )
            fig_champions.update_layout(showlegend=False)
            st.plotly_chart(fig_champions, use_container_width=True)
        
        with col2:
            # Championship wins distribution
            wins_count = champions_df['champion'].value_counts()
            fig_wins = px.pie(
                values=wins_count.values,
                names=wins_count.index,
                title="Championship Distribution"
            )
            st.plotly_chart(fig_wins, use_container_width=True)
    
    # Recent Performance Trends
    st.header("📈 Recent Performance Trends")
    
    if len(selected_seasons) >= 2:
        # Get top drivers from the most recent season
        latest_season = max(selected_seasons)
        latest_standings = filtered_standings[filtered_standings['season'] == latest_season]
        
        if not latest_standings.empty:
            max_round = latest_standings['round'].max()
            final_standings = latest_standings[latest_standings['round'] == max_round]
            top_drivers = final_standings.nsmallest(10, 'driver_standings_pos_after_race')['driver'].tolist()
            
            # Create evolution chart for top drivers
            evolution_fig = create_championship_evolution_chart(
                filtered_standings, 
                top_drivers[:5], 
                selected_seasons
            )
            st.plotly_chart(evolution_fig, use_container_width=True)
    
    # Performance Analysis
    st.header("🎯 Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Win rate analysis
        driver_stats = calculate_driver_stats(filtered_results)
        top_winners = driver_stats.nlargest(10, 'win_rate')
        
        fig_winrate = px.bar(
            top_winners,
            x='win_rate',
            y='driver',
            orientation='h',
            title="Top 10 Win Rates",
            labels={'win_rate': 'Win Rate (%)', 'driver': 'Driver'}
        )
        fig_winrate.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_winrate, use_container_width=True)
    
    with col2:
        # Podium rate analysis
        fig_podium = px.bar(
            top_winners,
            x='podium_rate',
            y='driver',
            orientation='h',
            title="Top 10 Podium Rates",
            labels={'podium_rate': 'Podium Rate (%)', 'driver': 'Driver'}
        )
        fig_podium.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_podium, use_container_width=True)
    
    # Constructor Performance
    st.header("🏗️ Constructor Performance")
    
    constructor_stats = calculate_constructor_stats(filtered_results)
    top_constructors = constructor_stats.nlargest(10, 'total_points')
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_const_points = px.bar(
            top_constructors,
            x='total_points',
            y='constructor',
            orientation='h',
            title="Constructor Points",
            labels={'total_points': 'Total Points', 'constructor': 'Constructor'}
        )
        fig_const_points.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_const_points, use_container_width=True)
    
    with col2:
        fig_const_wins = px.bar(
            top_constructors,
            x='total_wins',
            y='constructor',
            orientation='h',
            title="Constructor Wins",
            labels={'total_wins': 'Total Wins', 'constructor': 'Constructor'}
        )
        fig_const_wins.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_const_wins, use_container_width=True)
    
    # Key Insights
    st.header("💡 Key Insights")
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.subheader("🏆 Championship Insights")
        if len(final_standings) > 0:
            latest_champion = champions_df[champions_df['season'] == max(champions_df['season'])].iloc[0]
            st.write(f"**Current Champion:** {latest_champion['champion']}")
            st.write(f"**Championship Points:** {latest_champion['points']:.0f}")
            st.write(f"**Season Wins:** {latest_champion['wins']:.0f}")
            
            # Most successful driver in selected period
            if len(champions_df) > 1:
                most_titles = champions_df['champion'].value_counts().index[0]
                title_count = champions_df['champion'].value_counts().iloc[0]
                st.write(f"**Most Titles:** {most_titles} ({title_count})")
    
    with insights_col2:
        st.subheader("📊 Performance Statistics")
        if not driver_stats.empty:
            highest_win_rate = driver_stats.loc[driver_stats['win_rate'].idxmax()]
            st.write(f"**Highest Win Rate:** {highest_win_rate['driver']} ({highest_win_rate['win_rate']:.1f}%)")
            
            most_races = driver_stats.loc[driver_stats['total_races'].idxmax()]
            st.write(f"**Most Races:** {most_races['driver']} ({most_races['total_races']:.0f})")
            
            most_points = driver_stats.loc[driver_stats['total_points'].idxmax()]
            st.write(f"**Most Points:** {most_points['driver']} ({most_points['total_points']:.0f})")
    
    # Navigation help
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Navigation")
    st.sidebar.markdown("Use the pages in the sidebar to explore:")
    st.sidebar.markdown("- **Driver Analysis**: Detailed driver comparisons")
    st.sidebar.markdown("- **Constructor Analysis**: Team performance insights")
    st.sidebar.markdown("- **Weather Impact**: Weather correlation analysis")
    st.sidebar.markdown("- **Circuit Analysis**: Track-specific performance")

if __name__ == "__main__":
    main()
