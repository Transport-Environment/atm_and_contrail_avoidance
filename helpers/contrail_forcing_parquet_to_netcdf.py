"""
Convert contrail parquet data to hourly NetCDF (4D: lon-lat-alt-time).
"""

import warnings
import numpy as np
import pandas as pd
import xarray as xr
import sys
from tqdm import tqdm
from pycontrails.physics.geo import grid_surface_area
import os 

# ----------- USER INPUTS ----------- #

FOLDER_PATH = "./"        # Folder with daily parquet files
OUTPUT_PATH = "cdf/"      # Folder to save hourly netcdf files

# CLI arguments: start and end date (inclusive)
if len(sys.argv) >= 3:
    DATE_START = sys.argv[1]
    DATE_END = sys.argv[2]
else:
    print("Usage: python script.py YYYY-MM-DD YYYY-MM-DD")
    sys.exit(1)

TEMPORAL_RES_H = 1  # 1-hour resolution

# Altitude dimension (m)
ALTITUDE_BOUNDS_M = (6000.0, 15000.0)
ALTITUDE_RES_M = 304.8

# Longitude-latitude dimension (degrees)
SPATIAL_BBOX = (-180.0, -90.0, 180.0, 90.0)
SPATIAL_GRID_RES = 0.25

# ----------- FUNCTIONS ----------- #

def _agg_to_grid(df_res, agg_map, lon_coords, lat_coords, alt_coords):
    shape = lon_coords.size, lat_coords.size, alt_coords.size

    idx_lon = np.searchsorted(lon_coords, df_res["longitude"])
    idx_lat = np.searchsorted(lat_coords, df_res["latitude"])
    idx_alt = np.searchsorted(alt_coords, df_res["altitude"])

    df_agg = df_res.groupby([idx_lon, idx_lat, idx_alt]).agg(agg_map)
    i0, i1, i2 = df_agg.index.get_level_values(0), df_agg.index.get_level_values(1), df_agg.index.get_level_values(2)
    ds = xr.Dataset(coords={"longitude": lon_coords, "latitude": lat_coords, "altitude": alt_coords})

    for name, col in df_agg.items():
        arr = np.zeros(shape, dtype=np.float32)
        arr[i0, i1, i2] = col.astype(np.float32)
        ds[name] = (("longitude", "latitude", "altitude"), arr)

    return ds


def _convert_daily_to_hourly(date: pd.Timestamp):
    date_str = date.strftime("%Y%m%d")
    file_path = f"{FOLDER_PATH}/{date_str}.pq"
    df_res = pd.read_parquet(file_path)

    # Downcast floats
    float_cols = df_res.select_dtypes(include=['float64']).columns
    df_res[float_cols] = df_res[float_cols].astype('float32')

    df_res['new_contrail_length'] = df_res['new_contrail_length'].fillna(0)

    # Filter by spatial and altitude bounds
    west, south, east, north = SPATIAL_BBOX
    df_res = df_res[
        df_res["longitude"].between(west, east)
        & df_res["latitude"].between(south, north)
        & df_res["altitude"].between(*ALTITUDE_BOUNDS_M)
    ].copy()

    # Coordinates
    lon_coords = np.arange(west, east + 0.01, SPATIAL_GRID_RES)
    lat_coords = np.arange(south, north + 0.01, SPATIAL_GRID_RES)
    alt_coords = np.arange(ALTITUDE_BOUNDS_M[0], ALTITUDE_BOUNDS_M[1] + ALTITUDE_RES_M, ALTITUDE_RES_M)
    df_res["hour"] = df_res["hour"].round().astype(int)

    # Time slices
    time_slices = np.arange(0, 25, TEMPORAL_RES_H)
    for t in range(len(time_slices) - 1):
        h_start, h_end = time_slices[t], time_slices[t + 1]
        filt = df_res["hour"].between(h_start, h_end, inclusive="left")
        df_hour = df_res[filt].copy()
        if len(df_hour) == 0:
            continue
        _grid_one_hour(date, h_start, h_end, df_hour, lon_coords, lat_coords, alt_coords)


