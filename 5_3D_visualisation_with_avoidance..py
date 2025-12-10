import xarray as xr 
import numpy as np 
import pyvista as pv
from pyvista import examples
from matplotlib.colors import ListedColormap, BoundaryNorm

# Load dataset
ds0 = xr.open_dataset(r"data\issr\20240101T00.nc")
    
ef = ds0["ef_per_m"] # Your original DataArray

# --- Constants ---
R_EARTH = 6371e1  # meters
FEET_TO_M = 0.3048 * 100  # flight level (hundreds of feet) → meters

# Primary Flight Constants
CRUISE_ALTITUDE_FL_1 = 350 # Flight Level 350 (35,000 feet)
CRUISE_ALTITUDE_M_1 = CRUISE_ALTITUDE_FL_1 * FEET_TO_M # meters
CLIMB_FRAC_1 = 0.15 # Primary profile climb fraction

# Secondary Flight Constants
CRUISE_ALTITUDE_FL_2 = 270 # Flight Level 270 (27,000 feet)
CRUISE_ALTITUDE_M_2 = CRUISE_ALTITUDE_FL_2 * FEET_TO_M # meters
# Phase Fractions for Step-Climb Profile 2
INITIAL_CLIMB_END_FRAC = 0.15  # End initial climb at 15% (to FL 270)
STEP_CLIMB_START_FRAC = 0.50  # Start step climb at 50%
STEP_CLIMB_END_FRAC = 0.65    # End step climb at 65% (to FL 350)
DESCENT_START_FRAC = 0.85     # Start final descent at 85%
TOTAL_PATH_POINTS = 300 # Total number of segments for the final path

# --- Dataset ---
data = ds0["ef_per_m"].values  # shape (lon, lat, flight_level)
lons = np.deg2rad(ef.longitude.values)
lats = np.deg2rad(ef.latitude.values)
levels = ef.flight_level.values * FEET_TO_M
data = ef.values

# Build 3D mesh
lon3d, lat3d, lev3d = np.meshgrid(lons, lats, levels, indexing="ij")

# Compute radius from Earth's center
r = R_EARTH + lev3d

# --- Cartesian transformation ---
x = r * np.cos(lat3d) * np.cos(lon3d)
y = r * np.cos(lat3d) * np.sin(lon3d)
z = r * np.sin(lat3d)

# --- Build grid ---
grid = pv.StructuredGrid(x, y, z)


grid["ef_per_m"] = data.flatten(order="F")

# --- Create 3 Distinct Regions via Thresholding ---

# 1. Negative Forcing (< 0)
mesh_neg = grid.threshold(value=[-1e15, -1e3])

# 2. Positive Forcing Low (0 <= x <= 5e8)
mesh_pos_low = grid.threshold(value=[1e3, 5e8])

# 3. Positive Forcing High (> 5e8)
mesh_pos_high = grid.threshold(value=5e8)

# --- Visualization ---
plotter = pv.Plotter()

# Region 1: Negative (Blueish)
#plotter.add_mesh(
#    mesh_neg,
#    color="#75a1f4",
#    opacity=0.6,
#    show_edges=False,
#    label="Cooling"
#)
#
## Region 2: Positive Low (Orangeish)
#plotter.add_mesh(
#    mesh_pos_low,
#    color="#ff8754",
#    opacity=0.6,
#    show_edges=False,
#    label="Warming"
#)

# Region 3: Positive High (Pink/Red)
plotter.add_mesh(
    mesh_pos_high,
    color="#c2447a",
    opacity=0.6,
    show_edges=False,
    label="Very warming airspace"
)



# --- Earth globe with texture ---
earth = examples.planets.load_earth(radius=R_EARTH, lat_resolution=90, lon_resolution=180)
# Rotate texture by 180 degrees to align it with the coordinate system
earth.rotate_z(180, inplace=True)
# Load the realistic Earth texture
earth_texture = examples.load_globe_texture()

plotter.add_mesh(earth, texture=earth_texture, smooth_shading=True)


# --- Helper Functions ---

