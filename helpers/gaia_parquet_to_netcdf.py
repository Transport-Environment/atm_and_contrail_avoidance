"""
Convert GAIA files to a 4D grid (longitude-latitude-altitude-time).

The user is required to specify the:
- folder path containing the GAIA files that are downloaded from Zenodo
- output path to save the netcdf files, and
- spatial bounding box and spatiotemporal resolution of the 4D grid.

Python package requirements:
- numpy
- pandas
- pyarrow or fastparquet
- xarray
"""
import warnings
import numpy as np
import pandas as pd
import xarray as xr

# FOLDER_PATH
FOLDER_PATH_GAIA = "<Specify folder path that contains the .pq files>"
OUTPUT_PATH = "<Specify folder path that to save the .netcdf outputs>"

# Time dimension
DATE_START = "2019-01-01"
DATE_END = "2019-01-02"
TEMPORAL_RES_H = 1          # Permissible values: 1, 2, 3, 4, 6, 8, 12, 24

# Altitude dimension (m)
ALTITUDE_BOUNDS_M = (0.0, 18000.0)
ALTITUDE_RES_M = 152.4        # Decimals allowed (152.4 m == 500 feet)

# Longitude-latitude dimension (degrees)
SPATIAL_BBOX = (-180.0, -90.0, 180.0, 90.0)     # (west, south, east, north)
SPATIAL_GRID_RES = 0.5      # Permissible values: 0.05, 0.1, 0.2, 0.25, 0.5, 1


def main() -> None:
    dates = pd.date_range(start=DATE_START, end=DATE_END, freq="1D")

    # Check grid resolutions
    if TEMPORAL_RES_H not in [1, 2, 3, 4, 6, 8, 12, 24]:
        raise AssertionError(
            "`TEMPORAL_RES_H` only accepts the following inputs: 1, 2, 3, 4, 6, 8, 12, 24"
        )

    if SPATIAL_GRID_RES not in [0.05, 0.1, 0.2, 0.25, 0.5, 1]:
        raise AssertionError(
            "`SPATIAL_GRID_RES` only accepts the following inputs: 0.05, 0.1, 0.2, 0.25, 0.5, 1"
        )
        
    if SPATIAL_GRID_RES <= 0.25:
        warnings.warn(
            f"Selected spatial grid resolution ({SPATIAL_GRID_RES}) is very high, and the resulting"
            f"hourly netcdf4 (.nc) output file size could be greater than 5 GB."
        )

    for date in dates:
        _convert_tabular_grid_to_netcdf(date)

    return


def _convert_tabular_grid_to_netcdf(date: pd.Timestamp) -> None:
    date_str = date.strftime("%Y-%m-%d")
    file_path = f"{FOLDER_PATH_GAIA}/{date_str}-gaia.pq"
    df_gaia = pd.read_parquet(file_path)

    # Filter dataset
    west, south, east, north = SPATIAL_BBOX
    is_in_lon = df_gaia["longitude"].between(west, east, inclusive="both")
    is_in_lat = df_gaia["latitude"].between(south, north, inclusive="both")
    is_in_altitude = df_gaia["altitude_m"].between(
        ALTITUDE_BOUNDS_M[0], ALTITUDE_BOUNDS_M[1], inclusive="both"
    )
    df_gaia = df_gaia[is_in_lon & is_in_lat & is_in_altitude].copy()

    # Process dataset
    time_slices = np.arange(0, 25, TEMPORAL_RES_H)

    for t in range(len(time_slices) - 1):
        is_in_time = df_gaia["hour"].between(
            time_slices[t], time_slices[t + 1], inclusive="left"
        )
        df_gaia_t = df_gaia[is_in_time].copy()

        t_start = date + pd.Timedelta(hours=time_slices[t])
        t_end = date + pd.Timedelta(hours=time_slices[t + 1])
        _grid_one_time_slice(t_start, t_end, df_gaia_t)

    return


def _grid_one_time_slice(t_start: pd.Timestamp, t_end: pd.Timestamp, df_gaia_t: pd.DataFrame) -> None:
    west, south, east, north = SPATIAL_BBOX
    lon_coords = np.arange(west, east + 0.01, SPATIAL_GRID_RES)
    lat_coords = np.arange(south, north + 0.01, SPATIAL_GRID_RES)
    alt_coords = np.arange(
        ALTITUDE_BOUNDS_M[0], ALTITUDE_BOUNDS_M[1] + ALTITUDE_RES_M + 0.01, ALTITUDE_RES_M
    )
    shape = lon_coords.size, lat_coords.size, alt_coords.size

    idx_lon = np.searchsorted(lon_coords, df_gaia_t["longitude"])
    idx_lat = np.searchsorted(lat_coords, df_gaia_t["latitude"])
    idx_alt = np.searchsorted(alt_coords, df_gaia_t["altitude_m"])

    agg_map = {
        'seg_length_km': 'sum',
        'fuel_burn_kg': 'sum',
        'nox_kg': 'sum',
        'co_g': 'sum',
        'hc_g': 'sum',
        'nvpm_mass_mg': 'sum',
        'nvpm_number': 'sum',
    }

    df_agg = df_gaia_t.groupby([idx_lon, idx_lat, idx_alt]).agg(agg_map)

    index_0 = df_agg.index.get_level_values(0)
    index_1 = df_agg.index.get_level_values(1)
    index_2 = df_agg.index.get_level_values(2)
    index = index_0, index_1, index_2

    ds = xr.Dataset(
        coords={"longitude": lon_coords, "latitude": lat_coords, "altitude": alt_coords}
    )

    for name, col in df_agg.items():
        arr = np.zeros(shape, dtype=col.dtype)
        arr[index] = col
        ds[name] = (("longitude", "latitude", "altitude"), arr)

    # Add time dimension
    t_mid_point = t_start + pd.Timedelta(hours=(TEMPORAL_RES_H / 2))
    ds = ds.expand_dims().assign_coords({"time": t_mid_point})

    # Save to netcdf
    t_start_str = t_start.strftime("%Y%m%d-%H")
    t_end_h_str = t_end.strftime("%H")
    output_path = f"{OUTPUT_PATH}/{t_start_str}-{t_end_h_str}-gaia.nc"
    ds.to_netcdf(output_path)
    print(f"Complete: {output_path}")
    return


if __name__ == "__main__":
    main()
