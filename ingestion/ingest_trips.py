#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import click
import pandas as pd


dtype = {
    "trip_id": "Int64",
    "duration": "Int64",
    "start_station": "Int64",
    "start_lat": "float64",
    "start_lon": "float64",
    "end_station": "Int64",
    "end_lat": "float64",
    "end_lon": "float64",
    "bike_id": "Int64",
    "plan_duration": "Int64",
    "trip_route_category": "string",
    "passholder_type": "string",
    "bike_type": "string",
}

parse_dates = [
    "start_time",
    "end_time",
]


@click.command()
@click.option(
    "--input-file",
    default="data/raw/metro-trips-2026-q1.csv",
    help="Path to the raw Metro Bike Share CSV file",
)
@click.option(
    "--output-file",
    default="data/lake/trips_2026_q1.parquet",
    help="Path where the cleaned Parquet file will be written",
)
def run(input_file, output_file):
    """Ingest LA Metro Bike Share trip data into the local data lake."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(
        input_path,
        dtype=dtype,
        parse_dates=parse_dates,
    )

    df.columns = df.columns.str.strip().str.lower()

    df = df.drop_duplicates(subset=["trip_id"])

    df = df[
        (df["start_time"].notna())
        & (df["end_time"].notna())
        & (df["duration"] > 0)
    ]

    df.to_parquet(output_path, index=False)

    print(f"Read {len(df):,} cleaned trips")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    run()