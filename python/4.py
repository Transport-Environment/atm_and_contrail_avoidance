# %% [markdown]
# ## Analyse impact of contrail-sensitive regions on airspace capacity
# 
# 1. Download gridded CoCiP regions - see 3_issr.ipynb for more info
# 2. Compute areas and volumes of regions with different forcing per flight distance by hour or by week

# %% [markdown]
# ## 0. Analyse gridded CoCiP data

# %%
import numpy as np
import pandas as pd
import shapely
import regionmask
from scipy import ndimage
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import glob
import os
import xarray as xr
import json, topojson, geopandas as gpd, regionmask

# ---------------------------------------
# CONFIGURATION
# ---------------------------------------
input_pattern = "GriddedCoCip/2024*.nc"  # adjust this path
output_file = "airspace_capacity.parquet"
n_workers = 8  # use all but one core

R = 6371.0  # Earth radius in km

# Load the combined GeoDataFrame
gdf_combined = gpd.read_file("airspace.geojson").set_crs(epsg=4326)

# Build the region mask
firs_mask = regionmask.Regions(
    outlines=gdf_combined.geometry.values,
    names=gdf_combined["name"].tolist(),
    abbrevs=gdf_combined["name"].tolist()
)

        
# ---------------------------------------
# HELPER FUNCTION
# ---------------------------------------

def process_file(filepath):
    """
    Compute % of airspace volume above/below EFcontrail thresholds
    for each region (rectangular + FIR) and flight level.

    Cases:
      1. Negative forcing (EF < 0)
      2. Non-zero forcing (EF != 0)
      3. Positive forcing (EF > 0)
      4. > 5e8 J/m (80th percentile)
      5. > 1.54e9 J/m (95th percentile)
    """
    try:
        # ---------------------------------------------
        # 1️⃣ Load EF dataset
        # ---------------------------------------------
        ds = xr.open_dataset(filepath)
        ds_hr = ds.isel(time=0)
        ef = ds_hr["ef_per_m"].transpose("latitude", "longitude", "flight_level")

        lat = ef.latitude.values
        lon = ef.longitude.values
        lev = ef.flight_level.values
        time = pd.to_datetime(str(ds.time.values[0]))

        # sort by longitude
        ef = ef.assign_coords(longitude=lon).sortby("longitude")
        ef_data = ef.values
        valid_mask = np.isfinite(ef_data)

        
        # apply FIR mask to lat/lon grid
        mask_fir = firs_mask.mask(lon, lat).values  # (lat, lon)


        # ---------------------------------------------
        # 2️⃣ Grid cell area & vertical thickness
        # ---------------------------------------------
        R = 6371.0  # Earth radius in km
        dlat = np.deg2rad(np.abs(np.diff(lat)).mean())
        dlon = np.deg2rad(np.abs(np.diff(lon)).mean())
        lat_rad = np.deg2rad(lat)
        cell_area_lat = (R**2) * dlat * dlon * np.cos(lat_rad)
        area_2d = np.repeat(cell_area_lat[:, None], len(lon), axis=1)
        area_3d = np.repeat(area_2d[:, :, None], ef.shape[2], axis=2)

        fl_ft = lev * 100.0
        fl_m = fl_ft * 0.3048
        dz = np.mean(np.diff(fl_m)) if len(fl_m) > 1 else 0.0

        # ---------------------------------------------
        # 3️⃣ Define forcing category masks
        # ---------------------------------------------
        masks = {
            "Negative": (ef_data < 0) & valid_mask,
            "Non-zero": (ef_data != 0) & valid_mask,
            "Positive": (ef_data > 0) & valid_mask,
            "+80th-percentile": (ef_data > 5e8) & valid_mask,
            "+95th-percentile": (ef_data > 1.54e9) & valid_mask,
        }

        records = []

        # ---------------------------------------------
        # 5️⃣ FIR REGIONS (Topological polygons)
        # ---------------------------------------------
        try:
            for idx, fir_name in enumerate(firs_mask.names):
                fir_mask2d = mask_fir == idx
                if not np.any(fir_mask2d):
                    continue

                fir_mask3d = np.repeat(fir_mask2d[:, :, None], ef.shape[2], axis=2)
                reg_valid = valid_mask & fir_mask3d

                for case, case_mask in masks.items():
                    reg_case = case_mask & fir_mask3d
                    for i, level in enumerate(lev):
                        area_total = np.nansum(area_3d[:, :, i][reg_valid[:, :, i]])
                        area_case  = np.nansum(area_3d[:, :, i][reg_case[:, :, i]])
                        vol_total  = area_total * dz / 1000.0
                        vol_case   = area_case * dz / 1000.0

                        records.append({
                            "time": time,
                            "file": filepath,
                            "region": fir_name,
                            "flight_level": level,
                            "forcing_case": case,
                            "vol_total_km3": vol_total,
                            "vol_case_km3": vol_case,
                        })

        except Exception as e:
            print(f"⚠️ FIR processing skipped for {filepath}: {e}")

        # ---------------------------------------------
        # 6️⃣ Combine and return
        # ---------------------------------------------
        ds.close()
        return pd.DataFrame(records)

    except Exception as e:
        print(f"⚠️ Error processing {filepath}: {e}")
        import traceback; traceback.print_exc(limit=1)
        return pd.DataFrame([])



