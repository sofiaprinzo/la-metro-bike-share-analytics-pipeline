#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import click
import pandas as pd


dtype = {
    "Kiosk ID": "Int64",
    "Kiosk Name": "string",
    "Region ": "string",
    "Status": "string",
    "Latitude": "float64",
    "Longitude": "float64",
}

parse_dates = [
    "Go Live Date",
]


@click.command()
@click.option(
    "--input-file",
    default="data/raw/metro-bike-share-stations-2026-04-01.csv",
    help="Path to the raw Metro Bike Share station table",
)
@click.option(
    "--output-file",
    default="data/lake/stations.parquet",
    help="Path where the cleaned station Parquet file will be written",
)
def run(input_file, output_file):
    """Ingest LA Metro Bike Share station metadata into the local data lake."""
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

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    df = df.rename(
        columns={
            "kiosk_id": "station_id",
            "kiosk_name": "station_name",
        }
    )

    df = df.drop_duplicates(subset=["station_id"])

    df.to_parquet(output_path, index=False)

    print(f"Read {len(df):,} stations")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    run()