# Data Sources

This project uses public LA Metro Bike Share data.

Source page:

https://bikeshare.metro.net/about/data/

## Required Raw Files

Download quarterly trip files from the Metro Bike Share data page and place them in `data/raw`.
The trip ingestion step will read any files that match `metro-trips-*.csv`.

```text
data/raw/metro-trips-2026-q1.csv
data/raw/metro-trips-2026-q2.csv
data/raw/metro-trips-2026-q3.csv
data/raw/metro-bike-share-stations-2026-04-01.csv
```

Each trip file contains one quarter of bike share trips.

The station file contains station names, IDs, regions, statuses, and coordinates. It is used to make the reporting tables human-readable instead of showing only station ID numbers.

The trip ingestion step writes partitioned Parquet files under `data/lake/trips`, grouped by source year and quarter:

```text
data/lake/trips/year=2026/quarter=1/trips.parquet
data/lake/trips/year=2026/quarter=2/trips.parquet
```

## Reproducing the Data Files

Raw and generated data files are not committed to this repository, so after downloading the required raw files, run the Docker pipeline to recreate the Parquet, DuckDB, and Tableau export files:

```bash
docker compose run --rm pipeline ./scripts/run_pipeline.sh
```
