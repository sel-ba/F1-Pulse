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

from utils.data_loader import load_all_data, get_circuit_list, get_driver_list
from utils.statistics import calculate_circuit_stats

st.set_page_config(
    page_title="3D Circuit Visualization - F1 Analytics",
    page_icon="🏎️",
    layout="wide"
)

st.title("🏎️ Interactive 3D Circuit Visualizations")
st.markdown("### Immersive track layouts and performance analysis in 3D")

# Load data
@st.cache_data
def get_data():
    return load_all_data()

try:
    data = get_data()
    races = data['races']
    results = data['results']
    qualifying = data['qualifying']
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Sidebar filters
st.sidebar.header("🔧 3D Visualization Controls")

# Circuit selection
available_circuits = get_circuit_list(data)
selected_circuit = st.sidebar.selectbox(
    "Select Circuit for 3D Visualization",
    available_circuits,
    index=0 if available_circuits else None
)

# Season filter
available_seasons = sorted(results['season'].unique())
selected_season = st.sidebar.selectbox(
    "Select Season",
    available_seasons,
    index=len(available_seasons)-1 if available_seasons else 0
)

# Visualization type
viz_type = st.sidebar.selectbox(
    "Visualization Type",
    ["Track Layout 3D", "Performance Elevation", "Grid Position Flow", "Lap Time Surface"]
)

if not selected_circuit:
    st.warning("Please select a circuit to visualize.")
    st.stop()

# Get circuit data
circuit_races = races[races['circuit_id'] == selected_circuit]
circuit_results = results[
    (results['circuit_id'] == selected_circuit) & 
    (results['season'] == selected_season)
]

if circuit_races.empty:
    st.error(f"No race data found for {selected_circuit}")
    st.stop()

# Get circuit coordinates
circuit_info = circuit_races.iloc[0]
circuit_lat = circuit_info.get('lat', 0)
circuit_long = circuit_info.get('long', 0)
circuit_country = circuit_info.get('country', 'Unknown')

