# Data Sources

This project uses public LA Metro Bike Share data.

Source page:

https://bikeshare.metro.net/about/data/

## Required Raw Files

Download these files from the Metro Bike Share data page and place them in `data/raw`.

```text
data/raw/metro-trips-2026-q1.csv
data/raw/metro-bike-share-stations-2026-04-01.csv
```

The trip file contains Q1 2026 bike share trips.

The station file contains station names, IDs, regions, statuses, and coordinates. It is used to make the reporting tables human-readable instead of showing only station ID numbers.

## Reproducing the Data Files

Raw and generated data files are not committed to this repository, so after downloading the required raw files, run the Docker pipeline to recreate the Parquet, DuckDB, and Tableau export files:

```bash
docker compose run --rm pipeline ./scripts/run_pipeline.sh
```