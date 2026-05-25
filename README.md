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