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

from utils.data_loader import load_all_data, get_circuit_list, get_driver_list, get_constructor_list
from utils.visualization import create_circuit_performance_map
from utils.statistics import calculate_circuit_stats

st.set_page_config(
    page_title="Circuit Analysis - F1 Analytics",
    page_icon="🏁",
    layout="wide"
)

st.title("🏁 Circuit Analysis")
st.markdown("### Track-specific performance insights and venue analysis")

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
st.sidebar.header("🔍 Circuit Analysis Filters")

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

# Circuit selection
available_circuits = get_circuit_list(data)
selected_circuits = st.sidebar.multiselect(
    "Select Circuits for Analysis",
    available_circuits,
    default=available_circuits[:10] if len(available_circuits) >= 10 else available_circuits[:5]
)

if not selected_circuits:
    st.warning("Please select at least one circuit to analyze.")
    st.stop()

# Filter data
filtered_results = results[
    (results['season'].isin(selected_seasons)) & 
    (results['circuit_id'].isin(selected_circuits))
]

filtered_races = races[
    (races['season'].isin(selected_seasons)) & 
    (races['circuit_id'].isin(selected_circuits))
]

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Circuit Performance", "🏎️ Driver Performance", "🏆 Historical Analysis"])

with tab1:
    st.header("📊 Circuit Overview")
    
    # Calculate circuit statistics
    circuit_stats = calculate_circuit_stats(filtered_results, filtered_races)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_races = len(filtered_results)
        st.metric("Total Races Analyzed", f"{total_races:,}")
    
    with col2:
        unique_circuits = filtered_results['circuit_id'].nunique()
        st.metric("Circuits", unique_circuits)
    
    with col3:
        countries = filtered_races['country'].nunique() if 'country' in filtered_races.columns else 0
        st.metric("Countries", countries)
    
    with col4:
        seasons_span = len(selected_seasons)
        st.metric("Seasons Analyzed", seasons_span)
    
    # Circuit statistics table
    st.subheader("📋 Circuit Statistics")
    
    if not circuit_stats.empty:
        # Select key columns for display
        display_stats = circuit_stats[[
            'circuit_id', 'country', 'total_points', 'total_wins', 'total_podiums',
            'avg_points_per_race', 'unique_drivers', 'seasons_featured'
        ]].copy()
        
        # Sort by total points
        display_stats = display_stats.sort_values('total_points', ascending=False)
        
        st.dataframe(
            display_stats,
            use_container_width=True,
            column_config={
                "circuit_id": "Circuit",
                "country": "Country",
                "total_points": st.column_config.NumberColumn("Total Points", format="%.0f"),
                "total_wins": st.column_config.NumberColumn("Wins", format="%.0f"),
                "total_podiums": st.column_config.NumberColumn("Podiums", format="%.0f"),
                "avg_points_per_race": st.column_config.NumberColumn("Avg Points/Race", format="%.1f"),
                "unique_drivers": st.column_config.NumberColumn("Unique Drivers", format="%.0f"),
                "seasons_featured": st.column_config.NumberColumn("Seasons Featured", format="%.0f")
            }
        )
    
    # Circuit activity visualization
    st.subheader("🏎️ Circuit Activity Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Races by circuit
        if not circuit_stats.empty:
            races_by_circuit = circuit_stats.nlargest(15, 'seasons_featured')
            fig_races = px.bar(
                races_by_circuit,
                x='circuit_id',
                y='seasons_featured',
                title="Seasons Featured by Circuit",
                labels={'seasons_featured': 'Seasons Featured', 'circuit_id': 'Circuit'}
            )
            fig_races.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_races, use_container_width=True)
    
    with col2:
        # Countries representation
        if 'country' in filtered_races.columns:
            country_counts = filtered_races['country'].value_counts().head(10)
            fig_countries = px.pie(
                values=country_counts.values,
                names=country_counts.index,
                title="Races by Country"
            )
            st.plotly_chart(fig_countries, use_container_width=True)

