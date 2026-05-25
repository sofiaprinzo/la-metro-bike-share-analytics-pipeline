# Tableau Dashboard

The Tableau dashboard uses CSV extracts generated from the DuckDB reporting marts.

Published dashboard:

[LA Metro Bike Share Demand Dashboard](https://public.tableau.com/shared/2S5YQT764?:display_count=n&:origin=viz_share_link)

## Exported Files

Run the export script from the project root:

```bash
python export/export_tableau_csvs.py
```

This creates:

```text
exports/tableau/hourly_demand.csv
exports/tableau/station_activity.csv
exports/tableau/route_popularity.csv
exports/tableau/stations.csv
```

## Dashboard Views

The dashboard includes:

- hourly demand patterns
- weekly trip trends
- busiest pickup stations
- station activity map
- most popular station-to-station routes

## Source Tables

The CSV files are exported from these DuckDB marts:

```text
marts.rpt_hourly_demand
marts.rpt_station_activity
marts.rpt_route_popularity
marts.dim_stations
```
