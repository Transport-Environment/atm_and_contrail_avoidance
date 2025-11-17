# Air traffic management implications of contrail avoidance

This repository analyses the **climate impact of contrails** using a combination of **traffic data, meteorological datasets, and contrail forcing simulations**.
It contains Jupyter notebooks, helper scripts, data, and visualisations exploring how **flight timing, routes, and airspace utilisation** contribute to contrail formation and radiative forcing.


## Project Overview

This project quantifies **traffic levels** and **contrail warming** over Europe and the North Atlantic and globally by analysing:

* 2019 European flight departures and their contrail warming
* Gridded contrail forcing simulations based on CoCiP for 2019
* Gridded CoCiP outputs for 2024
* Global aviation emissions inventory based on ADS-B (GAIA) for 2019

It draws on the following datasets. 
* Contrails simulations kindly provided by the Imperial College London
    - Flight-by-flight information for European arrivals and departures for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/)
    - Gridded contrail simulation outputs (0.25 deg x 0.25 deg spatial resolution, 1h temporal resolution) for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/), re-run by ICL with an updated version of pycontrails (v0.54.8), not accounting for vPM activation
* The high-resolution Global Aviation emissions Inventory based on ADS-B (![GAIA](https://zenodo.org/records/8369829)) for 2019 - 2021: High-resolution gridded outputs for 2019 (Full Year)
* ![Gridded CoCiP](https://egusphere.copernicus.org/preprints/2024/egusphere-2024-1361/) outputs for the year 2024 kindly provided by ![contrails.org](https://apidocs.contrails.org/notebooks/research_api.html)


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

### Departures (`1_departures.ipynb`)

**Goal:** Quantify contrail forcing from 2019 European flights using the dataset presented in Teoh et al. (2024)

**Analyses:**

* Contrail forcing by **month of year** and **hour of day**
* Number of **“big hit”** flights (major warming contrails) by day, airport, and FIR
* Total CO₂ and contrail forcing per departure airport/FIR

**Figures:**

![Traffic by Month](figures/1_departures/departures_1_traffic_by_month@2x.png)
![Traffic by Hour](figures/1_departures/departures_2_traffic_by_hour@2x.png)
![Big Hits per Day per Airport](figures/1_departures/partures_3_big_hits_per_day_airport@2x.png)
![Warming per Departure Airport](figures/1_departures/departures_4_airports@2x.png)
![Big Hits per Day per FIR](figures/1_departures/departures_5_big_hits_per_day_fir@2x.png)
![Big Hits by FIR](figures/1_departures/departures_6_big_hits_by_fir@2x.png)
![Warming by Flight Distance](figures/1_departures/departures_7_by_distance@2x.png)
![Big Hits by Aircraft Class](figures/1_departures/departures_8_by_aircraft@2x.png)


### Forcing (`2_forcing.ipynb`)

**Goal:** Evaluate **gridded forcing** from a newer 2019 simulation re-run by ICL with an updated version of pycontrails (v0.54.8). It has ~20% lower total energy forcing than the original publication and does not account for vPM activations. 

**Analyses:**

* File availability and statistics of forcing datasets
    - I used to approaches to analyse the data
        1. Convert tabular parquet files to hourly grid-based netcdf files + sum hourly grid-based files to get hourly, monthly and annual averages
        2. Directly sum parquet files for different FIRs to get hourly, monthly and annual statistics by FIR  - this method retains more of the original data fields since it is more memory efficient. At the same time, I lose all spatial information. 
    - Both approaches agree numerically
* Maps of flight distance, warming and contrails per flight
    - Use netcdf files and aggregate using xarray
* Forcing per **flight distance**, **hour**, **month**, **flight level**, and **FIR**
    - User parquet files with the exception of forcing per flight level
    - Aggregate using pandas


**Figures:**

![PQ File Availability](figures/2_forcing/forcing_1_pq_file_availability@2x.png)
![NetCDF Availability](figures/2_forcing/forcing_2_netcdf_file_availability@2x.png)
![Statistics](figures/2_forcing/forcing_3_statistics@2x.png)
![Flight Distance](figures/2_forcing/forcing_4_flight_distance@2x.png)
![Warming](figures/2_forcing/forcing_4_warming@2x.png)
![Warming Per Flight Level](figures/2_forcing/forcing_5_by_flight_level@2x.png)
![Warming Per Flight Distance](figures/2_forcing/forcing_4_per_distance@2x.png)
![Warming by Hour](figures/2_forcing/forcing_6_by_hour@2x.png)
![Warming by Month](figures/2_forcing/forcing_7_by_month@2x.png)
![Warming by FIR](figures/2_forcing/forcing_8_by_fir@2x.png)
![Airspace Activity](figures/2_forcing/forcing_9_how_busy_are_airspaces@2x.png)
![Contrail Concentration](figures/2_forcing/forcing_10_contrail_concentration@2x.png)
![Contrail Opportunities Pt. 1](figures/2_forcing/forcing_11_low_traffic@2x.png)
![Contrail Opportunities Pt. 2](figures/2_forcing/forcing_12_low_load@2x.png)
![Contrail calendar](figures/2_forcing/forcing_13_big_hits_per_day_fir@2x.png)

### ISSRs (`3_issr.ipynb`)

**Goal:** Identify and characterize **persistent contrail regions** (PCRs) where persistent contrails form.
Data: Gridded CoCiP outputs for 2024 provided by contrails.org, using Airbus A320 (η = 0.032) as the reference aircraft.

**Method:**
* Download gridded CoCiP output from contrails.org via their API (https://apidocs.contrails.org/notebooks/research_api.html)
* Intro to gridded CoCiP: https://py.contrails.org/notebooks/CoCiPGrid.html and original publication: https://gmd.copernicus.org/articles/18/253/2025/
* Hourly coverage not complete - around two days are missing despite repeated API requests
* Detect connected regions exceeding a **forcing threshold (5 × 10⁸ J m⁻¹)** that are fully contained within a fixed bounding box - lon = (-70.0, 70.0) and lat = (20.0, 90.0)
* This threshold comes from https://gmd.copernicus.org/articles/18/253/2025/: The grid-based CoCiP defines regions with strongly warming contrails based on the 80th percentile (5×108 J m−1) and the 95th percentile (1.5×109 J m−1) of EFcontrail per flight distance flown, both of which were derived from a 2019 global contrail simulation using the trajectory-based CoCiP (Teoh et al., 2024a).
* Compute per-region statistics: centroid, forcing, flight level, thickness, area, and volume

**Weaknesses of this analysis:**
- The intersection condition implies that we potentially miss out on very big ISSRs that have very high longitudinal elongation
- We do not track the evolution of ISSRs over time - in consecutive hours, we consider the same ISSR but don't actually track which ISSRs are the same  - so this is really an analysis about annual average properties of ISSRs rather than a study of how individual ISSRs evolve


**Figures:**

![NetCDF Availability](figures/3_issr/issr_1_netcdf_file_availability@2x.png)
![PCR map](figures/3_issr/issr_2_contrail_map@2x.png)
![PCR movement](figures/3_issr/issr_3_movement@2x.png)
![ISSR Depth Distribution](figures/3_issr/issr_4_depth_volume@2x.png)
![Contrail Region explorer](figures/3_issr/issr_5_contrail_region_explorer@2x.png)
![Vertical deviations](figures/3_issr/issr_6_deviation_likelihood@2x.png)



### Airspace Capacity (`4_airspace_capacity.ipynb`)

**Goal:** Quantify **airspace capacity** in terms of contrail warming potential.

**Analyses:**

* Download gridded CoCiP regions - see 3_issr.ipynb for more info
* Fraction of volume producing **cooling**, **warming**, and **highly warming** (80th / 95th percentile) contrails
* Aggregation by **week** and **flight level band**
* Derive **hourly and weekly statistics** for comparison

**Figures:**

![Forcing per Year](figures/4_airspace_capacity/airspace_capacity_1_forcing_per_year@2x.g)
![Forcing per Week](figures/4_airspace_capacity/airspace_capacity_2_forcing_per_week@2x.g)
![Forcing by Flight Level](figures/4_airspace_capacity/airspace_capacity_3_forcing_fl@2x.g)
![Weekly FL Comparison](figures/4_airspace_capacity/airspace_capacity_4_week_fl@2x.png)


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
