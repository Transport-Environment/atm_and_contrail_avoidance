# Air traffic management implications of contrail avoidance

This repository analyses the **climate impact of contrails** using a combination of **traffic data, meteorological datasets, and contrail forcing simulations**.
It contains Jupyter notebooks, helper scripts, data, and visualisations exploring how **flight timing, routes, and airspace utilisation** contribute to contrail formation and radiative forcing.


## Project Overview

This project quantifies **contrail radiative forcing (RF)** over Europe and globally by analysing:

* 2019 European flight departures and their contrail warming,
* Gridded contrail forcing simulations using CoCiP,
* Gridded CoCiP outputs

## Repository Structure


| Component                     | Description                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **1_departures.ipynb**        | Analyses **2019 European departures** to assess contrail forcing by **month**, **hour**, and **airport**.  |
| **2_forcing.ipynb**           | Examines **2019 gridded contrail forcing outputs** to assess contrail forcing by **month**, **hour**, and **FIR**.           |
| **3_issr.ipynb**              | Detect **persistent contrail regions** (PCRs) from gridded CoCiP outputs (2024), evaluating their distribution and geometry.          |
| **4_airspace_capacity.ipynb** | Quantifies the **fraction of airspace volume** affected by warming/cooling contrails based on gridded CoCiP outputs (2024) and analyses it by flight level and time. |
| **supporting/**               | Contains supplementary notebooks for data acquisition and intermediate analyses.                                               |
| **data/**                     | Includes airports, FIRs, GeoJSON boundaries, and intermediate simulation results.                                              |
| **helpers/**                  | Python scripts for data conversion, downloads, and processing utilities.                                                       |
| **output/**                   | Generated CSV summaries and figures for visualisation.                                                                         |
| **figures/**                  | Visualisation outputs from each notebook (see below).                                                                          |


## Core Analyses

### 1Departures (`1_departures.ipynb`)

**Goal:** Quantify contrail forcing from 2019 European flights using the dataset presented in Teoh et al. (2024)

**Analyses:**

* Contrail forcing by **month of year** and **hour of day**
* Number of **“big hit”** flights (major warming contrails) by day, airport, and FIR
* Total CO₂ and contrail forcing per departure airport/FIR

**Figures:**

* ![Traffic by Month](figures/1_departures/departures_1_traffic_by_month@2x.png)
* ![Traffic by Hour](figures/1_departures/departures_2_traffic_by_hour@2x.png)
* ![Big Hits per Day per Airport](figures/1_departures/departures_3_big_hits_per_day_airport@2x.png)
* ![Big Hits per Day per FIR](figures/1_departures/departures_5_big_hits_per_day_fir@2x.png)
* ![Big Hits by FIR](figures/1_departures/departures_6_big_hits_by_fir@2x.png)


### Forcing (`2_forcing.ipynb`)

**Goal:** Evaluate **gridded forcing** from a newer 2019 simulation re-run by ICL with an updated version of pycontrails (v0.54.8). It has ~20% lower total energy forcing than the original publication and does not account for vPM activations. 

**Analyses:**

* File availability and statistics of forcing datasets
* Forcing per **flight distance**, **hour**, **month**, **flight level**, and **FIR**
* Comparison of **traffic density** and **warming intensity**


**Figures:**

* ![PQ File Availability](figures/2_forcing/forcing_1_pq_file_availability@2x.png)
* ![NetCDF Availability](figures/2_forcing/forcing_2_netcdf_file_availability@2x.png)
* ![Statistics](figures/2_forcing/forcing_3_statistics@2x.png)
* ![Flight Distance](figures/2_forcing/forcing_4_flight_distance@2x.png)
* ![Warming](figures/2_forcing/forcing_4_warming@2x.png)
* ![Warming P er Flight Distance](figures/2_forcing/forcing_4_per_distance@2x.png)
* ![Warming by Hour](figures/2_forcing/forcing_6_by_hour@2x.png)
* ![Warming by Month](figures/2_forcing/forcing_7_by_month@2x.png)
* ![Warming by FIR](figures/2_forcing/forcing_8_by_fir@2x.png)
* ![Airspace Activity](figures/2_forcing/forcing_9_how_busy_are_airspaces@2x.png)

### ISSRs (`3_issr.ipynb`)

**Goal:** Identify and characterize **persistent contrail regions** (PCRs) where persistent contrails form.
Data: Gridded CoCiP outputs for 2024 provided by contrails.org, using Airbus A320 (η = 0.032) as the reference aircraft.

**Method:**

* Detect connected regions exceeding a **forcing threshold (5 × 10⁸ J m⁻¹)**
* Compute per-region statistics: centroid, forcing, flight level, thickness, area, and volume

**Figures:**

* ![NetCDF Availability](figures/3_issr/issr_1_netcdf_file_availability@2x.png)
* ![ISSR Depth Distribution](figures/3_issr/issr_2_depth@2x.png)


### Airspace Capacity (`4_airspace_capacity.ipynb`)

**Goal:** Quantify **airspace capacity** in terms of contrail warming potential.

**Analyses:**

* Fraction of volume producing **cooling**, **warming**, and **highly warming** (80th / 95th percentile) contrails
* Aggregation by **week** and **flight level band**
* Derive **hourly and weekly statistics** for comparison

**Figures:**

* ![Forcing per Year](figures/4_airspace_capacity/airspace_capacity_1_forcing_per_year@2x.png)
* ![Forcing per Week](figures/4_airspace_capacity/airspace_capacity_2_forcing_per_week@2x.png)
* ![Forcing by Flight Level](figures/4_airspace_capacity/airspace_capacity_3_forcing_fl@2x.png)
* ![Weekly FL Comparison](figures/4_airspace_capacity/airspace_capacity_4_week_fl@2x.png)


## Supporting Notebooks

| Notebook                                             | Purpose                                                                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `20250808_Persistent_Contrails_From_ARCO_ERA5.ipynb` | Uses **FastMeteo** to download ERA5 weather data and map persistent contrail regions.               |
| `20250818_ACCF_and_GriddedCocip.ipynb`               | Compares **ACCFs** with **Gridded CoCiP** results.                                                  |
| `20250818_GAIA.ipynb`                                | Downloads and converts **GAIA** datasets to NetCDF format.                                          |
| `20250818_CoCiP.ipynb`                               | Demonstrates CoCiP usage for contrail simulations.                                                  |
| `20250821_Meteorological_Plots_ARCO_ERA5.ipynb`      | Plots meteorological parameters (T, RH, ISSR, SAC); loads one hour of ADS-B data from ADSBexchange. |
| `20251017_ADS-B_Traffic_Library_Demo.ipynb`          | Demonstrates loading and binning ADS-B traffic into FIRs.                                           |


## Helper Scripts

Key Python utilities in the `helpers/` folder:

* `contrail_forcing_sum_pq_parallel.py` — parallel aggregation of parquet files
* `contrail_forcing_parquet_to_netcdf.py` — conversion to NetCDF
* `create_airspace_geojson.py` — generation of FIR and airspace polygons
* `download_adsb.py` — download ADS-B traffic data
* `gaia_parquet_to_netcdf.py` — GAIA dataset conversion


## Data

The `/data` directory includes:

* **Airports, FIR boundaries, and country metadata**
* **GeoJSON** and **CSV** files for spatial aggregation
* **Gridded forcing outputs** (`hourly_totals.csv`)
* **ISSR datasets** (`ISSR and PCR depth distribution.csv`)

The datasets provided by contrails.org and Imperial College London are not included in this repository - partly because they are several 100 GBytes large. 


## Outputs

Final CSV summaries in `/output` are used for visualisation (e.g., via Flourish).
Each subfolder corresponds to a notebook (e.g., `/output/departures`, `/output/forcing`, `/output/issr`).


## Requirements

All dependencies are listed in `requirements.txt`.
Typical environment setup:

```bash
conda create -n contrail python=3.11
pip install -r requirements.txt
```