def to_cartesian(lat_deg, lon_deg, altitude_m=0):
    """Converts lat/lon to 3D cartesian using your constants."""
    r = R_EARTH + altitude_m 
    lat_rad = np.deg2rad(lat_deg)
    lon_rad = np.deg2rad(lon_deg)
    x = r * np.cos(lat_rad) * np.cos(lon_rad)
    y = r * np.cos(lat_rad) * np.sin(lon_rad)
    z = r * np.sin(lat_rad)
    return np.array([x, y, z])

def calculate_great_circle_points(p1_lat, p1_lon, p2_lat, p2_lon, num_segments):
    """Calculates points along a Great Circle path between two lat/lon pairs."""
    
    # Convert degrees to radians
    lat1, lon1 = np.deg2rad(p1_lat), np.deg2rad(p1_lon)
    lat2, lon2 = np.deg2rad(p2_lat), np.deg2rad(p2_lon)
    
    # Angular distance (central angle)
    d = np.arccos(np.sin(lat1) * np.sin(lat2) + np.cos(lat1) * np.cos(lat2) * np.cos(lon2 - lon1))
    
    # If points are the same or antipodal, skip calculation
    if np.isclose(d, 0) or np.isclose(d, np.pi):
        return np.array([[p1_lat, p1_lon]])
    
    intermediate_points = []
    
    for i in range(num_segments + 1):
        f = i / num_segments # fractional distance along the path (0 to 1)
        
        # Spherical interpolation formula (slerp)
        A = np.sin((1 - f) * d) / np.sin(d)
        B = np.sin(f * d) / np.sin(d)
        
        x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
        y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
        z = A * np.sin(lat1) + B * np.sin(lat2)
        
        # Convert back to lat/lon
        lat_f = np.arctan2(z, np.sqrt(x**2 + y**2))
        lon_f = np.arctan2(y, x)
        
        intermediate_points.append([np.rad2deg(lat_f), np.rad2deg(lon_f)])
        
    return np.array(intermediate_points)


def calculate_altitude_profile_1(N):
    """Profile 1: Standard Climb (15%), Cruise (70%), Descent (15%) at FL 350."""
    altitudes = np.zeros(N)
    CLIMB_END = int(N * CLIMB_FRAC_1)
    CRUISE_END = int(N * (CLIMB_FRAC_1 + (1 - 2*CLIMB_FRAC_1))) # Approx 70% cruise

    altitudes[:CLIMB_END] = np.linspace(0, CRUISE_ALTITUDE_M_1, CLIMB_END)
    altitudes[CLIMB_END:CRUISE_END] = CRUISE_ALTITUDE_M_1
    altitudes[CRUISE_END:] = np.linspace(CRUISE_ALTITUDE_M_1, 0, N - CRUISE_END)
    
    altitudes[0], altitudes[-1] = 0, 0
    return altitudes, CRUISE_END

def calculate_altitude_profile_2(N):
    """
    Profile 2: Step Climb (Climb to FL 270, Cruise, Climb to FL 350, Cruise, Descent).
    """
    altitudes = np.zeros(N)
    
    # Define phase points based on fractions
    C1_END = int(N * INITIAL_CLIMB_END_FRAC)   # 15% (End of Initial Climb to FL 270)
    C2_START = int(N * STEP_CLIMB_START_FRAC)  # 50% (Start of Step Climb to FL 350)
    C2_END = int(N * STEP_CLIMB_END_FRAC)      # 65% (End of Step Climb to FL 350)
    D_START = int(N * DESCENT_START_FRAC)      # 85% (Start of final Descent)
    
    # 1. Initial Climb (0% to 15%): 0m to FL 270
    altitudes[:C1_END] = np.linspace(0, CRUISE_ALTITUDE_M_2, C1_END)
    
    # 2. Low Cruise (15% to 50%): Constant at FL 270
    altitudes[C1_END:C2_START] = CRUISE_ALTITUDE_M_2

    # 3. Step Climb (50% to 65%): FL 270 to FL 350
    altitudes[C2_START:C2_END] = np.linspace(CRUISE_ALTITUDE_M_2, CRUISE_ALTITUDE_M_1, C2_END - C2_START)

    # 4. High Cruise (65% to 85%): Constant at FL 350
    altitudes[C2_END:D_START] = CRUISE_ALTITUDE_M_1

    # 5. Descent (85% to 100%): FL 350 to 0m
    altitudes[D_START:] = np.linspace(CRUISE_ALTITUDE_M_1, 0, N - D_START)
    
    altitudes[0], altitudes[-1] = 0, 0
    
    # Return index where the plane is in the high cruise phase (e.g., 75% point)
    static_index = int(N * 0.75)
    return altitudes, static_index

