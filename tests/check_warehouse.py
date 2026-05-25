from pathlib import Path

import duckdb


DATABASE_PATH = Path("data/warehouse/bikeshare.duckdb")

EXPECTED_TABLES = {
    "raw.trips": 88932,
    "raw.stations": 448,
    "staging.trips": 88932,
    "marts.dim_stations": 447,
    "marts.rpt_hourly_demand": 2120,
    "marts.rpt_station_activity": 230,
    "marts.rpt_route_popularity": 10021,
}


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "DuckDB warehouse not found. Run the pipeline before checking outputs."
        )

    con = duckdb.connect(str(DATABASE_PATH))

    for table_name, expected_rows in EXPECTED_TABLES.items():
        actual_rows = con.sql(f"select count(*) from {table_name}").fetchone()[0]

        if actual_rows != expected_rows:
            raise ValueError(
                f"{table_name} expected {expected_rows:,} rows but found {actual_rows:,}"
            )

        print(f"{table_name}: {actual_rows:,} rows")

    print("Warehouse checks passed.")


if __name__ == "__main__":
    main()