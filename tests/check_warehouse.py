from pathlib import Path

import duckdb


DATABASE_PATH = Path("data/warehouse/bikeshare.duckdb")

REQUIRED_TABLES = [
    "raw.trips",
    "raw.stations",
    "staging.trips",
    "marts.dim_stations",
    "marts.rpt_hourly_demand",
    "marts.rpt_station_activity",
    "marts.rpt_route_popularity",
]


def check_nonempty_table(con, table_name):
    row_count = con.sql(f"select count(*) from {table_name}").fetchone()[0]

    if row_count == 0:
        raise ValueError(f"{table_name} has no rows")

    print(f"{table_name}: {row_count:,} rows")


def check_query_returns_zero(con, check_name, sql):
    failed_rows = con.sql(sql).fetchone()[0]

    if failed_rows != 0:
        raise ValueError(f"{check_name} failed with {failed_rows:,} row(s)")

    print(f"{check_name}: passed")


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "DuckDB warehouse not found. Run the pipeline before checking outputs."
        )

    con = duckdb.connect(str(DATABASE_PATH))

    for table_name in REQUIRED_TABLES:
        check_nonempty_table(con, table_name)

    check_query_returns_zero(
        con,
        "duplicate staging trip_id check",
        """
        select count(*)
        from (
            select trip_id
            from staging.trips
            group by trip_id
            having count(*) > 1
        )
        """,
    )
    check_query_returns_zero(
        con,
        "invalid trip timing check",
        """
        select count(*)
        from staging.trips
        where start_time is null
           or end_time is null
           or end_time < start_time
           or duration_minutes <= 0
        """,
    )
    check_query_returns_zero(
        con,
        "missing hourly demand grain check",
        """
        select count(*)
        from marts.rpt_hourly_demand
        where trip_date is null
           or start_hour is null
           or trip_count <= 0
        """,
    )

    print("Warehouse checks passed.")


if __name__ == "__main__":
    main()
