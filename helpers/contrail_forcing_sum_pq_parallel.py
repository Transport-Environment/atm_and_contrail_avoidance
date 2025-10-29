import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import regionmask
import json, topojson
import glob, re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


# ---------------------------------------
# CONFIGURATION
# ---------------------------------------
COLS_SUM = [
    "total_flight_dist", 
    "contrail_ef_initial_loc",
    "contrail_ef_overlap_initial_loc", 
    "new_contrail_length", 
    "total_contrail_length", 
    "tau_contrail_area", 
    "mean_contrail_age", 
    "contrail_ef", 
    "contrail_ef_sw", 
    "contrail_ef_lw", 
    "contrail_ef_overlap", 
    "contrail_ef_sw_overlap", 
    "contrail_ef_lw_overlap"
]


def build_regionmask():
    """Builds a combined regionmask from FIRs and rectangular regions."""
    # Rectangular regions
    regions = { 
        "Global": {"lon_min": -180, "lon_max": 180, "lat_min": -90, "lat_max": 90},
        "USA": {"lon_min": -126, "lon_max": -66, "lat_min": 23, "lat_max": 50},
        "Europe": {"lon_min": -12, "lon_max": 20, "lat_min": 35, "lat_max": 60},
        "East_Asia": {"lon_min": 103, "lon_max": 150, "lat_min": 15, "lat_max": 48},
        "Southeast_Asia": {"lon_min": 87.5, "lon_max": 130, "lat_min": -10, "lat_max": 20},
        "Latin_America": {"lon_min": -85, "lon_max": -35, "lat_min": -60, "lat_max": 15},
        "Africa_Middle_East": {"lon_min": -20, "lon_max": 50, "lat_min": -35, "lat_max": 40},
        "China": {"lon_min": 73.5, "lon_max": 135, "lat_min": 18, "lat_max": 53.5},
        "India": {"lon_min": 68, "lon_max": 97.5, "lat_min": 8, "lat_max": 35.5},
        "North Atlantic": {"lon_min": -70, "lon_max": -5, "lat_min": 40, "lat_max": 63},
        "North Pacific": {"lon_min": 140, "lon_max": -120, "lat_min": 35, "lat_max": 65},
        "Arctic": {"lon_min": -180, "lon_max": 180, "lat_min": 66.5, "lat_max": 90},
        "Eurocontrol": {"lon_min": -30.0, "lon_max": 45.0, "lat_min": 25.0, "lat_max": 72.0}
    }

    # Load FIRs
    with open("worldfirs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    topo = topojson.Topology(data, object_name="data")
    gdf_fir = topo.to_gdf().set_crs(epsg=4326)
    gdf_fir = gdf_fir[gdf_fir["type"].str.upper() == "FIR"]

    # Filter to European FIRs
    european_fir = pd.read_csv("european_firs.csv")
    gdf_fir = gdf_fir[gdf_fir["designator"].isin(european_fir["FIR code"])]

    # Build rectangular GeoDataFrame
    rects = []
    for name, region in regions.items():
        geom = box(region["lon_min"], region["lat_min"], region["lon_max"], region["lat_max"])
        rects.append({"name": name, "geometry": geom})
    gdf_rects = gpd.GeoDataFrame(rects, crs="EPSG:4326")

    # Combine both
    combined_gdf = pd.concat([gdf_fir[["name", "geometry"]], gdf_rects], ignore_index=True)
    combined_mask = regionmask.Regions(
        outlines=combined_gdf.geometry.values,
        names=combined_gdf["name"].tolist(),
        abbrevs=combined_gdf["name"].tolist()
    )
    return combined_mask


def process_file(file, mask):
    """Processes a single parquet file for all FIR/regions."""
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point
    import re

    fname = Path(file).stem
    m = re.search(r"(\d{8})", fname)
    date = pd.Timestamp(m.group(1)) if m else pd.NaT

    df = pd.read_parquet(file).fillna(0)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs="EPSG:4326")

    results = []
    for region_id, region_name in enumerate(mask.names):
        geom = mask[region_id].polygon
        minx, miny, maxx, maxy = geom.bounds
        subset = gdf.cx[minx:maxx, miny:maxy]
        subset = subset[subset.geometry.within(geom)]
        if subset.empty:
            continue

        df_hourly = subset.groupby("hour")[COLS_SUM].sum(min_count=1).reset_index()
        df_hourly["timestamp"] = [date + pd.Timedelta(hours=int(h)) for h in df_hourly["hour"]]
        df_hourly["region"] = region_name
        df_hourly["file"] = Path(file).name
        results.append(df_hourly)

    return pd.concat(results, ignore_index=True) if results else None


def main():
    """Main entry point for multiprocessing FIR analysis."""
    folder_path = "./"
    pq_files = sorted(glob.glob(f"{folder_path}/*.pq"))
    n_workers = 4  # With 4 cores, this takes 3 hours to run for 365 days

    if not pq_files:
        print("❌ No parquet files found!")
        return

    print(f"Found {len(pq_files)} parquet files")
    mask = build_regionmask()

    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(process_file, f, mask): f for f in pq_files}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
            try:
                df_res = fut.result()
                if df_res is not None:
                    results.append(df_res)
            except Exception as e:
                print(f"⚠️ Error processing {futures[fut]}: {e}")

    if not results:
        print("❌ No data processed!")
        return

    df_all = pd.concat(results, ignore_index=True)
    output_path = Path("hourly_totals_by_region.pq")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_parquet(output_path, index=False)
    print(f"✅ Multiprocessing complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()
