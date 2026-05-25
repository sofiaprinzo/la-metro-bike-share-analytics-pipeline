#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import click
import duckdb


EXPORT_TABLES = {
    "hourly_demand": "marts.rpt_hourly_demand",
    "station_activity": "marts.rpt_station_activity",
    "route_popularity": "marts.rpt_route_popularity",
    "stations": "marts.dim_stations",
}


@click.command()
@click.option(
    "--database",
    default="data/warehouse/bikeshare.duckdb",
    help="Path to the DuckDB warehouse database",
)
@click.option(
    "--output-dir",
    default="exports/tableau",
    help="Directory where Tableau CSV extracts will be written",
)
def run(database, output_dir):
    """Export dashboard-ready mart tables to CSV files."""
    database_path = Path(database)
    output_path = Path(output_dir)

    if not database_path.exists():
        raise FileNotFoundError(f"DuckDB database not found: {database_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(database_path))

    for file_name, table_name in EXPORT_TABLES.items():
        csv_path = output_path / f"{file_name}.csv"
        con.execute(
            f"""
            copy (
                select *
                from {table_name}
            ) to ? with (header, delimiter ',')
            """,
            [str(csv_path)],
        )
        print(f"Wrote {csv_path}")

    con.close()


if __name__ == "__main__":
    run()