def create_3d_track_layout(circuit_name, lat, long):
    """Create a 3D representation of a circuit track layout"""
    
    # Generate synthetic track layout based on real coordinates
    # This creates a representative track shape for visualization
    angles = np.linspace(0, 2*np.pi, 100)
    
    # Create a more complex track shape based on circuit characteristics
    if 'monaco' in circuit_name.lower():
        # Monaco - tight street circuit
        radius_variation = 0.3 + 0.2 * np.sin(4 * angles)
        elevation_variation = np.sin(2 * angles) * 50
    elif 'monza' in circuit_name.lower():
        # Monza - high-speed circuit with long straights
        radius_variation = 0.8 + 0.4 * np.sin(2 * angles)
        elevation_variation = np.sin(angles) * 20
    elif 'silverstone' in circuit_name.lower():
        # Silverstone - flowing circuit
        radius_variation = 0.6 + 0.3 * np.sin(3 * angles)
        elevation_variation = np.sin(1.5 * angles) * 30
    else:
        # Generic circuit
        radius_variation = 0.5 + 0.3 * np.sin(3 * angles)
        elevation_variation = np.sin(2 * angles) * 25
    
    # Generate track coordinates
    x = radius_variation * np.cos(angles)
    y = radius_variation * np.sin(angles)
    z = elevation_variation
    
    # Add track markers
    sectors = ['Sector 1', 'Sector 2', 'Sector 3', 'Start/Finish']
    sector_indices = [0, 25, 50, 75]
    
    fig = go.Figure()
    
    # Main track line
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='lines',
        line=dict(color='red', width=8),
        name='Track Layout',
        hovertemplate="<b>Track Position</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Elevation: %{z:.1f}m<extra></extra>"
    ))
    
    # Add sector markers
    for i, (idx, sector) in enumerate(zip(sector_indices, sectors)):
        fig.add_trace(go.Scatter3d(
            x=[x[idx]], y=[y[idx]], z=[z[idx]],
            mode='markers+text',
            marker=dict(size=12, color=['green', 'yellow', 'orange', 'red'][i]),
            text=[sector],
            textposition="top center",
            name=sector,
            hovertemplate=f"<b>{sector}</b><br>Position: %{{x:.2f}}, %{{y:.2f}}<br>Elevation: %{{z:.1f}}m<extra></extra>"
        ))
    
    # Add racing line indicators
    racing_line_x = x * 0.95  # Inside line
    racing_line_y = y * 0.95
    racing_line_z = z + 2  # Slightly elevated
    
    fig.add_trace(go.Scatter3d(
        x=racing_line_x, y=racing_line_y, z=racing_line_z,
        mode='lines',
        line=dict(color='blue', width=4, dash='dash'),
        name='Ideal Racing Line',
        hovertemplate="<b>Racing Line</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Elevation: %{z:.1f}m<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"3D Track Layout - {circuit_name.replace('_', ' ').title()}",
        scene=dict(
            xaxis_title="Track Width (km)",
            yaxis_title="Track Length (km)",
            zaxis_title="Elevation (m)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            aspectmode='cube'
        ),
        height=600
    )
    
    return fig

def create_performance_elevation_3d(circuit_results):
    """Create 3D elevation map of driver performance"""
    
    if circuit_results.empty:
        return go.Figure().add_annotation(
            text="No performance data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    # Create grid positions
    grid_positions = circuit_results['grid'].values
    points = circuit_results['points'].values
    drivers = circuit_results['driver'].values
    
    # Create 3D surface based on grid vs points
    x_range = np.linspace(1, max(grid_positions) if len(grid_positions) > 0 else 20, 20)
    y_range = np.linspace(0, max(points) if len(points) > 0 else 25, 15)
    
    X, Y = np.meshgrid(x_range, y_range)
    Z = np.zeros_like(X)
    
    # Create elevation based on performance density
    for i, (grid_pos, point_score) in enumerate(zip(grid_positions, points)):
        if pd.notna(grid_pos) and pd.notna(point_score):
            # Find nearest grid points
            x_idx = np.argmin(np.abs(x_range - grid_pos))
            y_idx = np.argmin(np.abs(y_range - point_score))
            
            # Add elevation peak
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    xi, yi = x_idx + dx, y_idx + dy
                    if 0 <= xi < len(x_range) and 0 <= yi < len(y_range):
                        distance = np.sqrt(dx**2 + dy**2)
                        elevation = max(0, 10 - distance * 2)
                        Z[yi, xi] += elevation
    
    fig = go.Figure()
    
    # Add surface
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        colorscale='Viridis',
        name='Performance Density',
        hovertemplate="Grid: %{x:.0f}<br>Points: %{y:.0f}<br>Density: %{z:.1f}<extra></extra>"
    ))
    
    # Add individual driver points
    valid_mask = pd.notna(grid_positions) & pd.notna(points)
    if valid_mask.any():
        fig.add_trace(go.Scatter3d(
            x=grid_positions[valid_mask],
            y=points[valid_mask],
            z=np.ones(np.sum(valid_mask)) * (np.max(Z) + 5),
            mode='markers+text',
            marker=dict(
                size=8,
                color=points[valid_mask],
                colorscale='RdYlBu',
                showscale=True,
                colorbar=dict(title="Points Scored")
            ),
            text=drivers[valid_mask],
            textposition="top center",
            name='Driver Results',
            hovertemplate="<b>%{text}</b><br>Grid: %{x}<br>Points: %{y}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"3D Performance Landscape - {selected_circuit.replace('_', ' ').title()} {selected_season}",
        scene=dict(
            xaxis_title="Starting Grid Position",
            yaxis_title="Points Scored",
            zaxis_title="Performance Density",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        height=600
    )
    
    return fig

def create_grid_flow_3d(circuit_results):
    """Create 3D flow visualization of grid position changes"""
    
    if circuit_results.empty:
        return go.Figure().add_annotation(
            text="No grid data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=20)
        )
    
    fig = go.Figure()
    
    # Create flow lines from grid to finish
    for _, row in circuit_results.iterrows():
        if pd.notna(row['grid']) and pd.notna(row.get('podium', 0)):
            start_pos = row['grid']
            finish_pos = row.get('podium', row['grid'])  # Use podium position or grid as fallback
            points_scored = row['points']
            
            # Create flow line
            x_line = [0, 1]  # Start to finish
            y_line = [start_pos, finish_pos]
            z_line = [0, points_scored]
            
            color_intensity = points_scored / 25.0 if points_scored > 0 else 0.1
            
            fig.add_trace(go.Scatter3d(
                x=x_line, y=y_line, z=z_line,
                mode='lines+markers',
                line=dict(
                    color=f'rgba({int(255*color_intensity)}, {int(100*(1-color_intensity))}, {int(50*(1-color_intensity))}, 0.8)',
                    width=6
                ),
                marker=dict(size=[8, 12], color=['blue', 'red']),
                name=row['driver'],
                hovertemplate=f"<b>{row['driver']}</b><br>Grid: {start_pos}<br>Finish: {finish_pos}<br>Points: {points_scored}<extra></extra>"
            ))
    
    fig.update_layout(
        title=f"3D Grid Position Flow - {selected_circuit.replace('_', ' ').title()} {selected_season}",
        scene=dict(
            xaxis_title="Race Progress",
            yaxis_title="Position",
            zaxis_title="Points Earned",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            yaxis=dict(autorange='reversed')  # Lower position numbers are better
        ),
        height=600,
        showlegend=False
    )
    
    return fig

def create_laptime_surface_3d():
    """Create 3D surface representing theoretical lap time variations"""
    
    # Generate synthetic lap time data for visualization
    track_positions = np.linspace(0, 100, 50)  # Track completion percentage
    speed_zones = np.linspace(50, 350, 30)  # Speed in km/h
    
    X, Y = np.meshgrid(track_positions, speed_zones)
    
    # Create theoretical lap time surface
    # Higher speeds generally mean lower sector times
    base_time = 90  # Base lap time in seconds
    Z = base_time - (Y - 50) / 10 + np.sin(X / 10) * 5
    
    fig = go.Figure()
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        colorscale='RdYlBu_r',
        name='Lap Time Surface',
        hovertemplate="Track Position: %{x:.0f}%<br>Speed: %{y:.0f} km/h<br>Sector Time: %{z:.1f}s<extra></extra>"
    ))
    
    # Add optimal racing line
    optimal_positions = np.linspace(0, 100, 20)
    optimal_speeds = 200 + 50 * np.sin(optimal_positions / 15)  # Varying optimal speeds
    optimal_times = base_time - (optimal_speeds - 50) / 10 + np.sin(optimal_positions / 10) * 5
    
    fig.add_trace(go.Scatter3d(
        x=optimal_positions,
        y=optimal_speeds,
        z=optimal_times + 2,  # Slightly elevated
        mode='lines+markers',
        line=dict(color='yellow', width=8),
        marker=dict(size=6, color='gold'),
        name='Optimal Racing Line',
        hovertemplate="Position: %{x:.0f}%<br>Speed: %{y:.0f} km/h<br>Time: %{z:.1f}s<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"3D Lap Time Surface - {selected_circuit.replace('_', ' ').title()}",
        scene=dict(
            xaxis_title="Track Position (%)",
            yaxis_title="Speed (km/h)",
            zaxis_title="Sector Time (seconds)",
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
        ),
        height=600
    )
    
    return fig

# Main content area
st.header(f"🏁 {selected_circuit.replace('_', ' ').title()} - {selected_season}")

# Circuit information
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Country", circuit_country)
with col2:
    st.metric("Latitude", f"{circuit_lat:.4f}")
with col3:
    st.metric("Longitude", f"{circuit_long:.4f}")
with col4:
    races_at_circuit = len(circuit_results)
    st.metric("Drivers in Race", races_at_circuit)

# Create and display the selected visualization
if viz_type == "Track Layout 3D":
    st.subheader("🏎️ 3D Track Layout Visualization")
    st.info("💡 This 3D representation shows the track layout with elevation changes, sector markers, and the ideal racing line.")
    
    fig = create_3d_track_layout(selected_circuit, circuit_lat, circuit_long)
    st.plotly_chart(fig, use_container_width=True)
    
    # Track statistics
    st.subheader("📊 Track Characteristics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Track Features:**")
        st.write("• Elevation changes simulate real track characteristics")
        st.write("• Red line shows the main racing circuit")
        st.write("• Blue dashed line indicates the ideal racing line")
        st.write("• Colored markers show different track sectors")
        
    with col2:
        st.write("**Racing Analysis:**")
        st.write("• Monaco: Tight street circuit with elevation")
        st.write("• Monza: High-speed with long straights")
        st.write("• Silverstone: Flowing medium-speed circuit")
        st.write("• Other circuits: Generic characteristics")

elif viz_type == "Performance Elevation":
    st.subheader("📈 3D Performance Landscape")
    st.info("💡 This shows how grid position and points scored create a performance 'landscape' with peaks representing successful combinations.")
    
    fig = create_performance_elevation_3d(circuit_results)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance insights
    if not circuit_results.empty:
        st.subheader("🔍 Performance Insights")
        
        avg_points = circuit_results['points'].mean()
        best_performer = circuit_results.loc[circuit_results['points'].idxmax()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Average Points Scored", f"{avg_points:.2f}")
            st.metric("Best Performer", best_performer['driver'])
            
        with col2:
            st.metric("Points by Best", f"{best_performer['points']:.0f}")
            st.metric("Started from Grid", f"{best_performer['grid']:.0f}")

elif viz_type == "Grid Position Flow":
    st.subheader("🔄 3D Grid Position Flow")
    st.info("💡 This visualization shows how drivers moved from their starting grid position to their finishing position, with height representing points earned.")
    
    fig = create_grid_flow_3d(circuit_results)
    st.plotly_chart(fig, use_container_width=True)
    
    # Flow analysis
    if not circuit_results.empty:
        st.subheader("📈 Position Change Analysis")
        
        # Calculate biggest movers
        circuit_results_clean = circuit_results.dropna(subset=['grid'])
        if not circuit_results_clean.empty:
            circuit_results_clean['position_change'] = circuit_results_clean['grid'] - circuit_results_clean.get('podium', circuit_results_clean['grid'])
            
            biggest_gainer = circuit_results_clean.loc[circuit_results_clean['position_change'].idxmax()]
            biggest_loser = circuit_results_clean.loc[circuit_results_clean['position_change'].idxmin()]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Biggest Position Gain:**")
                st.write(f"🏆 {biggest_gainer['driver']}")
                st.write(f"📍 Moved {biggest_gainer['position_change']:.0f} positions forward")
                
            with col2:
                st.write("**Most Positions Lost:**")
                st.write(f"📉 {biggest_loser['driver']}")
                st.write(f"📍 Lost {abs(biggest_loser['position_change']):.0f} positions")

elif viz_type == "Lap Time Surface":
    st.subheader("⏱️ 3D Lap Time Surface Analysis")
    st.info("💡 This theoretical surface shows how track position and speed affect sector times, with the yellow line indicating the optimal racing approach.")
    
    fig = create_laptime_surface_3d()
    st.plotly_chart(fig, use_container_width=True)
    
    # Lap time insights
    st.subheader("🏁 Racing Strategy Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Speed Strategy:**")
        st.write("• Higher speeds generally reduce sector times")
        st.write("• Track position affects optimal speed zones")
        st.write("• Surface shows theoretical performance relationships")
        
    with col2:
        st.write("**Optimal Racing Line:**")
        st.write("• Yellow line shows theoretical optimal path")
        st.write("• Balances speed with track position")
        st.write("• Elevated slightly above the main surface")

# Interactive controls explanation
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎮 3D Controls")
st.sidebar.markdown("• **Rotate**: Click and drag")
st.sidebar.markdown("• **Zoom**: Mouse wheel or pinch")
st.sidebar.markdown("• **Pan**: Shift + click and drag")
st.sidebar.markdown("• **Reset**: Double-click")

# Additional features
st.sidebar.markdown("---")
st.sidebar.markdown("### ✨ Visualization Features")

show_data_table = st.sidebar.checkbox("Show Raw Data Table", False)
show_statistics = st.sidebar.checkbox("Show Statistical Analysis", True)

if show_data_table and not circuit_results.empty:
    st.subheader("📋 Race Data Table")
    display_columns = ['driver', 'constructor', 'grid', 'points', 'status']
    available_columns = [col for col in display_columns if col in circuit_results.columns]
    st.dataframe(circuit_results[available_columns], use_container_width=True)

if show_statistics:
    st.subheader("📊 Circuit Statistics Summary")
    
    if not circuit_results.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_points = circuit_results['points'].sum()
            st.metric("Total Points Awarded", f"{total_points:.0f}")
            
        with col2:
            avg_grid = circuit_results['grid'].mean()
            st.metric("Average Grid Position", f"{avg_grid:.1f}")
            
        with col3:
            point_scorers = len(circuit_results[circuit_results['points'] > 0])
            st.metric("Point Scoring Drivers", point_scorers)