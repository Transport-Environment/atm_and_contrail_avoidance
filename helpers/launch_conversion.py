#!/usr/bin/env python3
import subprocess
import datetime
import sys
import math
import os
from datetime import timedelta

"""
GAIA Launcher + Missing File Checker

Checks for missing hourly contrail files in a given year,
and if necessary, reruns the daily GAIA script for missing days.
If no files are missing, can launch the year in N parallel chunks.

Usage:
    python launch_gaia.py <N_PROCESSES> [--check-only]

Example:
    python launch_gaia.py 4
    → Runs 4 parallel GAIA manager processes for 2019 if no files are missing.

    python launch_gaia.py 4 --check-only
    → Only checks missing files, does not launch parallel jobs.
"""

# === CONFIGURATION ===
YEAR = 2019
INDIR = "cdf"
SCRIPT_PATH = "parquet_to_netcdf_one_day.py"  # the per-day processor, either gaia_parquet_to_netcdf.py or contrail_forcing_parquet_to_netcdf.py


# --------------------------------------------------------------------
# 🔍 Missing file checker
# --------------------------------------------------------------------
def expected_filenames(year):
    """Generate all expected filenames for each hour in the given year."""
    start = datetime.datetime(year, 1, 1, 0)
    end = datetime.datetime(year + 1, 1, 1, 0)
    delta = timedelta(hours=1)

    expected = []
    while start < end:
        next_hour = start + delta
        # Handle the case where next_hour.hour == 0 (i.e., next day)
        # → end hour should be 24 of the current day
        if next_hour.hour == 0:
            fname = f"{start.strftime('%Y%m%d')}-{start.strftime('%H')}-24-contrail.nc"
        else:
            fname = f"{start.strftime('%Y%m%d')}-{start.strftime('%H')}-{next_hour.strftime('%H')}-contrail.nc"
        expected.append(fname)
        start = next_hour
    return expected

def check_missing_files(year, indir, min_size_mb=3):
    """
    Return list of missing filenames and affected days.
    A file is considered 'missing' if it:
      - does not exist, OR
      - exists but is smaller than `min_size_mb` megabytes.
    """
    # Expected filenames from your generator
    expected = expected_filenames(year)

    # Map existing filenames to their full paths
    existing_files = {
        f: os.path.join(indir, f)
        for f in os.listdir(indir)
        if f.endswith(".nc")
    }

    missing = []
    for fname in expected:
        path = existing_files.get(fname)
        if path is None:
            # File completely missing
            missing.append(fname)
        else:
            try:
                size_mb = os.path.getsize(path) / (1024 * 1024)
                if size_mb < min_size_mb:
                    print(f"⚠️  {fname} too small ({size_mb:.2f} MB) → marked as missing")
                    missing.append(fname)
            except OSError:
                # Handle broken symlinks or permission errors
                missing.append(fname)

    # Derive affected days (e.g. 'YYYYMMDD' from filename prefix)
    missing_days = sorted(set(f[:8] for f in missing))
    return missing, missing_days



# --------------------------------------------------------------------
# 🚀 Parallel launcher
# --------------------------------------------------------------------
def split_year(year: int, n_parts: int):
    start = datetime.date(year, 1, 1)
    end = datetime.date(year + 1, 1, 1)
    total_days = (end - start).days
    days_per_part = math.ceil(total_days / n_parts)

    ranges = []
    current = start
    for i in range(n_parts):
        next_date = min(current + datetime.timedelta(days=days_per_part), end)
        ranges.append((current, next_date))
        current = next_date
    return ranges


def launch_parallel(n_procs, year):
    """Launch GAIA processes in parallel for the given year."""
    date_ranges = split_year(year, n_procs)
    print(f"Launching {n_procs} GAIA manager processes for {year}...\n")

    processes = []
    for i, (start, end) in enumerate(date_ranges, start=1):
        print(f"🟢 Starting process {i}: {start} → {end}")
        p = subprocess.Popen(
            [sys.executable, SCRIPT_PATH, start.isoformat(), end.isoformat()]
        )
        processes.append(p)

    # Wait for all to complete
    for i, p in enumerate(processes, start=1):
        p.wait()
        print(f"✅ Process {i} finished with return code {p.returncode}")

    print("\n🎉 All GAIA manager processes completed successfully!")


def rerun_missing_days(missing_days):
    """Run daily script for missing days sequentially (format fixed)."""
    print(f"\n🔁 Reprocessing {len(missing_days)} missing days...\n")
    for day_str in missing_days:
        try:
            # Convert e.g. '20190102' → datetime.date(2019, 1, 2)
            day = datetime.datetime.strptime(day_str, "%Y%m%d").date()
            iso_day = day.isoformat()  # '2019-01-02'

            print(f"→ Running {SCRIPT_PATH} for {iso_day}")
            subprocess.run([sys.executable, SCRIPT_PATH, iso_day, iso_day], check=True)
        except Exception as e:
            print(f"⚠️ Failed to process {day_str}: {e}")
    print("\n✅ All missing days processed.")



# --------------------------------------------------------------------
# 🧠 Main
# --------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python launch_gaia.py <N_PROCESSES> [--check-only]")
        sys.exit(1)

    n_procs = int(sys.argv[1])
    check_only = "--check-only" in sys.argv

    print(f"🔎 Checking for missing hourly files for {YEAR} in {INDIR} ...")
    missing, missing_days = check_missing_files(YEAR, INDIR)

    if not missing:
        print("✅ All expected hourly files are present.")
        if not check_only:
            launch_parallel(n_procs, YEAR)
        else:
            print("🟡 Check-only mode: no launch executed.")
        return

    print(f"⚠️ Missing {len(missing)} hourly files in {len(missing_days)} distinct days.")
    for f in missing[:20]:
        print("  ", f)
    if len(missing) > 20:
        print("  ...")

    rerun = input("\nDo you want to re-run the daily script for missing days? [y/N]: ").strip().lower()
    if rerun == "y":
        rerun_missing_days(missing_days)
    else:
        print("No reprocessing performed.")

    print("\n✨ Done.")


if __name__ == "__main__":
    main()
