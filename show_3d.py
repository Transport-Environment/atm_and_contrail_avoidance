# pip install pyvista pyvistaqt
import math
import numpy as np
import pyvista as pv
from pyvista import examples

# -----------------------------
# Helpers: local ENU frame
# -----------------------------
def enu_axes(lat_deg: float, lon_deg: float):
    """Return unit vectors (E, N, U) in ECEF coordinates at (lat, lon)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    # Up
    U = np.array([math.cos(lat)*math.cos(lon),
                  math.cos(lat)*math.sin(lon),
                  math.sin(lat)])
    # East
    E = np.array([-math.sin(lon), math.cos(lon), 0.0])
    # North
    N = np.array([-math.sin(lat)*math.cos(lon),
                  -math.sin(lat)*math.sin(lon),
                  math.cos(lat)])
    # Normalize (just in case)
    def _n(v): 
        return v/np.linalg.norm(v)
    return _n(E), _n(N), _n(U)

def look_vectors(lat_deg: float, lon_deg: float):
    """Return camera position (unit-radius), west/look dir, and view-up."""
    E, N, U = enu_axes(lat_deg, lon_deg)
    west = -E  # looking due west
    pos = U    # position at unit radius along Up (we’ll scale later)
    return pos, west, U

def make_transform_from_axes(x_axis, y_axis, z_axis, origin):
    """Build 4x4 transform whose columns are the axes and origin."""
    T = np.eye(4)
    T[0:3, 0] = x_axis
    T[0:3, 1] = y_axis
    T[0:3, 2] = z_axis
    T[0:3, 3] = origin
    return T

# -----------------------------
# Load Earth + assets
# -----------------------------
earth = examples.planets.load_earth()
texture = examples.load_globe_texture()

# Try starry background; fall back to solid color if unavailable
star_bg_path = None
try:
    star_bg_path = examples.planets.download_stars_sky_background(load=False)
except Exception:
    star_bg_path = None

# -----------------------------
# Scene parameters
# -----------------------------
# Brussels
LAT, LON = 50.8503, 4.3517

# Derive Earth "radius" from mesh bounds (works with examples sphere)
xmin, xmax, ymin, ymax, zmin, zmax = earth.bounds
R_est = max(xmax - xmin, ymax - ymin, zmax - zmin) * 0.5

# Camera altitude above the surface (fraction of Earth radius)
altitude_frac = 0.01 # ~4% of R; tweak to taste
cam_R = R_est * (1.0 + altitude_frac)

# Compute camera vectors on the unit sphere, then scale to R
pos_unit, west_dir, up_unit = look_vectors(LAT, LON)
cam_pos = cam_R * pos_unit
cam_fp  = cam_pos + (R_est * 0.5) * west_dir  # look “straight west” ahead
cam_up  = up_unit

# -----------------------------
# Build plotter & add Earth
# -----------------------------
plotter = pv.Plotter()
if star_bg_path:
    try:
        plotter.add_background_image(star_bg_path)
    except Exception:
        plotter.set_background("white")
else:
    plotter.set_background("white")

plotter.add_mesh(earth, texture=texture, smooth_shading=True)

# -----------------------------
# Airplane in front of camera
# -----------------------------
plane = examples.load_airplane().copy()

# The airplane in examples faces +X by default.
# We’ll align:
#   x_axis -> west (look direction)
#   y_axis -> north (for a sane “wing” orientation)
#   z_axis -> up
E, N, U = enu_axes(LAT, LON)
west = -E
x_axis = west / np.linalg.norm(west)
y_axis = N / np.linalg.norm(N)
z_axis = U / np.linalg.norm(U)

# Place the plane some distance in front of the camera, along look direction
plane_distance = R_est * 0.08  # tweak to place closer/farther
plane_origin = cam_pos + plane_distance * x_axis

# Create world transform for the airplane
T = make_transform_from_axes(x_axis, y_axis, z_axis, plane_origin)
plane.transform(T, inplace=True)

# Scale airplane to something visible near the camera
# (The airplane model is unit-ish; scale relative to Earth radius.)
plane_scale = R_est * 0.01
plane.points *= plane_scale

plotter.add_mesh(plane, color="white", smooth_shading=True, specular=0.3, name="airplane")

# -----------------------------
# Camera setup
# -----------------------------
plotter.camera.position = cam_pos.tolist()
plotter.camera.focal_point = cam_fp.tolist()
plotter.camera.up = cam_up.tolist()

# Optional niceties
#plotter.enable_eye_dome_lighting()  # improves depth perception
#plotter.show_bounds(grid='back', location='outer', ticks='both', font_size=10)
plotter.add_text("Brussels observer • looking west", font_size=12)

# Render
plotter.show()
