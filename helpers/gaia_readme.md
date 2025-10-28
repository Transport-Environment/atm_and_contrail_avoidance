
## GAIA data

Data repository for the global aviation emissions inventory based on ADS-B (GAIA): High-resolution gridded outputs for 2019 (full year)

ADS-B telemetry used to produce the global aviation emissions inventory was provided by Spire Aviation. Data is strictly for non-commercial use and research purposes only.

-----------
Description
-----------
This dataset contains the high resolution gridded outputs for the whole of 2019. The flight distance flown, fuel consumption and emissions from each flight waypoints are aggregated to a 4D grid.

To minimise the storage requirements, the dataset is saved in a tabular format (parquet, .pq). A Python script (parquet_to_netcdf.py) is included in this repository to convert the parquet files to the gridded outputs (netCDF-4, .nc). Users have the flexibility to specify their preferred spatiotemporal resolution of the gridded outputs to suit their modeling needs. The maximum spatiotemporal resolution that can be specified is 0.05° (longitude) x 0.05° (latitude) horizontal resolution, over altitude intervals of 100.0 m, and for each hour.

The following variables are provided in the gridded outputs: 
- `seg_length_km`: the sum of the total flight distance flown in each grid cell [Units: km]
- `fuel_burn_kg`: The total mass of fuel consumption in each grid cell [Units: kg]
- `nox_kg`: The total mass of nitrogen oxide (NOx) emissions in each grid cell [Units: kg]
- `co_g`: The total mass of carbon monoxide (CO) emissions in each grid cell [Units: g]
- `hc_g`: The total mass of unburnt hydrocarbon (HC) emissions in each grid cell [Units: g]
- `nvpm_mass_mg`: The total mass of non-volatile particulate matter (nvPM) emitted in each grid cell [Units: mg]
- `nvpm_number`: The total number of non-volatile particulate matter (nvPM) emitted in each grid cell [Units: -]

The following variables can be derived from the provided variables: 
- The mass of carbon dioxide (CO2) emitted in each grid cell by multiplying "fuel_burn" with a constant emissions index of 3.159 kg/kg.
- The mass of water vapour (H2O) emitted in each grid cell by multiplying "fuel_burn" with a constant emissions index of 1.237 kg/kg.
- The mass of organic carbon (OC) emitted in each grid cell by multiplying "fuel_burn" with a constant emissions index of 20 mg/kg.
- The mass of sulphur oxides (SO2) emitted in each grid cell by multiplying "fuel_burn" with a constant emissions index of 1.2 g/kg.
- The mass of sulphate particles (SVI) emitted in each grid cell by multiplying "fuel_burn" with a constant emissions index of 0.024 g/kg.
- The emission indices of each pollutant by dividing the total mass/number of each pollutant by the total fuel consumption at each grid cell.

## Contrail forcing data
 have provided you access to download the 2019 gridded outputs (https://console.cloud.google.com/storage/browser/data-sharing-transport-environment). The data description can be found in the Excel attachment above. 

You will need to convert the parquet files to 4D netCDF files, and you can customise the spatial resolution for the longitude, latitude, and altitude. Please refer to the codes annualise_grid.py and parquet_to_netcdf.py (in the Google cloud bucket) that I used to do the conversion for an earlier study. Unfortunately, it is not plug-and-play and cannot be directly applicable to this dataset, so you'll need to make some minor modifications. 

These results are from a more recent (yet to be published) simulations using pycontrails v0.54.8 without vPM activation, and the contrail RF is around 20% lower than those in the publication. We have to share this more recent dataset, rather than the publication, because the gridded outputs have a much higher spatiotemporal resolution. 