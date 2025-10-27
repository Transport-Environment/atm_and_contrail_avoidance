import numpy as np
import pandas as pd
import xarray as xr

from tqdm import tqdm
from pycontrails.physics.geo import grid_surface_area


SIM_NAMES = [
    "2019-jet-a-no-vpm"
]

# Altitude dimension (m)
ALTITUDE_BOUNDS_M = (6000.0, 15000.0)
ALTITUDE_RES_M = 304.8        # Decimals allowed (152.4 m == 500 feet)

# Longitude-latitude dimension (degrees)
SPATIAL_BBOX = (-180.0, -90.0, 180.0, 90.0)     # (west, south, east, north)
SPATIAL_GRID_RES = 0.25      # Permissible values: 0.25, 0.5, 1


def _agg_to_grid(
    df_res: pd.DataFrame, 
    agg_map: dict, 
    lon_coords: np.ndarray, 
    lat_coords: np.ndarray, 
    alt_coords: np.ndarray,
) -> xr.Dataset:
    shape = lon_coords.size, lat_coords.size, alt_coords.size
    
    # Aggregate to 3D grid
    idx_lon = np.searchsorted(lon_coords, df_res["longitude"])
    idx_lat = np.searchsorted(lat_coords, df_res["latitude"])
    idx_alt = np.searchsorted(alt_coords, df_res["altitude"])
    
    # Aggregation
    var_names = ["longitude", "latitude", "altitude"] + list(agg_map.keys())
    df_agg = df_res[var_names].groupby([idx_lon, idx_lat, idx_alt]).agg(agg_map)

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
        
    return ds


def convert_tabular_to_grid_one_day(folder_path: str, date: pd.Timestamp) -> xr.Dataset:
    date_str = date.strftime("%Y%m%d")
    file_path = f"{folder_path}/{date_str}.pq"
    df_res = pd.read_parquet(file_path)

    # Convert nan to zero
    df_res['new_contrail_length'] = df_res['new_contrail_length'].fillna(0)
    
    # Filter dataset
    west, south, east, north = SPATIAL_BBOX
    is_in_lon = df_res["longitude"].between(west, east, inclusive="both")
    is_in_lat = df_res["latitude"].between(south, north, inclusive="both")
    is_in_altitude = df_res["altitude"].between(
        ALTITUDE_BOUNDS_M[0], ALTITUDE_BOUNDS_M[1], inclusive="both"
    )
    df_res = df_res[is_in_lon & is_in_lat & is_in_altitude].copy()
    
    # Initialise 3D coordinates
    lon_coords = np.arange(west, east + 0.01, SPATIAL_GRID_RES)
    lat_coords = np.arange(south, north + 0.01, SPATIAL_GRID_RES)
    alt_coords = np.arange(
        ALTITUDE_BOUNDS_M[0], ALTITUDE_BOUNDS_M[1] + ALTITUDE_RES_M + 0.01, ALTITUDE_RES_M
    )
    
    # Aggregation 1
    agg_map = {
        'total_flight_dist': 'sum',
        'new_contrail_length': 'sum',
        'contrail_ef_initial_loc': 'sum',
        'contrail_ef_overlap_initial_loc': 'sum',
    }
    ds_agg_1 = _agg_to_grid(df_res, agg_map, lon_coords, lat_coords, alt_coords)
    
    # Aggregation 2
    filt = df_res["tau_contrail_area"].notna()
    agg_map = {
        'total_contrail_length': 'sum',
    }
    ds_agg_2 = _agg_to_grid(df_res[filt].copy(), agg_map, lon_coords, lat_coords, alt_coords)
    da_area = grid_surface_area(ds_agg_2["longitude"].values, ds_agg_2["latitude"].values)
    # ds_agg_2["tau_contrail"] = ds_agg_2["tau_contrail"].where(ds_agg_2["tau_contrail"] > 0, np.nan)
    
    # Aggregation 3
    filt = df_res["contrail_ef"].notna()
    agg_map = {
        'contrail_ef': 'sum',
        'contrail_ef_sw': 'sum',
        'contrail_ef_lw': 'sum',
        'contrail_ef_overlap': 'sum',
        'contrail_ef_sw_overlap': 'sum',
        'contrail_ef_lw_overlap': 'sum',
    }
    ds_agg_3 = _agg_to_grid(df_res[filt].copy(), agg_map, lon_coords, lat_coords, alt_coords)
    
    # Aggregation 4
    filt = df_res["mean_contrail_age"].notna()
    df_res["n"] = np.where(df_res["tau_contrail_area"] > 0 , 1, 0)
    agg_map = {
        'mean_contrail_age': 'mean',
        'tau_contrail_area': 'sum',
        'n': 'count',
    }
    ds_agg_4 = _agg_to_grid(df_res[filt].copy(), agg_map, lon_coords, lat_coords, alt_coords)
    ds_agg_4["tau_contrail"] = ds_agg_4["tau_contrail_area"] / (da_area * ds_agg_4["n"])
    # ds_agg_4["mean_contrail_age"] = ds_agg_4["mean_contrail_age"].where(ds_agg_4["mean_contrail_age"] > 0, np.nan)
    
    # Combine daily outputs to one xr.Dataset
    ds = xr.Dataset(
        data_vars=dict(
            total_flight_dist=(["longitude", "latitude", "altitude"], (ds_agg_1["total_flight_dist"].values / 1000)),
            new_contrail_length=(["longitude", "latitude", "altitude"], (ds_agg_1["new_contrail_length"].values / 1000)),
            total_contrail_length=(["longitude", "latitude", "altitude"], (ds_agg_2["total_contrail_length"].values / 1000)),
            tau_contrail=(["longitude", "latitude", "altitude"], ds_agg_4["tau_contrail"].values),
            mean_contrail_age=(["longitude", "latitude", "altitude"], ds_agg_4["mean_contrail_age"].values),
            ef_sw=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_sw"].values),
            ef_lw=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_lw"].values),
            ef_net=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef"].values),
            ef_initial_loc=(["longitude", "latitude", "altitude"], ds_agg_1["contrail_ef_initial_loc"].values),
            ef_sw_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_sw_overlap"].values),
            ef_lw_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_lw_overlap"].values),
            ef_net_overlap=(["longitude", "latitude", "altitude"], ds_agg_3["contrail_ef_overlap"].values),
            ef_initial_loc_overlap=(["longitude", "latitude", "altitude"], ds_agg_1["contrail_ef_overlap_initial_loc"].values),
        ),
        coords=dict(longitude=ds_agg_1.longitude, latitude=ds_agg_1.latitude, altitude=ds_agg_1.altitude)
    )
    
    ds.expand_dims().assign_coords({"time": date})
    return ds


