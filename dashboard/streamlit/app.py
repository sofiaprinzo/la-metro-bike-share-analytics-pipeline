#!/usr/bin/env python
# coding: utf-8

import json
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


LOCAL_DATABASE_PATH = Path("data/warehouse/bikeshare.duckdb")
DEPLOY_DATABASE_PATH = Path("dashboard/streamlit/data/bikeshare_dashboard.duckdb")
DATABASE_PATH = (
    DEPLOY_DATABASE_PATH if DEPLOY_DATABASE_PATH.exists() else LOCAL_DATABASE_PATH
)

LOCAL_MANIFEST_PATH = Path("data/manifest/trip_ingestion_manifest.json")
DEPLOY_MANIFEST_PATH = Path("dashboard/streamlit/data/trip_ingestion_manifest.json")
MANIFEST_PATH = DEPLOY_MANIFEST_PATH if DEPLOY_MANIFEST_PATH.exists() else LOCAL_MANIFEST_PATH
REGION_COLORS = {
    "DTLA": "#0057B8",
    "Westside": "#E4572E",
    "North Hollywood": "#2CA02C",
    "Pasadena": "#8E44AD",
    "Port of LA": "#D81B60",
}


st.set_page_config(
    page_title="LA Metro Bike Share Analytics",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def run_query(sql):
    con = duckdb.connect(str(DATABASE_PATH), read_only=True)
    try:
        return con.sql(sql).df()
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def read_manifest():
    if not MANIFEST_PATH.exists():
        return None

    with MANIFEST_PATH.open() as manifest_file:
        return json.load(manifest_file)


def require_warehouse():
    if DATABASE_PATH.exists():
        return

    st.error(
        "DuckDB warehouse not found. Run the batch pipeline before opening the dashboard."
    )
    st.code("docker compose run --rm pipeline ./scripts/run_pipeline.sh", language="bash")
    st.stop()


def format_number(value):
    return f"{int(value):,}"


def format_date(value):
    return pd.to_datetime(value).strftime("%b %-d, %Y")


def get_quarters():
    return run_query(
        """
        select
            source_year,
            source_quarter,
            source_year || ' Q' || source_quarter as quarter_label
        from staging.trips
        group by source_year, source_quarter, quarter_label
        order by source_year, source_quarter
        """
    )


def get_quarter_filter(selected_quarter, table_alias=None):
    if selected_quarter == "All Quarters":
        return ""

    year, quarter = selected_quarter.replace(" Q", " ").split()
    prefix = f"{table_alias}." if table_alias else ""

    return (
        f"where {prefix}source_year = {int(year)} "
        f"and {prefix}source_quarter = {int(quarter)}"
    )


def build_where_clause(filters):
    active_filters = [filter_text for filter_text in filters if filter_text]

    if not active_filters:
        return ""

    return "where " + " and ".join(active_filters)


def sql_string(value):
    return str(value).replace("'", "''")


def get_overview_metrics(selected_quarter):
    quarter_filter = get_quarter_filter(selected_quarter)

    return run_query(
        f"""
        select
            count(*) as total_trips,
            min(trip_date) as first_trip_date,
            max(trip_date) as last_trip_date,
            count(distinct start_station_id) as start_station_count,
            count(distinct bike_id) as distinct_bikes,
            round(avg(duration_minutes), 2) as avg_duration_minutes
        from staging.trips
        {quarter_filter}
        """
    ).iloc[0]


def get_table_counts():
    return run_query(
        """
        select *
        from (
            select 'staging.trips' as table_name, count(*) as row_count from staging.trips
            union all
            select 'marts.rpt_hourly_demand', count(*) from marts.rpt_hourly_demand
            union all
            select 'marts.rpt_station_activity', count(*) from marts.rpt_station_activity
            union all
            select 'marts.rpt_route_popularity', count(*) from marts.rpt_route_popularity
        )
        order by table_name
        """
    )


@st.cache_data(show_spinner=False)
def get_route_categories():
    return run_query(
        """
        select coalesce(trip_route_category, 'Unknown') as route_category
        from staging.trips
        group by trip_route_category
        order by route_category
        """
    )["route_category"].tolist()


@st.cache_data(show_spinner=False)
def get_historical_demand_filters():
    options = run_query(
        """
        select
            'region' as filter_name,
            coalesce(s.region, 'Unknown Region') as filter_value
        from staging.trips t
        left join marts.dim_stations s
            on t.start_station_id = s.station_id
        where coalesce(s.region, 'Unknown Region') not in ('Free Bikes', 'Unknown Region')
        group by s.region
        union all
        select
            'passholder_type',
            coalesce(passholder_type, 'Unknown')
        from staging.trips
        where coalesce(passholder_type, 'Unknown') not in ('Testing', 'Unknown')
        group by passholder_type
        union all
        select
            'bike_type',
            coalesce(bike_type, 'Unknown')
        from staging.trips
        group by bike_type
        order by filter_name, filter_value
        """
    )

    return {
        "regions": options[options["filter_name"] == "region"][
            "filter_value"
        ].tolist(),
        "passholder_types": options[options["filter_name"] == "passholder_type"][
            "filter_value"
        ].tolist(),
        "bike_types": options[options["filter_name"] == "bike_type"][
            "filter_value"
        ].tolist(),
    }


def show_overview(selected_quarter):
    metrics = get_overview_metrics(selected_quarter)
    manifest = read_manifest()

    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trips", format_number(metrics["total_trips"]))
    col2.metric("Start Stations", format_number(metrics["start_station_count"]))
    col3.metric("Distinct Bikes", format_number(metrics["distinct_bikes"]))
    col4.metric("Avg Duration", f"{metrics['avg_duration_minutes']:.2f} min")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("First Trip", format_date(metrics["first_trip_date"]))
    col2.metric("Latest Trip", format_date(metrics["last_trip_date"]))

    if manifest:
        files = manifest.get("files", [])
        latest_file = max(
            files,
            key=lambda item: (item["source_year"], item["source_quarter"]),
        )
        col3.metric(
            "Latest Quarter",
            f"{latest_file['source_year']} Q{latest_file['source_quarter']}",
        )
        col4.metric("Files Processed", format_number(len(files)))
        st.caption(f"Manifest updated at {manifest.get('updated_at', 'unknown')}")
    else:
        col3.metric("Latest Quarter", "Unknown")
        col4.metric("Files Processed", "Unknown")

    if selected_quarter == "All Quarters":
        demand_by_quarter = run_query(
            """
            select
                source_year,
                source_quarter,
                source_year || ' Q' || source_quarter as quarter_label,
                count(*) as trip_count
            from staging.trips
            group by source_year, source_quarter, quarter_label
            order by source_year, source_quarter
            """
        )

        fig = px.bar(
            demand_by_quarter,
            x="quarter_label",
            y="trip_count",
            labels={"quarter_label": "Quarter", "trip_count": "Trips"},
        )
        fig.update_layout(height=420, xaxis_tickangle=-45)
    else:
        quarter_filter = get_quarter_filter(selected_quarter)
        daily = run_query(
            f"""
            select
                trip_date,
                count(*) as trip_count
            from staging.trips
            {quarter_filter}
            group by trip_date
            order by trip_date
            """
        )

        fig = px.line(
            daily,
            x="trip_date",
            y="trip_count",
            labels={"trip_date": "Date", "trip_count": "Trips"},
        )
        fig.update_layout(height=420)

    st.plotly_chart(fig, width="stretch", key=f"overview_trips_{selected_quarter}")


def show_historical_demand(selected_quarter):
    filter_options = get_historical_demand_filters()
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    selected_region = filter_col1.selectbox(
        "Region",
        ["All Regions"] + filter_options["regions"],
        key=f"demand_region_{selected_quarter}",
    )
    selected_passholder_type = filter_col2.selectbox(
        "Passholder Type",
        ["All Passholder Types"] + filter_options["passholder_types"],
        key=f"demand_passholder_{selected_quarter}",
    )
    selected_bike_type = filter_col3.selectbox(
        "Bike Type",
        ["All Bike Types"] + filter_options["bike_types"],
        key=f"demand_bike_type_{selected_quarter}",
    )

    filter_col1, filter_col2 = st.columns([1, 2])
    selected_day_type = filter_col1.selectbox(
        "Weekday / Weekend",
        ["All Days", "Weekday", "Weekend"],
        key=f"demand_day_type_{selected_quarter}",
    )
    start_hour, end_hour = filter_col2.slider(
        "Hour Range",
        min_value=0,
        max_value=23,
        value=(0, 23),
        key=f"demand_hour_range_{selected_quarter}",
    )

    conditions = []

    if selected_quarter != "All Quarters":
        year, quarter = selected_quarter.replace(" Q", " ").split()
        conditions.append(
            f"t.source_year = {int(year)} and t.source_quarter = {int(quarter)}"
        )

    if selected_region != "All Regions":
        conditions.append(
            "coalesce(s.region, 'Unknown Region') = "
            f"'{sql_string(selected_region)}'"
        )

    if selected_passholder_type != "All Passholder Types":
        conditions.append(
            "coalesce(t.passholder_type, 'Unknown') = "
            f"'{sql_string(selected_passholder_type)}'"
        )

    if selected_bike_type != "All Bike Types":
        conditions.append(
            "coalesce(t.bike_type, 'Unknown') = "
            f"'{sql_string(selected_bike_type)}'"
        )

    if selected_day_type == "Weekday":
        conditions.append("t.day_of_week between 1 and 5")
    elif selected_day_type == "Weekend":
        conditions.append("t.day_of_week in (0, 6)")

    conditions.append(f"t.start_hour between {start_hour} and {end_hour}")
    where_clause = build_where_clause(conditions)

    hourly = run_query(
        f"""
        select
            t.source_year,
            t.source_quarter,
            t.source_year || ' Q' || t.source_quarter as quarter_label,
            t.trip_date,
            t.start_hour,
            case
                when t.start_hour = 0 then '12 AM'
                when t.start_hour < 12 then cast(t.start_hour as varchar) || ' AM'
                when t.start_hour = 12 then '12 PM'
                else cast(t.start_hour - 12 as varchar) || ' PM'
            end as start_hour_label,
            case
                when t.day_of_week in (0, 6) then 'Weekend'
                else 'Weekday'
            end as day_type,
            count(*) as trip_count,
            count(distinct t.start_station_id) as active_station_count,
            count(distinct t.bike_id) as distinct_bikes_used,
            round(avg(t.duration_minutes), 2) as avg_duration_minutes
        from staging.trips t
        left join marts.dim_stations s
            on t.start_station_id = s.station_id
        {where_clause}
        group by
            t.source_year,
            t.source_quarter,
            quarter_label,
            t.trip_date,
            t.start_hour,
            start_hour_label,
            day_type
        order by t.trip_date, t.start_hour
        """
    )

    if hourly.empty:
        st.info("No trips match these demand filters.")
        return

    hourly["trip_date"] = pd.to_datetime(hourly["trip_date"])
    daily = (
        hourly.groupby("trip_date", as_index=False)
        .agg(
            trip_count=("trip_count", "sum"),
            active_station_count=("active_station_count", "max"),
            distinct_bikes_used=("distinct_bikes_used", "sum"),
        )
    )
    by_hour = (
        hourly.groupby(["start_hour", "start_hour_label"], as_index=False)
        .agg(
            trip_count=("trip_count", "sum"),
            avg_duration_minutes=("avg_duration_minutes", "mean"),
        )
        .sort_values("start_hour")
    )
    by_day_type = (
        hourly.groupby("day_type", as_index=False)
        .agg(
            trip_count=("trip_count", "sum"),
            avg_duration_minutes=("avg_duration_minutes", "mean"),
        )
        .sort_values("day_type")
    )

    fig = px.line(
        daily,
        x="trip_date",
        y="trip_count",
        labels={"trip_date": "Date", "trip_count": "Trips"},
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, width="stretch", key=f"daily_demand_{selected_quarter}")

    if selected_quarter == "All Quarters":
        by_quarter = (
            hourly.groupby(
                ["source_year", "source_quarter", "quarter_label"],
                as_index=False,
            )
            .agg(trip_count=("trip_count", "sum"))
            .sort_values(["source_year", "source_quarter"])
        )
        quarter_fig = px.bar(
            by_quarter,
            x="quarter_label",
            y="trip_count",
            labels={"quarter_label": "Quarter", "trip_count": "Trips"},
        )
        quarter_fig.update_layout(height=360, xaxis_tickangle=-45)
        st.plotly_chart(
            quarter_fig,
            width="stretch",
            key=f"quarterly_demand_{selected_region}_{selected_passholder_type}_{selected_bike_type}",
        )

    col1, col2 = st.columns(2)

    hour_fig = px.bar(
        by_hour,
        x="start_hour_label",
        y="trip_count",
        labels={"start_hour_label": "Start Hour", "trip_count": "Trips"},
    )
    hour_fig.update_layout(height=380)
    col1.plotly_chart(hour_fig, width="stretch", key=f"hourly_demand_{selected_quarter}")

    duration_fig = px.line(
        by_hour,
        x="start_hour_label",
        y="avg_duration_minutes",
        labels={
            "start_hour_label": "Start Hour",
            "avg_duration_minutes": "Avg Duration",
        },
    )
    duration_fig.update_layout(height=380)
    col2.plotly_chart(
        duration_fig,
        width="stretch",
        key=f"hourly_duration_{selected_quarter}",
    )

    day_type_fig = px.bar(
        by_day_type,
        x="day_type",
        y="trip_count",
        color="day_type",
        labels={"day_type": "Day Type", "trip_count": "Trips"},
    )
    day_type_fig.update_layout(height=320, showlegend=False)
    st.plotly_chart(
        day_type_fig,
        width="stretch",
        key=f"weekday_weekend_demand_{selected_quarter}",
    )


def show_station_activity(selected_quarter):
    quarter_condition = ""

    if selected_quarter != "All Quarters":
        year, quarter = selected_quarter.replace(" Q", " ").split()
        quarter_condition = (
            f"t.source_year = {int(year)} and t.source_quarter = {int(quarter)}"
        )

    base_where_clause = build_where_clause([quarter_condition])
    stations = run_query(
        f"""
        select
            t.start_station_id as station_id,
            coalesce(s.station_name, 'Unknown Station') as station_name,
            coalesce(s.region, 'Unknown Region') as region,
            coalesce(s.status, 'Unknown Status') as station_status,
            coalesce(s.latitude, round(avg(t.start_lat), 6)) as station_lat,
            coalesce(s.longitude, round(avg(t.start_lon), 6)) as station_lon,
            count(*) as trip_starts,
            count(distinct t.bike_id) as distinct_bikes_used,
            round(avg(t.duration_minutes), 2) as avg_duration_minutes
        from staging.trips t
        left join marts.dim_stations s
            on t.start_station_id = s.station_id
        {base_where_clause}
        group by
            t.start_station_id,
            s.station_name,
            s.region,
            s.status,
            s.latitude,
            s.longitude
        order by trip_starts desc
        """
    )

    regions = sorted(
        region
        for region in stations["region"].dropna().unique()
        if region not in ["Free Bikes", "Unknown Region"]
    )

    filter_col1, filter_col2, filter_col3 = st.columns([1, 2, 1])
    selected_region = filter_col1.selectbox(
        "Region",
        ["All Regions"] + regions,
        key=f"station_region_{selected_quarter}",
    )

    filtered_stations = stations.copy()

    if selected_region != "All Regions":
        filtered_stations = filtered_stations[
            filtered_stations["region"] == selected_region
        ]

    station_options = (
        filtered_stations[["station_id", "station_name"]]
        .drop_duplicates()
        .sort_values("station_name")
    )
    station_labels = ["All Stations"] + [
        f"{row.station_name} ({row.station_id})"
        for row in station_options.itertuples(index=False)
    ]
    selected_station_label = filter_col2.selectbox(
        "Station",
        station_labels,
        key=f"station_select_{selected_quarter}_{selected_region}",
    )
    top_n = filter_col3.slider(
        "Top stations",
        min_value=10,
        max_value=50,
        value=20,
        step=5,
        key=f"station_top_n_{selected_quarter}_{selected_region}",
    )

    selected_station_id = None

    if selected_station_label != "All Stations":
        selected_station_id = selected_station_label.rsplit("(", 1)[-1].replace(")", "")

    if selected_station_id:
        selected_station = filtered_stations[
            filtered_stations["station_id"] == selected_station_id
        ].iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Trip Starts", format_number(selected_station["trip_starts"]))
        col2.metric("Region", selected_station["region"])
        col3.metric("Distinct Bikes", format_number(selected_station["distinct_bikes_used"]))
        col4.metric("Avg Duration", f"{selected_station['avg_duration_minutes']:.2f} min")

        include_special_destinations = st.checkbox(
            "Include virtual / unknown destinations",
            value=False,
            help=(
                "Includes Virtual Station and Unknown Region trips. A Virtual Station is "
                "not a regular bike dock. Metro may use it when staff need to check bikes "
                "in or out during events like CicLAvia, overflow, maintenance, or bike "
                "rebalancing. Unknown Region means the trip could not be matched to one "
                "of Metro's normal service areas. This can happen if a bike is taken "
                "outside the usual service area."
            ),
            key=(
                f"include_special_destinations_"
                f"{selected_quarter}_{selected_station_id}"
            ),
        )

        station_conditions = [
            quarter_condition,
            f"t.start_station_id = '{sql_string(selected_station_id)}'",
        ]
        station_where_clause = build_where_clause(station_conditions)

        daily = run_query(
            f"""
            select
                t.trip_date,
                count(*) as trip_starts
            from staging.trips t
            {station_where_clause}
            group by t.trip_date
            order by t.trip_date
            """
        )
        hourly = run_query(
            f"""
            select
                t.start_hour,
                case
                    when t.start_hour = 0 then '12 AM'
                    when t.start_hour < 12 then cast(t.start_hour as varchar) || ' AM'
                    when t.start_hour = 12 then '12 PM'
                    else cast(t.start_hour - 12 as varchar) || ' PM'
                end as start_hour_label,
                count(*) as trip_starts
            from staging.trips t
            {station_where_clause}
            group by t.start_hour, start_hour_label
            order by t.start_hour
            """
        )
        destination_conditions = station_conditions + ["t.end_station_id is not null"]

        if not include_special_destinations:
            destination_conditions.extend(
                [
                    "coalesce(end_station.station_name, 'Unknown End Station') != 'Virtual Station'",
                    "coalesce(end_station.region, 'Unknown Region') != 'Unknown Region'",
                    "end_station.latitude is not null",
                    "end_station.longitude is not null",
                    "end_station.latitude != 0",
                    "end_station.longitude != 0",
                ]
            )

        destination_where_clause = build_where_clause(destination_conditions)
        destinations = run_query(
            f"""
            select
                coalesce(start_station.station_name, 'Unknown Start Station') as start_station_name,
                coalesce(start_station.region, 'Unknown Region') as start_region,
                coalesce(end_station.station_name, 'Unknown End Station') as end_station_name,
                coalesce(end_station.region, 'Unknown Region') as end_region,
                count(*) as trip_count,
                round(avg(t.duration_minutes), 2) as avg_duration_minutes
            from staging.trips t
            left join marts.dim_stations start_station
                on t.start_station_id = start_station.station_id
            left join marts.dim_stations end_station
                on t.end_station_id = end_station.station_id
            {destination_where_clause}
            group by
                t.start_station_id,
                start_station.station_name,
                start_station.region,
                t.end_station_id,
                end_station.station_name,
                end_station.region
            order by trip_count desc
            limit 15
            """
        )

        daily_fig = px.line(
            daily,
            x="trip_date",
            y="trip_starts",
            labels={"trip_date": "Date", "trip_starts": "Trip Starts"},
        )
        daily_fig.update_layout(height=360)
        st.plotly_chart(
            daily_fig,
            width="stretch",
            key=f"station_daily_{selected_quarter}_{selected_station_id}",
        )

        col1, col2 = st.columns(2)
        hourly_fig = px.bar(
            hourly,
            x="start_hour_label",
            y="trip_starts",
            labels={"start_hour_label": "Start Hour", "trip_starts": "Trip Starts"},
        )
        hourly_fig.update_layout(height=360)
        col1.plotly_chart(
            hourly_fig,
            width="stretch",
            key=f"station_hourly_{selected_quarter}_{selected_station_id}",
        )

        if destinations.empty:
            col2.info("No physical destination station trips found for this filter.")
        else:
            destination_fig = px.bar(
                destinations.sort_values("trip_count"),
                x="trip_count",
                y="end_station_name",
                orientation="h",
                color="end_region",
                color_discrete_map=REGION_COLORS,
                labels={"trip_count": "Trips", "end_station_name": "Destination"},
            )
            destination_fig.update_layout(
                height=360,
                yaxis_title="",
                title=f"Top destinations from {selected_station['station_name']}",
            )
            col2.plotly_chart(
                destination_fig,
                width="stretch",
                key=(
                    f"station_destinations_{selected_quarter}_"
                    f"{selected_station_id}_{include_special_destinations}"
                ),
            )

        if not include_special_destinations:
            st.caption(
                "Virtual Station and Unknown Region destinations are hidden here by "
                "default because they represent operational, non-physical, or unmapped "
                "endpoints rather than normal station-to-station demand."
            )
        st.dataframe(destinations, width="stretch", hide_index=True)
        return

    top_stations = (
        filtered_stations.sort_values("trip_starts", ascending=False)
        .head(top_n)
        .copy()
    )
    top_stations["station_label"] = top_stations["station_name"]
    top_stations = top_stations.sort_values("trip_starts", ascending=True)
    station_order = top_stations["station_label"].tolist()

    fig = px.bar(
        top_stations,
        x="trip_starts",
        y="station_label",
        orientation="h",
        color="region",
        color_discrete_map=REGION_COLORS,
        labels={"trip_starts": "Trip Starts", "station_label": "Station"},
    )
    fig.update_layout(height=620, yaxis_title="")
    fig.update_yaxes(categoryorder="array", categoryarray=station_order)
    st.plotly_chart(
        fig,
        width="stretch",
        key=f"station_rankings_{selected_quarter}_{selected_region}",
    )
    visible_regions = ", ".join(sorted(top_stations["region"].dropna().unique()))
    st.caption(
        f"The bar chart ranks the top {top_n} stations by trip starts. "
        f"The region legend only includes regions visible in those top stations"
        f"{': ' + visible_regions if visible_regions else '.'}"
    )

    map_df = filtered_stations[
        (filtered_stations["region"].notna())
        & (~filtered_stations["region"].isin(["Free Bikes", "Unknown Region"]))
        & (filtered_stations["station_lat"].notna())
        & (filtered_stations["station_lon"].notna())
        & (filtered_stations["station_lat"] != 0)
        & (filtered_stations["station_lon"] != 0)
    ].copy()
    map_df["marker_size"] = map_df["trip_starts"].pow(0.5).clip(lower=6)
    st.caption(
        "Map excludes non-physical station records and stations without valid coordinates. "
        "Only regions with trip starts in the selected quarter appear in the legend."
    )
    map_fig = px.scatter_map(
        map_df,
        lat="station_lat",
        lon="station_lon",
        size="marker_size",
        color="region",
        color_discrete_map=REGION_COLORS,
        hover_name="station_name",
        hover_data={
            "trip_starts": True,
            "marker_size": False,
            "station_lat": False,
            "station_lon": False,
        },
        zoom=9,
        height=520,
    )
    map_fig.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(
        map_fig,
        width="stretch",
        key=f"station_map_{selected_quarter}_{selected_region}",
    )
    st.dataframe(filtered_stations, width="stretch", hide_index=True)


def show_routes(selected_quarter):
    quarter_filter = get_quarter_filter(selected_quarter, "t")
    route_category = st.selectbox(
        "One-way vs round-trip",
        ["All Trips"] + get_route_categories(),
        key=f"route_category_{selected_quarter}",
    )
    route_category_filter = ""

    if route_category != "All Trips":
        route_category_filter = (
            "and coalesce(t.trip_route_category, 'Unknown') = "
            f"'{sql_string(route_category)}'"
        )

    routes = run_query(
        f"""
        select
            coalesce(start_station.station_name, 'Unknown Start Station') as start_station_name,
            coalesce(start_station.region, 'Unknown Region') as start_region,
            coalesce(end_station.station_name, 'Unknown End Station') as end_station_name,
            coalesce(end_station.region, 'Unknown Region') as end_region,
            count(*) as trip_count,
            count(distinct t.bike_id) as distinct_bikes_used,
            round(avg(t.duration_minutes), 2) as avg_duration_minutes
        from staging.trips t
        left join marts.dim_stations start_station
            on t.start_station_id = start_station.station_id
        left join marts.dim_stations end_station
            on t.end_station_id = end_station.station_id
        {quarter_filter}
          {"and" if quarter_filter else "where"} t.start_station_id is not null
          and t.end_station_id is not null
          {route_category_filter}
        group by
            t.start_station_id,
            start_station.station_name,
            start_station.region,
            t.end_station_id,
            end_station.station_name,
            end_station.region
        order by trip_count desc
        limit 500
        """
    )

    top_n = st.slider("Top routes", min_value=10, max_value=50, value=20, step=5)
    top_routes = routes.head(top_n).copy()
    top_routes["route"] = (
        top_routes["start_station_name"] + " to " + top_routes["end_station_name"]
    )

    fig = px.bar(
        top_routes.sort_values("trip_count"),
        x="trip_count",
        y="route",
        orientation="h",
        labels={"trip_count": "Trips", "route": "Route"},
    )
    fig.update_layout(height=640, yaxis_title="")
    st.plotly_chart(fig, width="stretch", key=f"route_rankings_{selected_quarter}")
    st.dataframe(routes, width="stretch", hide_index=True)


def show_data_health(selected_quarter):
    table_counts = get_table_counts()
    st.dataframe(table_counts, width="stretch", hide_index=True)

    manifest = read_manifest()

    if not manifest:
        st.warning("No ingestion manifest found.")
        return

    files = pd.DataFrame(manifest.get("files", []))

    if selected_quarter != "All Quarters":
        year, quarter = selected_quarter.replace(" Q", " ").split()
        files = files[
            (files["source_year"] == int(year))
            & (files["source_quarter"] == int(quarter))
        ]

    st.caption(f"Manifest updated at {manifest.get('updated_at', 'unknown')}")
    st.dataframe(files, width="stretch", hide_index=True)


require_warehouse()

st.title("LA Metro Bike Share Analytics")
st.caption("Batch analytics from Metro Bike Share quarterly trip data")
st.info(
    "This dashboard reflects the latest quarterly trip data loaded by the batch "
    "pipeline. When Metro releases a new quarter, the scheduled pipeline can ingest "
    "it and refresh these views."
)

quarters = get_quarters()
quarter_options = ["All Quarters"] + quarters["quarter_label"].tolist()
selected_quarter = st.selectbox("Quarter", quarter_options, index=0)

overview_tab, demand_tab, station_tab, route_tab, health_tab = st.tabs(
    [
        "Overview",
        "Historical Demand",
        "Station Activity",
        "Routes",
        "Data Health",
    ]
)

with overview_tab:
    show_overview(selected_quarter)

with demand_tab:
    show_historical_demand(selected_quarter)

with station_tab:
    show_station_activity(selected_quarter)

with route_tab:
    show_routes(selected_quarter)

with health_tab:
    show_data_health(selected_quarter)