with tab2:
    st.header("🗺️ Circuit Performance Analysis")
    
    # Circuit performance map
    st.subheader("🌍 Global Circuit Performance Map")
    
    if not filtered_races.empty and 'lat' in filtered_races.columns and 'long' in filtered_races.columns:
        try:
            map_fig = create_circuit_performance_map(filtered_races, filtered_results, 'points')
            st.plotly_chart(map_fig, use_container_width=True)
        except Exception as e:
            st.info("Map visualization not available. Showing alternative analysis.")
    
    # Circuit performance comparison
    st.subheader("📊 Circuit Performance Comparison")
    
    # Select specific circuit for detailed analysis
    selected_circuit = st.selectbox(
        "Select Circuit for Detailed Analysis",
        selected_circuits
    )
    
    if selected_circuit:
        circuit_data = filtered_results[filtered_results['circuit_id'] == selected_circuit]
        
        if not circuit_data.empty:
            st.subheader(f"🏁 {selected_circuit.replace('_', ' ').title()} - Performance Analysis")
            
            # Circuit metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_races_circuit = len(circuit_data)
            total_points_circuit = circuit_data['points'].sum()
            avg_points_circuit = circuit_data['points'].mean()
            unique_winners = circuit_data[circuit_data['is_win'] == True]['driver'].nunique() if 'is_win' in circuit_data.columns else 0
            
            with col1:
                st.metric("Total Races", total_races_circuit)
            with col2:
                st.metric("Total Points", f"{total_points_circuit:.0f}")
            with col3:
                st.metric("Avg Points/Race", f"{avg_points_circuit:.2f}")
            with col4:
                st.metric("Different Winners", unique_winners)
            
            # Performance analysis charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Points distribution at this circuit
                fig_points_dist = px.histogram(
                    circuit_data,
                    x='points',
                    title=f"Points Distribution at {selected_circuit.replace('_', ' ').title()}",
                    labels={'points': 'Points Scored', 'count': 'Frequency'}
                )
                st.plotly_chart(fig_points_dist, use_container_width=True)
            
            with col2:
                # Top performers at this circuit
                top_performers = circuit_data.groupby('driver').agg({
                    'points': 'sum',
                    'is_win': 'sum' if 'is_win' in circuit_data.columns else lambda x: 0
                }).sort_values('points', ascending=False).head(10)
                
                fig_top_performers = px.bar(
                    top_performers.reset_index(),
                    x='driver',
                    y='points',
                    title=f"Top Point Scorers at {selected_circuit.replace('_', ' ').title()}",
                    labels={'points': 'Total Points', 'driver': 'Driver'}
                )
                fig_top_performers.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_top_performers, use_container_width=True)
            
            # Constructor performance at circuit
            st.subheader(f"🏗️ Constructor Performance at {selected_circuit.replace('_', ' ').title()}")
            
            constructor_performance = circuit_data.groupby('constructor').agg({
                'points': ['sum', 'mean', 'count'],
                'is_win': 'sum' if 'is_win' in circuit_data.columns else lambda x: 0,
                'is_podium': 'sum' if 'is_podium' in circuit_data.columns else lambda x: 0
            }).round(2)
            
            # Flatten column names
            constructor_performance.columns = ['_'.join(col).strip() for col in constructor_performance.columns]
            constructor_performance = constructor_performance.reset_index()
            
            # Rename columns
            column_mapping = {
                'points_sum': 'Total_Points',
                'points_mean': 'Avg_Points',
                'points_count': 'Races',
                'is_win_sum': 'Wins',
                'is_podium_sum': 'Podiums'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in constructor_performance.columns:
                    constructor_performance = constructor_performance.rename(columns={old_col: new_col})
            
            # Sort by total points and display top constructors
            constructor_performance = constructor_performance.sort_values('Total_Points', ascending=False).head(10)
            st.dataframe(constructor_performance, use_container_width=True)
            
            # Performance over seasons at this circuit
            st.subheader(f"📈 Performance Trends at {selected_circuit.replace('_', ' ').title()}")
            
            seasonal_performance = circuit_data.groupby('season').agg({
                'points': 'mean',
                'is_win': 'sum' if 'is_win' in circuit_data.columns else lambda x: 0,
                'grid': 'mean'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Average points by season
                fig_seasonal_points = px.line(
                    seasonal_performance,
                    x='season',
                    y='points',
                    title=f"Average Points by Season at {selected_circuit.replace('_', ' ').title()}",
                    markers=True
                )
                st.plotly_chart(fig_seasonal_points, use_container_width=True)
            
            with col2:
                # Average finishing position by season
                fig_seasonal_grid = px.line(
                    seasonal_performance,
                    x='season',
                    y='grid',
                    title=f"Average Finish Position by Season",
                    markers=True
                )
                fig_seasonal_grid.update_layout(yaxis={'autorange': 'reversed'})  # Lower position is better
                st.plotly_chart(fig_seasonal_grid, use_container_width=True)
        else:
            st.info(f"No data available for {selected_circuit} in the selected seasons.")

with tab3:
    st.header("🏎️ Driver Performance by Circuit")
    
    # Driver selection
    available_drivers = get_driver_list(data)
    # Filter drivers who have raced at selected circuits
    circuit_drivers = filtered_results['driver'].unique()
    relevant_drivers = [d for d in available_drivers if d in circuit_drivers]
    
    selected_driver = st.selectbox(
        "Select Driver for Circuit Analysis",
        relevant_drivers
    )
    
    if selected_driver:
        driver_circuit_data = filtered_results[filtered_results['driver'] == selected_driver]
        
        st.subheader(f"🏎️ {selected_driver} - Circuit Performance Analysis")
        
        # Driver circuit statistics
        driver_circuit_stats = driver_circuit_data.groupby('circuit_id').agg({
            'points': ['sum', 'mean', 'count'],
            'is_win': 'sum' if 'is_win' in driver_circuit_data.columns else lambda x: 0,
            'is_podium': 'sum' if 'is_podium' in driver_circuit_data.columns else lambda x: 0,
            'grid': 'mean'
        }).round(2)
        
        # Flatten column names
        driver_circuit_stats.columns = ['_'.join(col).strip() for col in driver_circuit_stats.columns]
        driver_circuit_stats = driver_circuit_stats.reset_index()
        
        # Rename columns
        column_mapping = {
            'points_sum': 'Total_Points',
            'points_mean': 'Avg_Points',
            'points_count': 'Races',
            'is_win_sum': 'Wins',
            'is_podium_sum': 'Podiums',
            'grid_mean': 'Avg_Finish_Position'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in driver_circuit_stats.columns:
                driver_circuit_stats = driver_circuit_stats.rename(columns={old_col: new_col})
        
        # Calculate win rate and podium rate
        if 'Races' in driver_circuit_stats.columns:
            driver_circuit_stats['Win_Rate'] = (driver_circuit_stats.get('Wins', 0) / driver_circuit_stats['Races'] * 100).round(1)
            driver_circuit_stats['Podium_Rate'] = (driver_circuit_stats.get('Podiums', 0) / driver_circuit_stats['Races'] * 100).round(1)
        
        # Sort by total points
        driver_circuit_stats = driver_circuit_stats.sort_values('Total_Points', ascending=False)
        
        st.dataframe(
            driver_circuit_stats,
            use_container_width=True,
            column_config={
                "circuit_id": "Circuit",
                "Total_Points": st.column_config.NumberColumn("Total Points", format="%.0f"),
                "Avg_Points": st.column_config.NumberColumn("Avg Points", format="%.1f"),
                "Races": st.column_config.NumberColumn("Races", format="%.0f"),
                "Wins": st.column_config.NumberColumn("Wins", format="%.0f"),
                "Podiums": st.column_config.NumberColumn("Podiums", format="%.0f"),
                "Win_Rate": st.column_config.NumberColumn("Win Rate (%)", format="%.1f"),
                "Podium_Rate": st.column_config.NumberColumn("Podium Rate (%)", format="%.1f"),
                "Avg_Finish_Position": st.column_config.NumberColumn("Avg Finish", format="%.1f")
            }
        )
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Best circuits for the driver (by average points)
            best_circuits = driver_circuit_stats[driver_circuit_stats['Races'] >= 2].nlargest(10, 'Avg_Points')
            if not best_circuits.empty:
                fig_best = px.bar(
                    best_circuits,
                    x='circuit_id',
                    y='Avg_Points',
                    title=f"{selected_driver}'s Best Circuits (Avg Points)",
                    labels={'Avg_Points': 'Average Points', 'circuit_id': 'Circuit'}
                )
                fig_best.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_best, use_container_width=True)
        
        with col2:
            # Win rate by circuit
            circuits_with_wins = driver_circuit_stats[driver_circuit_stats.get('Wins', 0) > 0]
            if not circuits_with_wins.empty:
                fig_wins = px.bar(
                    circuits_with_wins,
                    x='circuit_id',
                    y='Win_Rate',
                    title=f"{selected_driver}'s Win Rate by Circuit (%)",
                    labels={'Win_Rate': 'Win Rate (%)', 'circuit_id': 'Circuit'}
                )
                fig_wins.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_wins, use_container_width=True)
            else:
                st.info("No wins recorded for this driver at selected circuits.")
        
        # Driver's strongest and weakest circuits
        st.subheader(f"💡 {selected_driver}'s Circuit Insights")
        
        if not driver_circuit_stats.empty:
            # Filter circuits with multiple races for more reliable statistics
            reliable_stats = driver_circuit_stats[driver_circuit_stats['Races'] >= 2]
            
            if not reliable_stats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    strongest_circuit = reliable_stats.loc[reliable_stats['Avg_Points'].idxmax()]
                    st.success(f"**Strongest Circuit**: {strongest_circuit['circuit_id'].replace('_', ' ').title()}")
                    st.write(f"- Average Points: {strongest_circuit['Avg_Points']:.1f}")
                    st.write(f"- Races: {strongest_circuit['Races']:.0f}")
                    st.write(f"- Win Rate: {strongest_circuit.get('Win_Rate', 0):.1f}%")
                
                with col2:
                    weakest_circuit = reliable_stats.loc[reliable_stats['Avg_Points'].idxmin()]
                    st.warning(f"**Needs Improvement**: {weakest_circuit['circuit_id'].replace('_', ' ').title()}")
                    st.write(f"- Average Points: {weakest_circuit['Avg_Points']:.1f}")
                    st.write(f"- Races: {weakest_circuit['Races']:.0f}")
                    st.write(f"- Win Rate: {weakest_circuit.get('Win_Rate', 0):.1f}%")

with tab4:
    st.header("🏆 Historical Circuit Analysis")
    
    # Historical trends
    st.subheader("📈 Historical Performance Trends")
    
    # Circuit popularity over time
    circuit_by_season = filtered_results.groupby(['season', 'circuit_id']).size().reset_index(name='races')
    
    # Most frequently used circuits
    circuit_frequency = circuit_by_season.groupby('circuit_id')['races'].sum().sort_values(ascending=False).head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most popular circuits
        fig_popularity = px.bar(
            x=circuit_frequency.values,
            y=circuit_frequency.index,
            orientation='h',
            title="Most Frequently Used Circuits",
            labels={'x': 'Total Races', 'y': 'Circuit'}
        )
        fig_popularity.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_popularity, use_container_width=True)
    
    with col2:
        # Circuit usage timeline
        top_circuits = circuit_frequency.head(5).index.tolist()
        timeline_data = circuit_by_season[circuit_by_season['circuit_id'].isin(top_circuits)]
        
        fig_timeline = px.line(
            timeline_data,
            x='season',
            y='races',
            color='circuit_id',
            title="Circuit Usage Over Time (Top 5)",
            labels={'races': 'Races per Season', 'season': 'Season'}
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Competitive analysis
    st.subheader("🎯 Circuit Competitiveness Analysis")
    
    # Calculate competitiveness metrics
    competitiveness_stats = []
    
    for circuit in selected_circuits:
        circuit_data = filtered_results[filtered_results['circuit_id'] == circuit]
        
        if len(circuit_data) >= 10:  # Minimum races for meaningful analysis
            # Calculate standard deviation of points (lower = more predictable)
            points_std = circuit_data['points'].std()
            
            # Number of different winners
            different_winners = circuit_data[circuit_data['is_win'] == True]['driver'].nunique() if 'is_win' in circuit_data.columns else 0
            
            # Number of different podium finishers
            different_podium = circuit_data[circuit_data['is_podium'] == True]['driver'].nunique() if 'is_podium' in circuit_data.columns else 0
            
            total_races = len(circuit_data)
            
            competitiveness_stats.append({
                'Circuit': circuit,
                'Total_Races': total_races,
                'Points_Std': points_std,
                'Different_Winners': different_winners,
                'Different_Podium': different_podium,
                'Winner_Diversity': (different_winners / total_races * 100) if total_races > 0 else 0,
                'Podium_Diversity': (different_podium / total_races * 100) if total_races > 0 else 0
            })
    
    if competitiveness_stats:
        comp_df = pd.DataFrame(competitiveness_stats)
        comp_df = comp_df.round(2)
        
        st.subheader("📊 Circuit Competitiveness Metrics")
        
        display_comp = comp_df[[
            'Circuit', 'Total_Races', 'Different_Winners', 'Different_Podium',
            'Winner_Diversity', 'Podium_Diversity', 'Points_Std'
        ]]
        
        st.dataframe(
            display_comp,
            use_container_width=True,
            column_config={
                "Circuit": "Circuit",
                "Total_Races": st.column_config.NumberColumn("Total Races", format="%.0f"),
                "Different_Winners": st.column_config.NumberColumn("Different Winners", format="%.0f"),
                "Different_Podium": st.column_config.NumberColumn("Different Podium", format="%.0f"),
                "Winner_Diversity": st.column_config.NumberColumn("Winner Diversity (%)", format="%.1f"),
                "Podium_Diversity": st.column_config.NumberColumn("Podium Diversity (%)", format="%.1f"),
                "Points_Std": st.column_config.NumberColumn("Points Variability", format="%.2f")
            }
        )
        
        # Competitiveness visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Winner diversity
            fig_diversity = px.bar(
                comp_df.sort_values('Winner_Diversity', ascending=False).head(10),
                x='Circuit',
                y='Winner_Diversity',
                title="Most Competitive Circuits (Winner Diversity %)",
                labels={'Winner_Diversity': 'Winner Diversity (%)', 'Circuit': 'Circuit'}
            )
            fig_diversity.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_diversity, use_container_width=True)
        
        with col2:
            # Points variability
            fig_variability = px.scatter(
                comp_df,
                x='Total_Races',
                y='Points_Std',
                size='Different_Winners',
                hover_name='Circuit',
                title="Circuit Predictability vs Sample Size",
                labels={'Points_Std': 'Points Variability', 'Total_Races': 'Total Races'}
            )
            st.plotly_chart(fig_variability, use_container_width=True)
        
        # Insights
        st.subheader("💡 Circuit Analysis Insights")
        
        if not comp_df.empty:
            most_competitive = comp_df.loc[comp_df['Winner_Diversity'].idxmax()]
            least_competitive = comp_df.loc[comp_df['Winner_Diversity'].idxmin()]
            most_unpredictable = comp_df.loc[comp_df['Points_Std'].idxmax()]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Most Competitive**: {most_competitive['Circuit'].replace('_', ' ').title()}\n({most_competitive['Winner_Diversity']:.1f}% winner diversity)")
            
            with col2:
                st.info(f"**Most Dominant**: {least_competitive['Circuit'].replace('_', ' ').title()}\n({least_competitive['Winner_Diversity']:.1f}% winner diversity)")
            
            with col3:
                st.info(f"**Most Unpredictable**: {most_unpredictable['Circuit'].replace('_', ' ').title()}\n(Points std: {most_unpredictable['Points_Std']:.2f})")

# Export circuit analysis
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export Circuit Analysis"):
    if not circuit_stats.empty:
        csv = circuit_stats.to_csv(index=False)
        
        st.sidebar.download_button(
            label="Download Circuit Statistics CSV",
            data=csv,
            file_name=f"circuit_analysis_{'-'.join(map(str, selected_seasons))}.csv",
            mime="text/csv"
        )

# Additional insights in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏁 Circuit Quick Facts")

if not filtered_results.empty:
    # Most successful circuit (by total points)
    most_points_circuit = filtered_results.groupby('circuit_id')['points'].sum().idxmax()
    st.sidebar.info(f"**Highest Points**: {most_points_circuit.replace('_', ' ').title()}")
    
    # Most races held
    most_races_circuit = filtered_results['circuit_id'].value_counts().index[0]
    race_count = filtered_results['circuit_id'].value_counts().iloc[0]
    st.sidebar.info(f"**Most Races**: {most_races_circuit.replace('_', ' ').title()} ({race_count} races)")
    
    # Average points across all circuits
    avg_points_all = filtered_results['points'].mean()
    st.sidebar.info(f"**Average Points**: {avg_points_all:.2f}")