# %%
import traceback

# ---------------------------------------
# MAIN EXECUTION BLOCK 
# ---------------------------------------
def main():

    files = sorted(glob.glob(input_pattern))
    print(f"Found {len(files)} hourly files.")
    if not files:
        print("⚠️ No files matched the pattern.")
        return

    # --- optional: resume capability ---
    if os.path.exists(output_file):
        existing = pd.read_parquet(output_file)
        done_files = set(os.path.basename(f) for f in existing["file"].unique())
        files = [f for f in files if os.path.basename(f) not in done_files]
        all_dfs = [existing]
        print(f"Resuming from previous run: {len(done_files)} already processed.")
    else:
        all_dfs = []
        done_files = set()

    n_total = len(files)
    if n_total == 0:
        print("✅ All files already processed.")
        return

    # --- partial save configuration ---
    save_every = 20  # save every N files
    temp_file = output_file.replace(".parquet", "_partial.parquet")

    try:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(process_file, f): f for f in files}
            processed = 0

            for fut in tqdm(as_completed(futures), total=n_total, desc="Processing files"):
                filepath = futures[fut]
                try:
                    df_part = fut.result()
                    if not df_part.empty:
                        all_dfs.append(df_part)
                        done_files.add(os.path.basename(filepath))
                except Exception as e:
                    print(f"⚠️ Failure in {filepath}: {e}")
                    traceback.print_exc(limit=1)
                    continue

                processed += 1
                # --- periodic save ---
                if processed % save_every == 0:
                    try:
                        df_temp = pd.concat(all_dfs, ignore_index=True)
                        df_temp.to_parquet(temp_file, index=False)
                        print(f"💾 Saved interim results ({processed}/{n_total}) to {temp_file}")
                    except Exception as e:
                        print(f"⚠️ Could not save interim parquet: {e}")

    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user. Saving current progress...")
    except Exception as e:
        print(f"❌ Unexpected error in main loop: {e}")
    finally:
        # --- final save ---
        if all_dfs:
            df_final = pd.concat(all_dfs, ignore_index=True)
            df_final.to_parquet(output_file, index=False)
            print(f"✅ Saved {len(df_final)} total region records to {output_file}")
        else:
            print("⚠️ No valid data processed (nothing to save).")



# ---------------------------------------
# ENTRY POINT (required for multiprocessing)
# ---------------------------------------
if __name__ == "__main__":
    main()

# %% [markdown]
# ## 1. Weekly capacity averages by forcing mode (used in report)

# %%
# Helper function to sort regions as desired, round results and pivot df to structure required for Flourish
def pivot_to_regions(df, time_key, column_key='forcing_case'): 
    df_ = df.copy()
    # Round to two decimal places
    df_ = df_.round(6)

    # Pivot so forcing_case becomes columns
    df_pivot = df_.pivot_table(
        index=[time_key, 'region'],      # rows
        columns=column_key,                        # columns
        values='occupied_capacity',                     # values to fill
        sort=False
    ).reset_index()

    return df_pivot


# %%
import pandas as pd

df = pd.read_parquet("data/airspace_capacity/airspace_capacity.parquet")

df['time'] = pd.to_datetime(df['time'])

# Extract ISO year and week
df['week'] = df['time'].dt.isocalendar().week

# Group by year-week, region, and forcing_case
df_capacity_week = (
    df.groupby(['week', 'region', 'forcing_case'], sort=False)
      .agg({
          'vol_case_km3': 'sum',
          'vol_total_km3': 'sum'
      })
      .reset_index()
)

# Compute fraction of capacity
df_capacity_week['occupied_capacity'] = (
    df_capacity_week['vol_case_km3'] / df_capacity_week['vol_total_km3']
)

df_pivot = pivot_to_regions(df_capacity_week, time_key="week")

# Rename columns using a mapping dictionary
df_pivot = df_pivot.rename(columns={
    "week": "Week",
    "region": "Region",
    "+80th-percentile": "Very warming",
    "+95th-percentile": "Extremely warming",
    "Negative": "Cooling",
    "Non-zero": "Persistent contrails",
    "Positive": "Warming"
})

# Save to CSV
df_pivot.to_csv("output/airspace_capacity/1_annual_by_forcing_case.csv", index=False)

# %%
df_pivot

# %% [markdown]
# ![image.png](figures\4_airspace_capacity\airspace_capacity_1_forcing_per_year@2x.png)

# %% [markdown]
# ## 2. Hourly average by forcing mode (used in report)

# %%
import pandas as pd

df = pd.read_parquet("data/airspace_capacity/airspace_capacity.parquet")

