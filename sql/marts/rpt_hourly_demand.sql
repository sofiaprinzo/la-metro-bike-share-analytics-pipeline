-- Reporting mart for bike share demand by date and hour.
-- This table supports dashboard analysis of usage patterns over time.

create or replace table marts.rpt_hourly_demand as
select
    trip_date,
    start_hour,
    case
        when start_hour = 0 then '12 AM'
        when start_hour < 12 then cast(start_hour as varchar) || ' AM'
        when start_hour = 12 then '12 PM'
        else cast(start_hour - 12 as varchar) || ' PM'
    end as start_hour_label,
    count(*) as trip_count,
    count(distinct start_station_id) as active_station_count,
    count(distinct bike_id) as distinct_bikes_used,
    round(avg(duration_minutes), 2) as avg_duration_minutes
from staging.trips
group by
    trip_date,
    start_hour,
    start_hour_label
order by
    trip_date,
    start_hour;