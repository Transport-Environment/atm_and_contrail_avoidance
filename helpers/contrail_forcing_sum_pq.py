import pandas as pd
import numpy as np
import glob
from pathlib import Path
import re

# Folder containing daily parquet files (each with 24 hours of data)
folder_path = "./"  # adjust as needed
pq_files = sorted(glob.glob(f"{folder_path}/*.pq"))

print(f"found {len(pq_files)} files")
# Columns to sum
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

hourly_results = []

for file in pq_files:
    # Parse date from filename like '20190101.pq'
    fname = Path(file).stem
    m = re.search(r"(\d{8})", fname)
    if m:
        date_str = m.group(1)
        date = pd.Timestamp(date_str)
    else:
        date = pd.NaT

    # Load parquet file
    df = pd.read_parquet(file)
    df = df.fillna(0)

    hour_col = "hour"

    # Group by hour and sum over spatial/grid points
    df_hourly = df.groupby(hour_col)[COLS_SUM].sum(min_count=1).reset_index()

    # Build full timestamp for each hour
    df_hourly["timestamp"] = [date + pd.Timedelta(hours=int(h)) for h in df_hourly[hour_col]]

    # Add filename for traceability
    df_hourly["file"] = Path(file).name

    # Append to list
    hourly_results.append(df_hourly)

# Combine all hourly totals
df_all_hours = pd.concat(hourly_results, ignore_index=True).sort_values("timestamp")

# Compute grand totals across all hours
grand_totals = df_all_hours[COLS_SUM].sum().to_frame("total_sum")

# Show sample and results
print("\nHourly totals (sample):")
print(df_all_hours.head())

print(f"\nTotal number of hours: {len(df_all_hours)}")
print("\nGrand totals:")
print(grand_totals)

# Optionally save to CSV
df_all_hours.to_csv("data/gridded_forcing/hourly_totals.csv", index=False)
