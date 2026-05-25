-- Staging model for LA Metro Bike Share trips.
-- This standardizes raw trip records and adds fields used by downstream marts.

create or replace table staging.trips as
select
    cast(trip_id as varchar) as trip_id,
    cast(duration as integer) as duration_minutes,

    cast(start_time as timestamp) as start_time,
    cast(end_time as timestamp) as end_time,
    cast(start_time as date) as trip_date,
    extract(hour from cast(start_time as timestamp)) as start_hour,
    extract(dow from cast(start_time as timestamp)) as day_of_week,

    cast(start_station as varchar) as start_station_id,
    cast(start_lat as double) as start_lat,
    cast(start_lon as double) as start_lon,

    cast(end_station as varchar) as end_station_id,
    cast(end_lat as double) as end_lat,
    cast(end_lon as double) as end_lon,

    cast(bike_id as varchar) as bike_id,
    cast(plan_duration as integer) as plan_duration_days,

    trim(trip_route_category) as trip_route_category,
    trim(passholder_type) as passholder_type,
    trim(bike_type) as bike_type

from raw.trips
where start_time is not null
  and end_time is not null
  and duration > 0
qualify row_number() over (
    partition by trip_id
    order by start_time
) = 1;