COLS_SUM = [
    "total_flight_dist", "new_contrail_length",
    "ef_sw", "ef_lw", "ef_net", "ef_initial_loc", 
    "ef_sw_overlap", "ef_lw_overlap", "ef_net_overlap", "ef_initial_loc_overlap", 
    "mean_contrail_age"
]


def one_simulation_run(sim_name: str):
    print(sim_name)

    # Time dimension
    year = sim_name[:4]
    date_start = f"{year}-01-01"
    date_end = f"{year}-12-31"
    dates = pd.date_range(start=date_start, end=date_end, freq="1D")
    folder_path = f"gs://contrails-301217-global-contrail-simulations-vpm-v2/{sim_name}/grid"
    
    ds_annual = convert_tabular_to_grid_one_day(folder_path, dates[0])
    
    n_counts = np.zeros(np.shape(ds_annual["total_flight_dist"].values))
    n_counts += np.where(ds_annual["mean_contrail_age"].values > 0, 1, 0)
    
    for date in tqdm(dates[1:]):
        ds_day = convert_tabular_to_grid_one_day(folder_path, date)
        n_counts += np.where(ds_day["mean_contrail_age"].values > 0, 1, 0)
    
        for var in COLS_SUM:
            ds_annual[var] = ds_annual[var] + ds_day[var]

    # Mean metrics
    ds_annual["tau_contrail"] = ds_annual["tau_contrail"] / n_counts
    ds_annual["mean_contrail_age"] = ds_annual["mean_contrail_age"] / n_counts
    ds_annual["mean_contrail_age"] = ds_annual["mean_contrail_age"].where(ds_annual["mean_contrail_age"] <= 12.0, 12.0)
    
    ds_annual["n_contrails"] = xr.DataArray(
        n_counts, 
        dims=["longitude", "latitude", "altitude"],
        coords={"longitude": ds_annual.longitude.values, "latitude": ds_annual.latitude.values, "altitude": ds_annual.altitude.values},
    )
    
    # Save outputs
    fpath = f"res/{sim_name}-grid-annualised.nc"
    ds_annual.to_netcdf(fpath)
    return


for SIM_NAME in SIM_NAMES:
    one_simulation_run(SIM_NAME)

