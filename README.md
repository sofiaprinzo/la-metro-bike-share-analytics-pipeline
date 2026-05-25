# LA Metro Bike Share Analytics Pipeline

An end-to-end data engineering project using LA Metro Bike Share data to analyze station demand, trip patterns, and first-mile/last-mile mobility behavior in Los Angeles.

## Problem Statement

Transportation and venue operations teams need reliable mobility data to understand how people move through a city. This project builds a pipeline that ingests LA Metro Bike Share trip data, cleans and transforms it, and produces analytics tables for dashboard reporting.

Key questions:
- Which stations have the highest trip demand?
- What days and hours are busiest?
- Which station-to-station routes are most common?
- How do different passholder types use the system?
- What patterns could help transportation or event operations teams plan better?

## Data Source

LA Metro Bike Share public trip data:

https://bikeshare.metro.net/about/data/

See `docs/data_sources.md` for the exact raw files used by this project.

## Planned Architecture

```text
Raw CSV files
    -> Python ingestion
    -> Parquet data lake
    -> DuckDB warehouse
    -> SQL staging models
    -> SQL mart models
    -> CSV exports
    -> Tableau dashboard
```

## Tech Stack
- Python
- Pandas
- PyArrow
- DuckDB
- SQL
- Tableau Public
- Kestra

## Docker Run

The pipeline can be run in Docker after the raw Metro Bike Share files have been downloaded into `data/raw`.

Build the image:

```bash
docker compose build
```

Run the full local pipeline:

```bash
docker compose run --rm pipeline ./scripts/run_pipeline.sh
```

This runs:

```text
ingestion/ingest_trips.py
ingestion/ingest_stations.py
warehouse/build_warehouse.py
export/export_tableau_csvs.py
```

## Data Checks

After running the pipeline, validate the warehouse tables:

```bash
docker compose run --rm pipeline python tests/check_warehouse.py
```

## Orchestration

The Kestra flow in `orchestration/flows/la_bike_share_pipeline.yaml` defines the same local pipeline steps used by the Docker runner:

```text
ingest trips
ingest stations
build DuckDB warehouse
export Tableau CSV files
```

## Dashboard

The Tableau dashboard visualizes the reporting marts exported by the pipeline.

Dashboard link: [LA Metro Bike Share Demand Dashboard](https://public.tableau.com/shared/2S5YQT764?:display_count=n&:origin=viz_share_link)

The dashboard includes:

- hourly demand patterns
- weekly trip trends
- busiest pickup stations
- station activity map
- most popular station-to-station routes

![Dashboard overview](dashboard/tableau/screenshots/LA_Bike_Share_Demand_Dashboard.png)
