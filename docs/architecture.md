# Architecture

This project uses a local batch pipeline.

```text
Metro Bike Share quarterly CSV files
        |
        v
Python ingestion scripts
        |
        v
Partitioned Parquet files
        |
        v
DuckDB warehouse
        |
        v
SQL staging and reporting tables
        |
        v
Streamlit dashboard
```

## Raw Data

Metro Bike Share trip and station files start in `data/raw`.

Trip files are quarterly CSV files. The station file adds station names, regions, statuses, and coordinates.

## Data Lake

The trip ingestion script cleans the raw trip files and writes Parquet files under `data/lake/trips`.

Trips are partitioned by year and quarter, so new quarterly files can be added without changing the whole folder structure.

## Warehouse

DuckDB is used as the local database for analysis.

The warehouse build script reads the Parquet files, creates raw tables, and then runs the SQL files in `sql/staging` and `sql/marts`.

## Reporting Tables

The SQL models create tables for:

- cleaned trip records
- station details
- hourly demand
- station activity
- route popularity

## Dashboard

The Streamlit app reads from DuckDB and shows the reporting tables in an interactive dashboard.

For deployment, a smaller DuckDB file is created for the Streamlit app so the hosted version does not need the full local warehouse.
