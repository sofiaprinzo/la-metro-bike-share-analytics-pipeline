# Architecture

I followed a local batch data pipeline pattern for this project:

```text
Metro Bike Share CSV files
        |
        v
Python ingestion scripts
        |
        v
Parquet files in data/lake
        |
        v
DuckDB warehouse
        |
        v
SQL staging and mart tables
        |
        v
CSV exports for Tableau
        |
        v
Tableau Public dashboard
```

## Pipeline Layers

### Raw Data

The raw Metro Bike Share trip and station CSV files are downloaded manually and stored in `data/raw`.

### Data Lake

The ingestion scripts clean the raw CSV files and write Parquet files to `data/lake`.

### Warehouse

DuckDB is used as the local analytical warehouse. The warehouse build script loads Parquet files into raw tables, then runs SQL models for staging and reporting.

### Transformations

SQL files in `sql/staging` and `sql/marts` create cleaned trip records, station dimensions, hourly demand metrics, station activity metrics, and route popularity metrics.

### Dashboard

The reporting marts are exported to CSV files for Tableau Public. The dashboard shows demand patterns, station activity, and popular routes.