df['time'] = pd.to_datetime(df['time'])

# Filter for the first week of 2024
df = df[
    (df['time'].dt.isocalendar().year == 2024) &
    (df['time'].dt.isocalendar().week == 1)
]

df['time_label'] = df['time'].dt.strftime('%m-%d %H')
region_order = df['region'].drop_duplicates().tolist()
df['region'] = pd.Categorical(df['region'], categories=region_order, ordered=True)


df = (
    df.groupby(['time_label', 'region', 'forcing_case'], sort=False)
      .agg({
          'vol_case_km3': 'sum',
          'vol_total_km3': 'sum'
      })
      .reset_index()
      .sort_values('time_label')  # ← sorts time_label only
)


# Compute fraction of capacity
df['occupied_capacity'] = (
    df['vol_case_km3'] / df['vol_total_km3']
)

df = pivot_to_regions(df, time_key="time_label")


# Rename columns using a mapping dictionary
df = df.rename(columns={
    "time_label": "Hour",
    "region": "Region",
    "+80th-percentile": "Very warming",
    "+95th-percentile": "Extremely warming",
    "Negative": "Cooling",
    "Non-zero": "Persistent contrails",
    "Positive": "Warming"
})

# Save to CSV
df.to_csv("output/airspace_capacity/2_week_by_forcing_case.csv", index=False)

# %%
df_pivot

# %% [markdown]
# ![image.png](figures\4_airspace_capacity\airspace_capacity_2_forcing_per_week.png)

# %% [markdown]
# ## 3. Weekly average by flight level (used in report)

# %%
import pandas as pd

df = pd.read_parquet("data/airspace_capacity/airspace_capacity.parquet")

df['time'] = pd.to_datetime(df['time'])

df_80      = df[df["forcing_case"]=="+80th-percentile"]

# Group by flight level bands to declutter plots
flight_level_bands = [
    (270, 290),  # lower upper airspace
    (300, 320),  # mid-level flows
    (330, 350),  # heavy-use cruise band
    (360, 380),  # high cruise
    (390, 410),  # upper high
    (420, 440),  # super-high, sparse traffic
]
def fl_band(fl):
    for low, high in flight_level_bands:
        if low <= fl <= high:
            return f"FL{low}-{high}"
    return "Other"

df_80["fl_band"] = df_80["flight_level"].apply(fl_band)

# group by time, region, and forcing_case
df_capacity = (
    df_80.groupby(['week', 'region', 'fl_band'], sort=False)
      .agg({
          'vol_case_km3': 'sum',      # occupied volume
          'vol_total_km3': 'sum'    # total capacity (same for all rows in group)
      })
      .reset_index()
)

# compute percentage or fraction of capacity used
df_capacity['occupied_capacity'] = df_capacity['vol_case_km3'] / df_capacity['vol_total_km3']

df_pivot = pivot_to_regions(df_capacity, time_key="week", column_key="fl_band")


# Rename columns using a mapping dictionary
df_pivot = df_pivot.rename(columns={
    "week": "Week",
    "region": "Region"
})

# Save to CSV
df_pivot.to_csv("output/airspace_capacity/3_annual_by_flight_level.csv", index=False)



# %% [markdown]
# ![image.png](figures\4_airspace_capacity\airspace_capacity_3_forcing_fl@2x.png)

# %% [markdown]
# ## 4. Hourly averages by flight level (not used in report)

# %%
import pandas as pd

df = pd.read_parquet("data/airspace_capacity/airspace_capacity.parquet")

df['time'] = pd.to_datetime(df['time'])

df_80            = df[df["forcing_case"]=="+80th-percentile"]
df_80["fl_band"] = df_80["flight_level"].apply(fl_band)


# Filter for the first week of 2024
df_80 = df_80[
    (df['time'].dt.isocalendar().year == 2024) &
    (df['time'].dt.isocalendar().week == 1)
]

df_80['time_label'] = df_80['time'].dt.strftime('%m-%d %H')

# group by time, region, and forcing_case
df_capacity = (
    df_80.groupby(['time_label', 'region', 'fl_band'])
      .agg({
          'vol_case_km3': 'sum',      # occupied volume
          'vol_total_km3': 'sum'    # total capacity (same for all rows in group)
      })
      .reset_index()
)

# compute percentage or fraction of capacity used
df_capacity['occupied_capacity'] = df_capacity['vol_case_km3'] / df_capacity['vol_total_km3']

df_pivot = pivot_to_regions(df_capacity, time_key="time_label", column_key="fl_band")


# Rename columns using a mapping dictionary
df_pivot = df_pivot.rename(columns={
    "time_label": "Hour",
    "region": "Region"
})

# Save to CSV
df_pivot.to_csv("output/airspace_capacity/4_week_by_flight_level.csv", index=False)



# %% [markdown]
# ![image.png](figures\4_airspace_capacity\airspace_capacity_4_week_fl@2x.png)


