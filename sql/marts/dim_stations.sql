-- Station dimension used to translate trip station IDs into public names and regions.

create or replace table marts.dim_stations as
select
    cast(station_id as varchar) as station_id,
    station_name,
    cast(go_live_date as date) as go_live_date,
    region,
    status,
    latitude,
    longitude
from raw.stations
where station_id is not null
qualify row_number() over (
    partition by station_id
    order by go_live_date desc
) = 1;