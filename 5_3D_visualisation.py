import xarray as xr 
import numpy as np 
import pyvista as pv
from pyvista import examples

# Load dataset
ds0 = xr.open_dataset(r"data\issr\20240101T00.nc")
    
ef = ds0["ef_per_m"] # Your original DataArray

ef = ef.coarsen(
    longitude=2, latitude=2, flight_level=2, boundary="trim"
).mean()

# Quick hack since the coordinates don't align
# Alternatives:
# 1. Interpolate the grid at evenly spaced points (BEST)
# 2. Shift grid by 0.125 deg and pretend everything is correct (incorrect, but probably fine)

slice_to_append = ef.isel(longitude=0)
slice_to_append['longitude'] = 180.125

ef = xr.concat([ef, slice_to_append], dim='longitude')

# --- Constants ---
R_EARTH = 6371e1  # meters
FEET_TO_M = 0.3048 * 100  # flight level (hundreds of feet) → meters

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
plotter.add_mesh(
    mesh_neg,
    color="#75a1f4",
    opacity=0.6,
    show_edges=False,
    label="Cooling"
)

# Region 2: Positive Low (Orangeish)
plotter.add_mesh(
    mesh_pos_low,
    color="#ff8754",
    opacity=0.6,
    show_edges=False,
    label="Warming"
)

# Region 3: Positive High (Pink/Red)
plotter.add_mesh(
    mesh_pos_high,
    color="#c2447a",
    opacity=0.6,
    show_edges=False,
    label="Very warming"
)



# --- Earth globe with texture ---
earth = examples.planets.load_earth(radius=R_EARTH, lat_resolution=90, lon_resolution=180)
# Rotate texture by 180 degrees to align it with the coordinate system
earth.rotate_z(180, inplace=True)
# Load the realistic Earth texture
earth_texture = examples.load_globe_texture()

plotter.add_mesh(earth, texture=earth_texture, smooth_shading=True)

plotter.enable_terrain_style(mouse_wheel_zooms=False)

plotter.export_html("html/pcr_visualization_without_UI.html")
plotter.show()