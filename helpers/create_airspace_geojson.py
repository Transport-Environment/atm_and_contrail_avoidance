import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import regionmask
import json, topojson
import glob, re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import datetime

# Filter to European FIRs
european_fir = pd.read_csv("data/european_firs.csv")

# Rectangular regions
regions = { 
    "European Airspace": {"lon_min": -30.0, "lon_max": 45.0, "lat_min": 25.0, "lat_max": 72.0},
    "North Atlantic": {"lon_min": -70, "lon_max": -5, "lat_min": 40, "lat_max": 63},
    "Continental Europe": {"lon_min": -12, "lon_max": 20, "lat_min": 35, "lat_max": 60},
    "Global": {"lon_min": -180, "lon_max": 180, "lat_min": -90, "lat_max": 90},
    "USA": {"lon_min": -126, "lon_max": -66, "lat_min": 23, "lat_max": 50},
    "East Asia": {"lon_min": 103, "lon_max": 150, "lat_min": 15, "lat_max": 48},
    "Southeast Asia": {"lon_min": 87.5, "lon_max": 130, "lat_min": -10, "lat_max": 20},
    "Latin America": {"lon_min": -85, "lon_max": -35, "lat_min": -60, "lat_max": 15},
    "Africa & Middle East": {"lon_min": -20, "lon_max": 50, "lat_min": -35, "lat_max": 40},
    "China": {"lon_min": 73.5, "lon_max": 135, "lat_min": 18, "lat_max": 53.5},
    "India": {"lon_min": 68, "lon_max": 97.5, "lat_min": 8, "lat_max": 35.5},
    "North Pacific": {"lon_min": 140, "lon_max": -120, "lat_min": 35, "lat_max": 65},
    "Arctic": {"lon_min": -180, "lon_max": 180, "lat_min": 66.5, "lat_max": 90},
}

# Load FIRs TopoJSON
with open("data/worldfirs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

topo = topojson.Topology(data, object_name="data")
gdf_fir = topo.to_gdf().set_crs(epsg=4326)
gdf_fir = gdf_fir[gdf_fir["type"].str.upper() == "FIR"]

# Filter to European FIRs
gdf_fir["Eurocontrol FIR"] = gdf_fir["designator"].isin(european_fir["FIR code"])

# Build rectangular regions GeoDataFrame
rects = []
for name, region in regions.items():
    geom = box(region["lon_min"], region["lat_min"], region["lon_max"], region["lat_max"])
    rects.append({"name": name, "geometry": geom})

gdf_rects = gpd.GeoDataFrame(rects, crs="EPSG:4326")

# ✅ Combine FIRs and rectangular regions
# Ensure both have the same column structure (optional)
gdf_rects["designator"] = None
gdf_rects["Eurocontrol FIR"] = None
gdf_rects["type"] = "RECT"

# Merge (concatenate)
gdf_combined = pd.concat([gdf_rects, gdf_fir], ignore_index=True)
gdf_combined.to_file("data/airspaces.geojson", driver="GeoJSON")
