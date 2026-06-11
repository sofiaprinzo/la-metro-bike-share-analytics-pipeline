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


def get_trip_file_quarter(trip_file):
    """Read year and quarter from a file name like metro-trips-2026-q1.csv."""
    name_parts = trip_file.stem.split("-")

    if len(name_parts) != 4 or name_parts[:2] != ["metro", "trips"]:
        raise ValueError(f"Unexpected trip file name: {trip_file.name}")

    year = int(name_parts[2])
    quarter = int(name_parts[3].replace("q", ""))

    return year, quarter


def clean_trip_file(trip_file, year, quarter):
    """Clean one quarterly trip CSV and add source metadata."""
    df = pd.read_csv(
        trip_file,
        dtype=dtype,
        parse_dates=parse_dates,
    )

    df.columns = df.columns.str.strip().str.lower()

    df = df.drop_duplicates(subset=["trip_id"])

    df = df[
        (df["start_time"].notna())
        & (df["end_time"].notna())
        & (df["duration"] > 0)
    ].copy()

    df["source_file"] = trip_file.name
    df["source_year"] = year
    df["source_quarter"] = quarter
    df["ingested_at"] = pd.Timestamp.now(tz="UTC")

    return df


@click.command()
@click.option(
    "--input-dir",
    default="data/raw",
    help="Directory containing raw quarterly Metro Bike Share trip CSV files",
)
@click.option(
    "--output-dir",
    default="data/lake/trips",
    help="Directory where partitioned trip Parquet files will be written",
)
def run(input_dir, output_dir):
    """Ingest LA Metro Bike Share trip data into the local data lake."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    trip_files = sorted(input_path.glob("metro-trips-*.csv"))

    if not trip_files:
        raise FileNotFoundError(f"No trip CSV files found in {input_path}")

    total_rows = 0

    for trip_file in trip_files:
        year, quarter = get_trip_file_quarter(trip_file)
        quarter_output_path = output_path / f"year={year}" / f"quarter={quarter}"
        quarter_output_path.mkdir(parents=True, exist_ok=True)

        df = clean_trip_file(trip_file, year, quarter)
        parquet_path = quarter_output_path / "trips.parquet"
        df.to_parquet(parquet_path, index=False)

        total_rows += len(df)

        print(f"Read {len(df):,} cleaned trips from {trip_file}")
        print(f"Wrote {parquet_path}")

        del df

    print(f"Ingested {len(trip_files):,} trip file(s)")
    print(f"Wrote {total_rows:,} cleaned trips")


if __name__ == "__main__":
    run()
