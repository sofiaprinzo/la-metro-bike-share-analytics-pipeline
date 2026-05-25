#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import click
import duckdb


def run_sql_file(con, sql_path):
    """Run a SQL file against DuckDB."""
    sql = Path(sql_path).read_text()
    con.execute(sql)


@click.command()
@click.option(
    "--trips-file",
    default="data/lake/trips_2026_q1.parquet",
    help="Path to the trips Parquet file in the local data lake",
)
@click.option(
    "--stations-file",
    default="data/lake/stations.parquet",
    help="Path to the stations Parquet file in the local data lake",
)
@click.option(
    "--database",
    default="data/warehouse/bikeshare.duckdb",
    help="Path to the DuckDB warehouse database",
)
def run(trips_file, stations_file, database):
    """Create DuckDB warehouse tables from local data lake files."""
    trips_path = Path(trips_file)
    stations_path = Path(stations_file)
    database_path = Path(database)

    if not trips_path.exists():
      raise FileNotFoundError(f"Trips file not found: {trips_path}")

    if not stations_path.exists():
      raise FileNotFoundError(f"Stations file not found: {stations_path}")

    database_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(database_path))

    con.execute("create schema if not exists raw")
    con.execute("create schema if not exists staging")
    con.execute("create schema if not exists marts")

    con.execute(
        """
        create or replace table raw.trips as
        select *
        from read_parquet(?)
        """,
        [str(trips_path)],
    )

    con.execute(
        """
        create or replace table raw.stations as
        select *
        from read_parquet(?)
        """,
        [str(stations_path)],
    )

    run_sql_file(con, "sql/staging/stg_trips.sql")
    run_sql_file(con, "sql/marts/dim_stations.sql")
    run_sql_file(con, "sql/marts/rpt_hourly_demand.sql")
    run_sql_file(con, "sql/marts/rpt_station_activity.sql")
    run_sql_file(con, "sql/marts/rpt_route_popularity.sql")

    raw_count = con.execute("select count(*) from raw.trips").fetchone()[0]
    staging_count = con.execute("select count(*) from staging.trips").fetchone()[0]
    hourly_count = con.execute("select count(*) from marts.rpt_hourly_demand").fetchone()[0]
    station_count = con.execute("select count(*) from marts.rpt_station_activity").fetchone()[0]
    route_count = con.execute("select count(*) from marts.rpt_route_popularity").fetchone()[0]
    
    stations_raw_count = con.execute("select count(*) from raw.stations").fetchone()[0]
    dim_station_count = con.execute("select count(*) from marts.dim_stations").fetchone()[0]
    

    con.close()

    print(f"Created raw.trips with {raw_count:,} rows")
    print(f"Created staging.trips with {staging_count:,} rows")
    print(f"Created marts.rpt_hourly_demand with {hourly_count:,} rows")
    print(f"Created marts.rpt_station_activity with {station_count:,} rows")
    print(f"Created marts.rpt_route_popularity with {route_count:,} rows")

    print(f"Created raw.stations with {stations_raw_count:,} rows")
    print(f"Created marts.dim_stations with {dim_station_count:,} rows")

    print(f"Wrote DuckDB database to {database_path}")


if __name__ == "__main__":
    run()