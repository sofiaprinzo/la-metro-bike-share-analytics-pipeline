-- Route-level table for identifying the most common station-to-station trip patterns.

create or replace table marts.rpt_route_popularity as
select
    t.source_year,
    t.source_quarter,
    t.start_station_id,
    coalesce(start_station.station_name, 'Unknown Start Station') as start_station_name,
    coalesce(start_station.region, 'Unknown Region') as start_region,

    t.end_station_id,
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
where t.start_station_id is not null
  and t.end_station_id is not null
group by
    t.source_year,
    t.source_quarter,
    t.start_station_id,
    start_station.station_name,
    start_station.region,
    t.end_station_id,
    end_station.station_name,
    end_station.region
order by
    t.source_year,
    t.source_quarter,
    trip_count desc;
