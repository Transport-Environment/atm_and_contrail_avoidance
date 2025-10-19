from datetime import datetime, timedelta
from tqdm import tqdm
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

API_KEY = ""
URL = "https://api.contrails.org"
HEADERS = {"x-api-key": API_KEY}

START_DATE = "2024-01-09"
END_DATE   = "2024-12-31"  # inclusive
OUTDIR = "data/sac"

os.makedirs(OUTDIR, exist_ok=True)

start_dt = datetime.fromisoformat(START_DATE)
end_dt   = datetime.fromisoformat(END_DATE)

def download_file(dt):
    time_str = dt.strftime("%Y-%m-%dT%H")
    fname = dt.strftime("%Y%m%dT%H") + ".nc"
    outpath = os.path.join(OUTDIR, fname)

    if os.path.exists(outpath):
        return f"Skipped {time_str} (already exists)"

    params = {
        "time": time_str,
        "bbox": "-180,-89,180,89",  # global
        "engine_efficiency": 0.32,
        "aircraft_type": "A320", 
        "format": "geojson"
    }

    try:
        r = requests.get(f"{URL}/v0/grid/sac", params=params,
                         headers=HEADERS, timeout=120)
                
        print(f"HTTP Response Code: {r.status_code} {r.reason}")
        print(f"Response content-type: {r.headers['content-type']}")

    except Exception as e:
        return f"Error {time_str}: {e}"

# Build list of datetimes
all_dts = []
curr_dt = start_dt
while curr_dt <= end_dt:
    for h in range(24):
        all_dts.append(curr_dt + timedelta(hours=h))
    curr_dt += timedelta(days=1)

# Run in parallel (tune workers to avoid server overload)
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(download_file, dt) for dt in all_dts]
    for future in as_completed(futures):
        print(future.result())