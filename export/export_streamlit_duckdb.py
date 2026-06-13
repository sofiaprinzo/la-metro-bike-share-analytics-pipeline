#!/usr/bin/env python
# coding: utf-8

import argparse
import shutil
from pathlib import Path

import duckdb


DEFAULT_SOURCE_DATABASE = Path("data/warehouse/bikeshare.duckdb")
DEFAULT_OUTPUT_DATABASE = Path("dashboard/streamlit/data/bikeshare_dashboard.duckdb")
DEFAULT_SOURCE_MANIFEST = Path("data/manifest/trip_ingestion_manifest.json")
DEFAULT_OUTPUT_MANIFEST = Path("dashboard/streamlit/data/trip_ingestion_manifest.json")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a smaller DuckDB file for the hosted Streamlit app."
    )
    parser.add_argument(
        "--source-database",
        default=DEFAULT_SOURCE_DATABASE,
        type=Path,
        help="Path to the full local DuckDB warehouse",
    )
    parser.add_argument(
        "--output-database",
        default=DEFAULT_OUTPUT_DATABASE,
        type=Path,
        help="Path where the Streamlit dashboard DuckDB file will be written",
    )
    parser.add_argument(
        "--source-manifest",
        default=DEFAULT_SOURCE_MANIFEST,
        type=Path,
        help="Path to the local ingestion manifest",
    )
    parser.add_argument(
        "--output-manifest",
        default=DEFAULT_OUTPUT_MANIFEST,
        type=Path,
        help="Path where the Streamlit manifest copy will be written",
    )
    return parser.parse_args()


def export_dashboard_database(source_database, output_database):
    if not source_database.exists():
        raise FileNotFoundError(f"Source database not found: {source_database}")

    output_database.parent.mkdir(parents=True, exist_ok=True)

    if output_database.exists():
        output_database.unlink()

    con = duckdb.connect(str(output_database))
    try:
        con.execute(f"attach '{source_database}' as source_db (read_only)")
        con.execute("create schema staging")
        con.execute("create schema marts")

        con.execute(
            """
            create table staging.trips as
            select
                trip_id,
                duration_minutes,
                trip_date,
                start_hour,
                day_of_week,
                start_station_id,
                start_lat,
                start_lon,
                end_station_id,
                bike_id,
                trip_route_category,
                passholder_type,
                bike_type,
                source_file,
                source_year,
                source_quarter,
                ingested_at
            from source_db.staging.trips
            """
        )
        con.execute(
            """
            create table marts.dim_stations as
            select *
            from source_db.marts.dim_stations
            """
        )
        con.execute(
            """
            create table marts.rpt_hourly_demand as
            select *
            from source_db.marts.rpt_hourly_demand
            """
        )
        con.execute(
            """
            create table marts.rpt_station_activity as
            select *
            from source_db.marts.rpt_station_activity
            """
        )
        con.execute(
            """
            create table marts.rpt_route_popularity as
            select *
            from source_db.marts.rpt_route_popularity
            """
        )
        con.execute("checkpoint")
    finally:
        con.close()


def copy_manifest(source_manifest, output_manifest):
    if not source_manifest.exists():
        return

    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_manifest, output_manifest)


def run():
    args = parse_args()
    export_dashboard_database(args.source_database, args.output_database)
    copy_manifest(args.source_manifest, args.output_manifest)
    print(f"Wrote {args.output_database}")

    if args.output_manifest.exists():
        print(f"Wrote {args.output_manifest}")


if __name__ == "__main__":
    run()
