# LA Metro Bike Share Analytics Pipeline

A batch data engineering project using public LA Metro Bike Share trip data to explore station demand, trip timing, and route patterns across Los Angeles.

## Dashboard

Hosted Streamlit app:

```text
https://la-metro-bike-share-analytics.streamlit.app/
```

The dashboard lets users explore:

- total trips, active stations, bikes, and date coverage
- demand by quarter, day, hour, region, passholder type, and bike type
- weekday vs weekend demand
- busiest stations and station activity maps
- station-level trends and top destinations
- popular routes, including one-way vs round-trip filtering
- processed files and table row counts

The dashboard is based on quarterly batch data. When Metro releases a new quarter, the pipeline can download the new file, rebuild the local warehouse, and refresh the dashboard data.

## Data Source

Data comes from LA Metro Bike Share's public trip data page:

https://bikeshare.metro.net/about/data/

Raw data files are not committed to this repository.

## Project Flow

```text
Metro quarterly CSV files
    -> Python ingestion
    -> partitioned Parquet files
    -> DuckDB warehouse
    -> SQL reporting tables
    -> Streamlit dashboard
```

## Tech Stack

- Python
- Pandas
- PyArrow
- DuckDB
- SQL
- Streamlit
- Kestra
- Docker

## Main Project Pieces

- `ingestion/`: downloads and cleans Metro Bike Share data
- `sql/`: builds staging and reporting tables
- `warehouse/`: creates the local DuckDB warehouse
- `tests/`: checks that the warehouse outputs look valid
- `orchestration/flows/`: contains the Kestra batch flow
- `dashboard/streamlit/`: contains the Streamlit dashboard

## Local Run

To run the pipeline locally:

```bash
docker compose build
docker compose run --rm pipeline python ingestion/download_trip_data.py
docker compose run --rm pipeline ./scripts/run_pipeline.sh
docker compose up streamlit
```

Then open:

```text
http://localhost:8501
```

## Local Kestra Schedule

Kestra can run the batch flow locally while Docker is running:

```bash
docker compose --profile orchestration up -d kestra
```

Then open:

```text
http://localhost:8080
```

Import this flow in the Kestra UI:

```text
orchestration/flows/la_bike_share_pipeline.yaml
```

The flow downloads new quarterly trip files, rebuilds the DuckDB warehouse, runs checks, and refreshes the Streamlit dashboard database.
