import os
import requests
from datetime import datetime, timedelta


#!/usr/bin/env python3
"""
Script to pull ADS-B data for a specified UTC period and save to an output directory.
Usage example:
    python generate_adsb.py \
      --year 2025 --month 6 --day 1 \
      --start-hour 12 --start-minute 0 --start-second 0 \
      --duration 3600 --step 30 \
      --output-dir adsb_2025_06_01_hour

To run for all 12 months of 2025:
    for m in {1..12}; do \
      python generate_adsb.py \
        --year 2025 --month "$m" --day 1 \
        --start-hour 12 --start-minute 0 --start-second 0 \
        --duration 3600 --step 30 \
        --output-dir "adsb_2025_$(printf '%02d' "$m")_01_hour"; \
    done
"""
import argparse
import os
from datetime import datetime, timedelta

# -------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Pull ADS-B data for a given UTC period and save results."
    )
    parser.add_argument("--year",        type=int, default=2024,  help="Year (e.g. 2025)")
    parser.add_argument("--month",       type=int, required=1,    help="Month (1-12)")
    parser.add_argument("--day",         type=int, default=1,     help="Day (1-31)")
    parser.add_argument("--start-hour",  type=int, default=12,    help="UTC start hour (0-23)")
    parser.add_argument("--start-minute",type=int, default=0,     help="UTC start minute (0-59)")
    parser.add_argument("--start-second",type=int, default=0,     help="UTC start second (0-59)")
    parser.add_argument("--duration",    type=int, default=3600,  help="Total duration in seconds")
    parser.add_argument("--step",        type=int, default=60,    help="Sampling step size in seconds")
    parser.add_argument(
        "--output-dir", type=str, default="data\\flights\\",
        help="Directory to write output files (will be created if missing)"
    )
    return parser.parse_args()

args = parse_args()

# -------------------------------
# 🔧 CONFIGURATION
year = args.year
month = args.month
day = args.day

# Start time (UTC) for the period
start_hour = args.start_hour
start_minute = args.start_minute
start_second = args.start_second

# Duration (in seconds) and step size (in seconds)
duration_seconds = args.duration   # 1 hour
step_seconds = args.step          # every 30 seconds

def make_config_str(args):
    # ensure month/day are zero-padded
    year   = args.year
    month  = f"{args.month:02d}"
    day    = f"{args.day:02d}"
    h      = f"{args.start_hour:02d}"
    m      = f"{args.start_minute:02d}"
    s      = f"{args.start_second:02d}"
    dur    = args.duration
    step   = args.step
    folder = f"adsb_{year}_{month}_{day}_{h}_{m}_{s}_{dur}"
    return folder

# Output folder
folder = make_config_str(args)
output_dir = args.output_dir + "\\" + folder
# -------------------------------

# 🗂️ Prepare output directory
os.makedirs(output_dir, exist_ok=True)

# 🕒 Compute start datetime
start_dt = datetime(year, month, day, start_hour, start_minute, start_second)

# 🔁 Loop over time, stepping properly
current_dt = start_dt
end_dt = start_dt + timedelta(seconds=duration_seconds)

headers = {"Accept-Encoding": "identity"}

while current_dt <= end_dt:
    # Format HHMMSS
    filename = current_dt.strftime("%H%M%S") + "Z.json.gz"
    url = f"https://samples.adsbexchange.com/readsb-hist/{year:04d}/{month:02d}/{day:02d}/{filename}"

    print(f"➡️ Downloading {url}")
    try:
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        if r.status_code == 200:
            outpath = os.path.join(output_dir, filename)
            with open(outpath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Saved {outpath}")
        else:
            print(f"⚠️ {filename} not found (status {r.status_code})")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

    # Step forward
    current_dt += timedelta(seconds=step_seconds)

print("🎉 Done.")
