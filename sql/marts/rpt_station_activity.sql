-- Counts trip starts by station for rankings, drilldowns, and the map.

create or replace table marts.rpt_station_activity as
select
    t.source_year,
    t.source_quarter,
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
where t.start_station_id is not null
group by
    t.source_year,
    t.source_quarter,
    t.start_station_id,
    s.station_name,
    s.region,
    s.status,
    s.latitude,
    s.longitude
order by
    t.source_year,
    t.source_quarter,
    trip_starts desc;
