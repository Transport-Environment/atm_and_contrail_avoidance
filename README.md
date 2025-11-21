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
* Contrails simulations using CoCiP based on Spire ADS-B data kindly provided by the Imperial College London
    - Flight-by-flight information for European arrivals and departures for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/)
    - Gridded contrail simulation outputs (0.25° x 0.25° lateral resolution, 1000 ft (~300 m) vertical resolution, 1h temporal resolution) for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/), re-run by ICL with an updated version of pycontrails (v0.54.8), not accounting for vPM activation
* The high-resolution Global Aviation emissions Inventory based on ADS-B (![GAIA](https://zenodo.org/records/8369829)) for 2019 - 2021: High-resolution gridded outputs for 2019 (Full Year) with (0.05° x 0.05° lateral resolution, 100 m vertical resolution, 1h temporal resolution)
* ![Gridded CoCiP](https://egusphere.copernicus.org/preprints/2024/egusphere-2024-1361/) outputs for the year 2024 kindly provided by ![contrails.org](https://apidocs.contrails.org/notebooks/research_api.html) with (0.25° x 0.25° lateral resolution, 1000 ft (~300 m) vertical resolution, 1h temporal resolution)


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
* Total CO₂ and contrail forcing per departure airport
* FIR geometry is on ![worldfirs.json](data/worldfirs.json) found on ![observablehq.com/@openaviation](https://observablehq.com/@openaviation/flight-information-regions#plot_fir)

**Methodology:**

* Convert total_fuel_burn (kg of jet a1) and total_contrail_energy_forcing per flight to contrail CO2eq 
* The fuel burn is converted to forcings over 20 and 100 years using the the CO2 absolute global warming potential over 20-years () and 100-years () are assumed to be 2.39 × 10−14 and 88.0 × 10−15 yr W m−2 kg−1, respectively (Gaillot et al., 2023). These forcings reflect the amount of energy deposited in the atmosphere over a given amount of time - the amount of energy absorbed by the atmosphere through CO2 grows with time. 
* The GWP factors are the ratio of CO2 to contrail radiative forcing weighted by this ERF_RF_RATIO which makes the effective radiative forcing (ERF) smaller than the radiative forcing (RF) by a factor of 0.42. This factor is quite uncertain and reflects, among other things, how the global atmosphere reacts to a local radiative forcing in the long run. It is one of the reasons why the contrail climate impact is so uncertain and why I refrain from adding absolute values in the charts .

**Figures:**
<table>
  <tr>
    <td><img src="figures/1_departures/departures_1_traffic_by_month@2x.png" width="300"></td>
    <td><img src="figures/1_departures/departures_2_traffic_by_hour@2x.png" width="300"></td>
    <td><img src="figures/1_departures/departures_3_big_hits_per_day_airport@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/1_departures/departures_4_airports@2x.png" width="300"></td>
    <td><img src="figures/1_departures/departures_5_big_hits_per_day_fir@2x.png" width="300"></td>
    <td><img src="figures/1_departures/departures_6_big_hits_by_fir@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/1_departures/departures_7_by_distance@2x.png" width="300"></td>
    <td><img src="figures/1_departures/departures_8_by_aircraft@2x.png" width="300"></td>
  </tr>
</table>

### Forcing (`2_forcing.ipynb`)

**Goal:** Evaluate **gridded forcing** from a newer 2019 simulation re-run by ICL with an updated version of pycontrails (v0.54.8). It has ~20% lower total energy forcing than the original publication and does not account for vPM activations. 

**Analyses:**

* File availability and statistics of forcing datasets
    - Two approaches to analyse the data
        1. Convert tabular parquet files to hourly grid-based netcdf files & sum hourly grid-based files to get hourly, monthly and annual averages
        2. Directly sum parquet files for different FIRs to get hourly, monthly and annual statistics by FIR  - this method retains more of the original data fields since it is more memory efficient. At the same time, it discards spatial information. 
    - Both approaches agree numerically
* Maps of flight distance, warming and contrails per flight
    - Use netcdf files and aggregate using xarray
* Forcing per **flight distance**, **hour**, **month**, **flight level**, and **FIR**
    - User parquet files with the exception of forcing per flight level
    - Aggregate using pandas
* Region boundaries based on rectangular bounding boxes suggest in Teoh et al. 2024 as well as on lower flight information region boundaries that I assume to be 2D boundaries. I do not take into account the finite vertical extension of lower flight information regions. This is a simplication so that the 2D maps actually conver the full picture. 

**Figures:**

<table>
  <tr>
    <td><img src="figures/2_forcing/forcing_1_pq_file_availability@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_2_netcdf_file_availability@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_3_statistics@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/2_forcing/forcing_4_flight_distance@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_4_warming@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_5_by_flight_level@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/2_forcing/forcing_4_per_distance@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_6_by_hour@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_7_by_month@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/2_forcing/forcing_8_by_fir@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_9_how_busy_are_airspaces@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_10_contrail_concentration@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/2_forcing/forcing_11_low_traffic@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_12_low_load@2x.png" width="300"></td>
    <td><img src="figures/2_forcing/forcing_13_big_hits_per_day_fir@2x.png" width="300"></td>
  </tr>
</table>

### ISSRs (`3_issr.ipynb`)

**Goal:** Identify and characterize **persistent contrail regions** (PCRs) where persistent contrails form.

**Analyses:**
* Compute per-region statistics from Gridded CoCiP outputs: centroid, forcing, flight level, thickness, area, and volume
* Intro to gridded CoCiP: https://py.contrails.org/notebooks/CoCiPGrid.html and original publication: https://gmd.copernicus.org/articles/18/253/2025/

**Methodology:**
* Download gridded CoCiP output from contrails.org via their API (https://apidocs.contrails.org/notebooks/research_api.html)

* Data: Gridded CoCiP outputs for 2024 provided by contrails.org, using Airbus A320 (η = 0.32) as the reference aircraft.
* Hourly coverage not complete - around two days are missing despite repeated API requests
* Detect connected regions exceeding a **forcing threshold (5 × 10⁸ J m⁻¹)** that are fully contained within a fixed bounding box - lon = (-70.0°, 70.0°) and lat = (20.0°, 90.0°)
* This threshold comes from https://gmd.copernicus.org/articles/18/253/2025/: The grid-based CoCiP defines regions with strongly warming contrails based on the 80th percentile (5×10^8 J/m) and the 95th percentile (1.5×10^9 J/m) of EFcontrail per flight distance flown, both of which were derived from a 2019 global contrail simulation using the trajectory-based CoCiP (Teoh et al., 2024a).

**Potential problems:**
- The intersection condition implies that we potentially miss out on very big ISSRs that have very high longitudinal elongation - I tried to mitigate this by choosing a wide longitudinal bounding box. Given that we go up to the North pole, this method covers ISSRs as wide as 14,000 km at lower latitudes. 
- We do not track the evolution of ISSRs over time - in consecutive hours, we consider the same ISSR but don't actually track which ISSRs are the same  - so this is really an analysis about annual average properties of ISSRs rather than a study of how individual ISSRs evolve


**Figures:**

<table>
  <tr>
    <td><img src="figures/3_issr/issr_1_netcdf_file_availability@2x.png" width="300"></td>
    <td><img src="figures/3_issr/issr_2_contrail_map@2x.png" width="300"></td>
    <td><img src="figures/3_issr/issr_3_movement@2x.png" width="300"></td>
  </tr>
  <tr>
    <td><img src="figures/3_issr/issr_4_depth_volume@2x.png" width="300"></td>
    <td><img src="figures/3_issr/issr_5_contrail_region_explorer@2x.png" width="300"></td>
    <td><img src="figures/3_issr/issr_6_deviation_likelihood@2x.png" width="300"></td>
  </tr>
</table>



### Airspace Capacity (`4_airspace_capacity.ipynb`)

**Goal:** Quantify **airspace capacity** in terms of contrail warming potential.

**Analyses:**

* Download gridded CoCiP data for 2024 - see 3_issr.ipynb for more info
* Fraction of volume producing **cooling**, **warming**, and **highly warming** (80th / 95th percentile) contrails per hour of the year
* Aggregation by **week** and **flight level band**

**Figures:**
<table>
  <tr>
    <td><img src="figures/4_airspace_capacity/airspace_capacity_1_forcing_per_year@2x.png" width="400"></td>
    <td><img src="figures/4_airspace_capacity/airspace_capacity_2_forcing_per_week@2x.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="figures/4_airspace_capacity/airspace_capacity_3_forcing_fl@2x.png" width="400"></td>
    <td><img src="figures/4_airspace_capacity/airspace_capacity_4_week_fl@2x.png" width="400"></td>
  </tr>
</table>


## Supporting Notebooks

| Notebook                                             | Purpose                                                                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `20250808_Persistent_Contrails_From_ARCO_ERA5.ipynb` | Uses **FastMeteo** to download ERA5 weather data and map persistent contrail regions.               |
| `20250818_ACCF_and_GriddedCocip.ipynb`               | Compares **ACCFs** with **Gridded CoCiP** results.                                                  |
| `20250818_GAIA.ipynb`                                | Downloads and converts **GAIA** datasets to NetCDF format.                                          |
| `20250818_CoCiP.ipynb`                               | Demonstrates CoCiP usage for contrail simulations.                                                  |
| `20250821_Meteorological_Plots_ARCO_ERA5.ipynb`      | Plots meteorological parameters (T, RH, ISSR, SAC); loads one hour of ADS-B data from ADSBexchange. |
| `20251017_ADS-B_Traffic_Library_Demo.ipynb`          | Demonstrates loading and binning ADS-B traffic into FIRs.                                           |
| `20251121_GriddedForcing_to_Netcdf.ipynb`            | Demonstrates loading and converting gridded forcing parquet into netcdf.                            |


## Helper Scripts

Key Python utilities in the `helpers/` folder:

* `contrail_forcing_sum_pq_parallel.py` — parallel aggregation of parquet files
* `contrail_forcing_parquet_to_netcdf.py` — conversion to NetCDF
* `create_airspace_geojson.py` — generation of FIR and airspace polygons
* `download_adsb.py` — download ADS-B traffic data
* `gaia_parquet_to_netcdf.py` — GAIA dataset conversion


## Data

The `/data` directory includes:

### Airports, FIR boundaries, and country metadata
- `data/countries.csv`: downloaded from https://ourairports.com/data/
- `data/airports.csv`: downloaded from https://ourairports.com/data/
- `data/worldfirs.json`: downloaded from https://observablehq.com/@openaviation/flight-information-regions#plot_fir
- `data/european_firs.csv`: list of European FIRs extracted from https://www.eurocontrol.int/publication/flight-information-region-firuir-charts-2024
- `data/airspaces.geojson`: combines `data/worldfirs.json` with bounding boxes from Teoh et al. 2024
- `data/worldfirst.geojson`: converted `data/worldfirs.json` to `.geojson` for Flourish

### Departures
- `data\departures\2019 - Jet-A - Flight Summary.pq`: not included in this repository
  - flight schedules + contrail information on a flight-by-flight level
  - 700 MB and contains all European arrivals and departures in 2019 
  - Corresponds to the data used in Teoh et al. 2019

#### Departure file structure

| Column                                | Type (inferred) | Description                                         |
| ------------------------------------- | --------------- | --------------------------------------------------- |
| `flight_id`                           | string          | Unique flight identifier                            |
| `aircraft_type_icao`                  | string          | ICAO aircraft type code                             |
| `aircraft_engine_type`                | string          | Engine category (e.g., Jet, Turboprop)              |
| `origin_airport`                      | string          | Origin airport ICAO code                            |
| `origin_airport_name`                 | string          | Full airport name                                   |
| `origin_country`                      | string          | ISO country code for origin                         |
| `destination_airport`                 | string          | Destination airport ICAO code                       |
| `destination_airport_name`            | string          | Full destination airport name                       |
| `destination_country`                 | string          | ISO country code for destination                    |
| `first_waypoint_time`                 | datetime        | Timestamp of first waypoint                         |
| `last_waypoint_time`                  | datetime        | Timestamp of last waypoint                          |
| `flight_duration_h`                   | float           | Flight duration in hours                            |
| `total_flight_distance_km`            | float           | Total distance flown (km)                           |
| `total_fuel_burn`                     | float           | Fuel burn (kg)         |
| `engine_name`                         | string          | Engine commercial name                              |
| `engine_uid`                          | string          | Engine unique identifier                            |
| `mean_nvpm_ei_n`                      | float           | Mean non-volatile PM emission index                 |
| `total_contrail_length_sac_km`        | float           | SAC-form contrail length (km)                       |
| `total_persistent_contrail_length_km` | float           | Persistent contrail length (km)                     |
| `mean_contrail_lifetime`              | float           | Mean contrail lifetime                              |
| `max_contrail_lifetime`               | float           | Maximum contrail lifetime                           |
| `total_contrail_energy_forcing`       | float           | Energy forcing due to contrails (J)                    |

### Gridded forcing outputs
- Based on tabular, gridded forcing outputs from a CoCiP simulation provided by Imperial College London that are not included in this repository. 
- `data/gridded_forcing/annual_hourly_sum_XX.nc`: Netcdf files containing the annual gridded forcing in hour XX
- `data/gridded_forcing/monthly_sum_XX.nc`: Netcdf files containing the annual monthly forcing in month XX
- `data/gridded_forcing/annual_sum.nc`: Netcdf file containing the annual forcing sum
- `data/hourly_totals_by_region.pq`: Parquet file containing by region statistics


#### Original parquet file structure provided by ICL
| No. | Column                           | Description                                                                                                                                                               | Units |
|----:|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------|
| 1   | longitude                        | Longitude of grid cell                                                                                                                                                    | degrees |
| 2   | latitude                         | Latitude of grid cell                                                                                                                                                     | degrees |
| 3   | altitude                         | Altitude of grid cell                                                                                                                                                     | m |
| 4   | hour                             | Air traffic activity and contrail statistics between (hour − 1) and hour since midnight (UTC)                                                                              | h |
| 5   | total_flight_dist                | Total hourly flight distance flown at each grid cell (longitude, latitude, altitude, hour)                                                                                | km |
| 6   | new_contrail_length              | Total length of newly formed persistent contrails at each grid cell (longitude, latitude, altitude, hour)                                                                | km |
| 7   | total_contrail_length            | Total persistent contrail length at each grid cell (longitude, latitude, altitude, hour)                                                                                 | km |
| 8   | tau_contrail_area                | Sum of (contrail segment optical depth × length × width) at each grid cell. Used to calculate mean contrail optical depth.                                               | m² |
| 9   | mean_contrail_age                | Mean contrail segment age at each grid cell (longitude, latitude, altitude, hour)                                                                                        | h |
| 10  | contrail_ef_overlap_initial_loc  | Total contrail energy forcing at the initial location of contrail formation (with overlap effects)                                                                        | J |
| 11  | contrail_ef_overlap              | Total contrail energy forcing at each grid cell (with overlap effects)                                                                                                    | J |
| 12  | contrail_ef_sw_overlap           | Total shortwave contrail energy forcing at each grid cell (with overlap effects). Used for calculating mean shortwave radiative forcing.                                 | J |
| 13  | contrail_ef_lw_overlap           | Total longwave contrail energy forcing at each grid cell (with overlap effects). Used for calculating mean longwave radiative forcing.                                   | J |
| 14  | contrail_ef_initial_loc          | Total contrail energy forcing at the initial location of contrail formation (without overlap effects)                                                                     | J |
| 15  | contrail_ef                      | Total contrail energy forcing at each grid cell (without overlap effects)                                                                                                 | J |
| 16  | contrail_ef_sw                   | Total shortwave contrail energy forcing at each grid cell (without overlap effects). Used for calculating mean shortwave radiative forcing.                              | J |
| 17  | contrail_ef_lw                   | Total longwave contrail energy forcing at each grid cell (without overlap effects). Used for calculating mean longwave radiative forcing.                                | J |


#### Netcdf file structure

| Dimension  | Size  | Description |
|------------|-------|-------------|
| `longitude` | 1441 | Grid longitudes from -180.0° to 180.0° |
| `latitude`  | 721  | Grid latitudes from -90.0° to 90.0° |
| `altitude`  | 31   | Altitude levels (approx. 6000 m → 15 140 m)  |

| Name        | Shape        | Type     | Description |
|-------------|--------------|----------|-------------|
| `longitude` | (longitude,) | float64  | Longitude values in 0.25° resolution |
| `latitude`  | (latitude,)  | float64  | Latitude values in 0.25° resolution |
| `altitude`  | (altitude,)  | float64  | Altitude levels in meters in ~300 m (1000 ft) resolution |

| Variable                     | Dimensions (in order)                   | Type     | Description |
|------------------------------|------------------------------------------|----------|-------------|
| `total_flight_dist`         | (longitude, latitude, altitude)          | float32  | Total flight distance intersecting each grid cell |
| `ef_net`                    | (longitude, latitude, altitude)          | float32  | Net contrail energy forcing (all-sky) |
| `ef_initial_loc`            | (longitude, latitude, altitude)          | float32  | Energy forcing at the initial contrail location (no overlap) |
| `ef_net_overlap`            | (longitude, latitude, altitude)          | float32  | Net energy forcing including overlap effects |
| `ef_initial_loc_overlap`    | (longitude, latitude, altitude)          | float32  | Energy forcing attributed to initial location including overlap |

#### Parquet file structure

| Column                        | Type          | Description |
|-------------------------------|-----------------|-------------|
| `hour`                        | int             | Hour of day (0–23) for the aggregation window where hour 0 = [00:00, 00:59] and so on  |
| `total_flight_dist`          | float           | Total flown distance in the aggregation in km |
| `contrail_ef_initial_loc`    | float           | Contrail energy forcing at initial location (no overlap) in J|
| `contrail_ef_overlap_initial_loc` | float      | Contrail energy forcing at initial location accounting for overlap in J |
| `new_contrail_length`        | float           | Length of newly formed contrails in the time step |
| `total_contrail_length`      | float           | Total contrail length present in the aggregation |
| `tau_contrail_area`          | float           | Effective contrail optical depth integrated over area |
| `mean_contrail_age`          | float           | Mean age of contrails in the aggregation (e.g. hours) |
| `contrail_ef`                | float           | Net contrail energy forcing (all-sky, no overlap) |
| `contrail_ef_sw`             | float           | Shortwave component of contrail energy forcing |
| `contrail_ef_lw`             | float           | Longwave component of contrail energy forcing |
| `contrail_ef_overlap`        | float           | Net contrail energy forcing accounting for overlap |
| `contrail_ef_sw_overlap`     | float           | Shortwave contrail energy forcing with overlap |
| `contrail_ef_lw_overlap`     | float           | Longwave contrail energy forcing with overlap |
| `timestamp`                  | datetime        | Timestamp representing the start of the aggregation period |
| `region`                     | string          | Region label (e.g. `European Airspace`) |
| `file`                       | string          | Source file name for the aggregated data (e.g. `20190101.pq`) |

### ISSR datasets

- `data/issr/2024MMDDTHH.nc`: Hourly gridded CoCiP outputs provided by contrails.org
- `data/issr/contrail_region_details_2024.csv`: A summary of all PCRs with energy forcing greater than 5e8 J/m in 2024 completely contained within bounding box lon = (-70.0, 70.0) and lat = (20.0, 90.0) by hour

#### PCR file structure
| Column          | Type            | Description |
|-----------------|-----------------|-------------|
| `time`          | datetime        | Timestamp representing the aggregation window (e.g., `2024-01-01 00:00:00`) |
| `file`          | string          | Source file for the aggregated region (e.g., `20240101T00.nc`) |
| `region_id`     | int             | Unique numeric identifier for the region/cluster |
| `area_km2`      | float           | Total area of the region in square kilometers (sum of areas of grid cells) |
| `pt in mask`    | int             | Number of grid points included in the region mask |
| `vol_km3`       | float           | Total contrail volume in cubic kilometers (sum of volumes of grid cells)|
| `thickness_m`   | float           | Mean contrail layer thickness in meters |
| `std_thickness` | float           | Standard deviation of layer thickness |
| `mean_FL`       | float           | Mean flight level (e.g., FL320 = 32,000 ft) |
| `mean_lat`      | float           | Mean latitude of the region |
| `mean_lon`      | float           | Mean longitude of the region |
| `mean_forcing`  | float           | Mean radiative forcing over the region |
| `max_forcing`   | float           | Maximum radiative forcing in the region |
| `std_forcing`   | float           | Standard deviation of radiative forcing |
| `min_lat`       | float           | Minimum latitude of the region |
| `max_lat`       | float           | Maximum latitude of the region |
| `min_lon`       | float           | Minimum longitude of the region |
| `max_lon`       | float           | Maximum longitude of the region |
| `min_FL`        | float           | Minimum flight level present in the region |
| `max_FL`        | float           | Maximum flight level present in the region |
| `area_by_FL`    | dict[int → float] | Mapping of flight levels → area contribution (e.g. `{320: 23265.83, ...}`) |
| `thickness_ft`  | float           | Contrail layer thickness converted to feet |

### Airspace capacity
- `data\airspace_capacity\airspace_capacity.parquet`: A summary of airspace volumes and areas covered by PCRs by hour, region and flight level based on the hourly gridded CoCiP ouputs provided by contrails.org for 2024

#### Airspace capacity file structure

| Column          | Type            | Description |
|-----------------|-----------------|-------------|
| `time`          | datetime        | Timestamp representing the aggregation period (e.g., `2024-01-01 02:00:00`) |
| `file`          | string          | Source file used to compute the volume (e.g., `GriddedCoCip/20240101T02.nc`) |
| `region`        | string          | Geographic region name (e.g., `European Airspace`) |
| `flight_level`  | int             | Flight level (e.g., `300` → FL300 → 30,000 ft) |
| `forcing_case`  | string          | Forcing classification (e.g., `Negative`, `Positive`, `Neutral`) |
| `vol_total_km3` | float           | Total contrail volume across all forcing cases (km³) |
| `vol_case_km3`  | float           | Contrail volume associated with the specific forcing case (km³) |



## Outputs

Final CSV summaries in `/output` are used for visualisation (e.g., via Flourish).
Each subfolder corresponds to a notebook (e.g., `/output/departures`, `/output/forcing`, `/output/issr`).
The figures `figures/1.png` to `figures/XX.png` correspond to the figures used in T&E's report in order of appearance. The subfolders `figures/1_departures` etc. contain all the figures created by the respective notebook. 


## Requirements

All dependencies are listed in `requirements.txt`.
Typical environment setup:

```bash
conda create -n contrail_atm python=3.11
pip install -r requirements.txt
```

## Open question: 
- Grid definition (cell or edge centered?) for longitudes, latitudes, altitudes and times 
- Altitudes - barometric or not?
  - gridded forcing in m so probably not
  - gridded CoCiP? maybe
- searchsorted binnign
- make sure correct European Airspace boundary is used everywhere (i originally moved a rect but now i use the union of all eurocontrol firs ) - this is ont yet implemented in the airspace capacity analysis. 
- Check whether labelling algorithm works 

## Sources and special thanks

* Contrails simulations using CoCiP based on Spire ADS-B data kindly provided by the Imperial College London
    - Flight-by-flight information for European arrivals and departures for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/)
    - Gridded contrail simulation outputs (0.25° x 0.25° lateral resolution, 1000 ft (~300 m) vertical resolution, 1h temporal resolution) for the year 2019 based on ![Teoh et al. 2024](https://acp.copernicus.org/articles/24/6071/2024/), re-run by ICL with an updated version of pycontrails (v0.54.8), not accounting for vPM activation
* The high-resolution Global Aviation emissions Inventory based on ADS-B (![GAIA](https://zenodo.org/records/8369829)) for 2019 - 2021: High-resolution gridded outputs for 2019 (Full Year) with (0.05° x 0.05° lateral resolution, 100 m vertical resolution, 1h temporal resolution)
* ![Gridded CoCiP](https://egusphere.copernicus.org/preprints/2024/egusphere-2024-1361/) outputs for the year 2024 kindly provided by ![contrails.org](https://apidocs.contrails.org/notebooks/research_api.html) with (0.25° x 0.25° lateral resolution, 1000 ft (~300 m) vertical resolution, 1h temporal resolution)
* FIR geometry is on ![worldfirs.json](data/worldfirs.json) found on ![observablehq.com/@openaviation](https://observablehq.com/@openaviation/flight-information-regions#plot_fir)

* Special thanks to many external stakeholders from universities, research organisations, ANSPs etc. 
