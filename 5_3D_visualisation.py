import xarray as xr 
import numpy as np 
import pyvista as pv

from matplotlib.colors import ListedColormap, BoundaryNorm

# These definitions follow the bounding boxes in Teoh et al.'s paper (except for Eurocontrol)
regions = {
    "Global": {"lon_min": -180, "lon_max": 180, "lat_min": -90, "lat_max": 90},
    "USA": {"lon_min": -126, "lon_max": -66, "lat_min": 23, "lat_max": 50},
    "Europe": {"lon_min": -5, "lon_max": 5, "lat_min": -5, "lat_max": 5},
    "Eurocontrol": {"lon_min": -30.0, "lon_max": 45.0, "lat_min": 25.0, "lat_max": 72.0},
    "Eurocontrol + North Atlantic": {"lon_min": -70.0, "lon_max": 45.0, "lat_min": 25.0, "lat_max": 72.0},
    "East_Asia": {"lon_min": 103, "lon_max": 150, "lat_min": 15, "lat_max": 48},
    "Southeast_Asia": {"lon_min": 87.5, "lon_max": 130, "lat_min": -10, "lat_max": 20},
    "Latin_America": {"lon_min": -85, "lon_max": -35, "lat_min": -60, "lat_max": 15},
    "Africa_Middle_East": {"lon_min": -20, "lon_max": 50, "lat_min": -35, "lat_max": 40},
    "China": {"lon_min": 73.5, "lon_max": 135, "lat_min": 18, "lat_max": 53.5},
    "India": {"lon_min": 68, "lon_max": 97.5, "lat_min": 8, "lat_max": 35.5},
    "North Atlantic": {"lon_min": -70, "lon_max": -5, "lat_min": 40, "lat_max": 63},
    "North Pacific": {"lon_min": 140, "lon_max": -120, "lat_min": 35, "lat_max": 65},
    "Arctic": {"lon_min": -180, "lon_max": 180, "lat_min": 66.5, "lat_max": 90}, 
}

def subset_region(ds, region):
    """Return subset of dataset within the region bounding box."""
    lon_min, lon_max = region["lon_min"], region["lon_max"]
    lat_min, lat_max = region["lat_min"], region["lat_max"]

    # Handle longitude wrap-around (e.g. North Pacific)
    if lon_min < lon_max:
        subset = ds.sel(longitude=slice(lon_min, lon_max), latitude=slice(lat_min, lat_max))
    else:
        # For regions crossing the dateline (e.g. 140E–120W)
        subset1 = ds.sel(longitude=slice(lon_min, 180))
        subset2 = ds.sel(longitude=slice(-180, lon_max))
        subset = xr.concat([subset1, subset2], dim="longitude")
        subset = subset.sel(latitude=slice(lat_min, lat_max))
    
    return subset

# Load two snapshots 3 hours apart
ds0 = subset_region(xr.open_dataset(r"data\issr\20240101T00.nc"), regions["Global"])


# --- Constants ---
R_EARTH = 6371e1  # meters
FEET_TO_M = 0.3048 * 100  # flight level (hundreds of feet) → meters

# --- Dataset ---
data = ds0["ef_per_m"].values  # shape (lon, lat, flight_level)
lons = np.deg2rad(ds0.longitude.values)  # radians
lats = np.deg2rad(ds0.latitude.values)
levels = ds0.flight_level.values * FEET_TO_M  # altitude above surface in meters

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

# Apply mask for ef_per_m > 5e8
mask = np.where(data > 0, data, np.nan)
grid["ef_per_m"] = mask.flatten(order="F")

# --- Visualization ---
thresh = grid.threshold(value=5e8)

plotter = pv.Plotter()

plotter.add_mesh(
    thresh,
    #scalars="ef_per_m",
    color="#c2447a",
    lighting=False,
    opacity=0.6,
    specular=0.4,
    show_edges=False,
)
plotter.add_text("Big hit regions on 01/01/2024 at midnight", font_size=14)

from pyvista import examples

# --- Earth globe with texture ---
earth = examples.planets.load_earth(radius=R_EARTH, lat_resolution=90, lon_resolution=180)

# Load the realistic Earth texture
earth_texture = examples.load_globe_texture()

plotter.add_mesh(earth, texture=earth_texture, smooth_shading=True)

#plotter.add_mesh(earth, color="lightgray", opacity=0.2)
# Optional: add axes + bounds
plotter.show_axes()
plotter.show_bounds(
    xlabel="X (m)",
    ylabel="Y (m)",
    zlabel="Z (m)",
    color='black',
    font_size=10,
)

#plotter.export_html("issr_visualization.html")
plotter.show()