def _grid_one_hour(date, h_start, h_end, df_hour, lon_coords, lat_coords, alt_coords):

    # Build expected output filename early
    t_start_str = date.strftime("%Y%m%d")
    t_end_str = f"{h_end:02d}"
    output_file = f"{OUTPUT_PATH}/{t_start_str}-{h_start:02d}-{t_end_str}-contrail.nc"

    # --- 🔍 Check if output already exists
    #if os.path.exists(output_file):
    #    print(f"⏩ Skipping existing file: {output_file}")
    #    return  # Nothing to do


    # Aggregations
    agg_map_1 = {
        'total_flight_dist': 'sum',
        #'new_contrail_length': 'sum',
        'contrail_ef_initial_loc': 'sum',
        'contrail_ef_overlap_initial_loc': 'sum',
    }
    ds_agg_1 = _agg_to_grid(df_hour, agg_map_1, lon_coords, lat_coords, alt_coords)

    #filt2 = df_hour["tau_contrail_area"].notna()
    #agg_map_2 = {'total_contrail_length': 'sum'}
    #ds_agg_2 = _agg_to_grid(df_hour[filt2], agg_map_2, lon_coords, lat_coords, alt_coords)

    filt3 = df_hour["contrail_ef"].notna()
    agg_map_3 = {
        'contrail_ef': 'sum',
        #'contrail_ef_sw': 'sum',
        #'contrail_ef_lw': 'sum',
        'contrail_ef_overlap': 'sum',
        #'contrail_ef_sw_overlap': 'sum',
        #'contrail_ef_lw_overlap': 'sum',
    }
    ds_agg_3 = _agg_to_grid(df_hour[filt3], agg_map_3, lon_coords, lat_coords, alt_coords)

    #filt4 = df_hour["mean_contrail_age"].notna()
    #df_hour["n"] = np.where(df_hour["tau_contrail_area"] > 0, 1, 0)
    #agg_map_4 = {
    #    'mean_contrail_age': 'mean',
    #    'tau_contrail_area': 'sum',
    #    'n': 'count',
    #}
    #ds_agg_4 = _agg_to_grid(df_hour[filt4], agg_map_4, lon_coords, lat_coords, alt_coords)
    #da_area = grid_surface_area(lon_coords, lat_coords)
    #ds_agg_4["tau_contrail"] = ds_agg_4["tau_contrail_area"] / (da_area * ds_agg_4["n"])

    # Merge hourly datasets
    ds = xr.Dataset(
        data_vars=dict(
            total_flight_dist=(["longitude", "latitude", "altitude"], ds_agg_1["total_flight_dist"].values / 1000),
            #new_contrail_length=(["longitude", "latitude", "altitude"], ds_agg_1["new_contrail_length"].values / 1000),
            #total_contrail_length=(["longitude", "latitude", "altitude"], ds_agg_2["total_contrail_length"].values / 1000),
            #tau_contrail=(["longitude", "latitude", "altitude"], ds_agg_4["tau_contrail"].values.astype('float32')),
            #mean_contrail_age=(["longitude", "latitude", "altitude"], ds_agg_4["mean_contrail_age"].values.astype('float32')),
            #ef_sw=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_sw"].values),
            #ef_lw=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_lw"].values),
            ef_net=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef"].values),
            ef_initial_loc=(["longitude", "latitude", "altitude"], ds_agg_1["contrail_ef_initial_loc"].values),
            #ef_sw_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_sw_overlap"].values),
            #ef_lw_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_lw_overlap"].values),
            ef_net_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_overlap"].values),
            ef_initial_loc_overlap=(["longitude", "latitude", "altitude"], ds_agg_1["contrail_ef_overlap_initial_loc"].values),
        ),
        coords=dict(longitude=lon_coords, latitude=lat_coords, altitude=alt_coords)
    )

    # Add time dimension
    t_mid = date + pd.Timedelta(hours=h_start + TEMPORAL_RES_H / 2)
    ds = ds.expand_dims().assign_coords({"time": t_mid})

    # Compression and saving
    t_start_str = date.strftime("%Y%m%d")
    t_end_str = f"{h_end:02d}"
    output_file = f"{OUTPUT_PATH}/{t_start_str}-{h_start:02d}-{t_end_str}-contrail.nc"


    comp = dict(zlib=True, complevel=4, dtype='float32')
    encoding = {var: comp for var in ds.data_vars}
    ds.to_netcdf(output_file, encoding=encoding)
    print(f"✅ Saved {output_file}")


def main():
    dates = pd.date_range(DATE_START, DATE_END, freq="1D")
    for date in tqdm(dates, desc="Processing days"):
        _convert_daily_to_hourly(date)


if __name__ == "__main__":
    main()
