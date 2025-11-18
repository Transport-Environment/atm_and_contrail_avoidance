# Sources

## General
- `worldfirs.json`: downloaded from https://observablehq.com/@openaviation/flight-information-regions#plot_fir
- `countries.csv`: downloaded from https://ourairports.com/data/
- `airports.csv`: downloaded from https://ourairports.com/data/
- `european_firs.csv`: list of European FIRs extracted from https://www.eurocontrol.int/publication/flight-information-region-firuir-charts-2024
- `airspaces.geojson`: combines `worldfirs.json` with bounding boxes from Teoh et al. 2024
- `worldfirst.geojson`: converted `worldfirs.json` to `.geojson` for Flourish

## 2019 departures
- `data\departures\2019 - Jet-A - Flight Summary.pq` provided by Imperial College London 
    - This file has 700 MB and contains all European arrivals and departures in 2019 
    - It corresponds to the data used in Teoh et al. 2019
    - It has the following structure

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