# Data Sources

This project uses public LA Metro Bike Share data.

Source page:

https://bikeshare.metro.net/about/data/

## Trip Data

Metro publishes trip files by quarter.

The downloader looks for files named like:

```text
metro-trips-2026-q1.csv
metro-trips-2026-q2.csv
```

The trip files include fields such as trip time, start station, end station, bike ID, passholder type, bike type, and route category.

## Station Data

The station file adds readable station information, including:

- station ID
- station name
- region
- status
- latitude and longitude

This makes the dashboard easier to read because it can show station names and regions instead of only station ID numbers.

## Generated Data

Raw and generated data files are not committed to the repository.

After the source files are downloaded, the pipeline creates:

```text
data/lake/trips/
data/warehouse/bikeshare.duckdb
data/manifest/trip_ingestion_manifest.json
```

The Streamlit deployment uses a smaller dashboard database:

```text
dashboard/streamlit/data/bikeshare_dashboard.duckdb
```

That file is generated from the local DuckDB warehouse and contains the data needed by the dashboard.