# Define known locations (Lat, Lon)
landmarks = {
    #"London (UK)": (51.5074, -0.1278),
    "Madrid (Spain)": (40.4167, 3.7033),
    "New York (USA)": (40.7128, -74.0060),
    #"Tokyo (Japan)": (35.6762, 139.6503),
    #"Sydney (Aus)": (-33.8688, 151.2093)
}

# --- 2. Define Geodesic Flight Path & Altitude Profile ---

# Define the start and end points (Lat, Lon)
NY_LAT, NY_LON = 40.7128, -74.0060
LON_LAT, LON_LON = 40.4167, 3.7033
N = TOTAL_PATH_POINTS + 1

# Calculate common geodesic path (lat/lon)
gc_lat_lon = calculate_great_circle_points(LON_LAT, LON_LON, NY_LAT, NY_LON, TOTAL_PATH_POINTS)

# --- Path 1: Standard Profile (FL 350) ---
altitudes_1, static_index_1 = calculate_altitude_profile_1(N)
path_points_3d_1 = np.vstack([
    to_cartesian(gc_lat_lon[i, 0], gc_lat_lon[i, 1], altitude_m=altitudes_1[i]) 
    for i in range(N)
])
great_circle_path_1 = pv.Spline(path_points_3d_1, n_points=N)


# --- Path 2: Alternative Profile (Delayed Climb, FL 270) ---
altitudes_2, static_index_2 = calculate_altitude_profile_2(N)
path_points_3d_2 = np.vstack([
    to_cartesian(gc_lat_lon[i, 0], gc_lat_lon[i, 1], altitude_m=altitudes_2[i]) 
    for i in range(N)
])
great_circle_path_2 = pv.Spline(path_points_3d_2, n_points=N)

# Add the Great Circle Flight Path (New Addition)
plotter.add_mesh(
    great_circle_path_1, 
    color='black', 
    line_width=5, 
    label='Original flight path'
)

# --- Path 2: Alternative Profile (Dotted Red) ---
plotter.add_mesh(
    great_circle_path_2, 
    color='green', 
    line_width=3, 
    label=f'Better flight path'
)

# Add Legend/Text
plotter.add_legend()
plotter.add_text("Regions where flights lead to high contrail warming on 1 January 2024 at 00:00", font_size=18, shadow=True)

# Create points and labels
points = []
labels = []

for name, (lat, lon) in landmarks.items():
    loc = to_cartesian(lat, lon, altitude_m=0) 
    points.append(loc)
    labels.append(name)

# Convert to PyVista format
point_cloud = pv.PolyData(points)

# Add red markers for the cities
plotter.add_mesh(
    point_cloud, 
    color="red", 
    point_size=15, 
    render_points_as_spheres=True,
    label="Calibration Points"
)

# Add text labels floating near the points
plotter.add_point_labels(
    point_cloud, 
    labels, 
    font_size=16, 
    point_color="red", 
    text_color="white",
    always_visible=True
)



# --- Controls Guide (Bottom Left) ---
controls_text = (
    "CONTROLS:\n"
    "Left Click   : Rotate\n"
    "Right Click  : Zoom\n"
    "Shift+Click  : Pan\n"
    "Ctrl+Click   : Spin\n"
    "Key 'r'      : Reset Camera"
)

plotter.add_text(
    controls_text,
    position="lower_left",
    font_size=10,        
    color="#555555",     
    font="courier",      # Monospace keeps the colons aligned
    shadow=False,
)



plotter.export_html("output\issr\issr_visualization.html")
plotter.show()