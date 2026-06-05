-- Session stitching: resolve the ordered touchpoint sequence per user and
-- attach the converting event, applying the rolling attribution window.

with events as (

    select * from {{ ref('stg_ga4_events') }}

),

-- Identify each user's first conversion timestamp.
conversions as (

    select
        user_id,
        min(event_timestamp) as conversion_ts,
        max(event_value)     as revenue
    from events
    where is_conversion = 1
    group by user_id

),

-- Keep only touchpoints within the N-day window before the conversion
-- (or all touchpoints for non-converting users).
windowed as (

    select
        e.user_id,
        e.event_timestamp,
        e.step,
        e.channel,
        c.conversion_ts,
        coalesce(c.revenue, 0) as revenue,
        case when c.user_id is not null then 1 else 0 end as converted
    from events e
    left join conversions c
        on e.user_id = c.user_id
    where c.conversion_ts is null
       or e.event_timestamp <= c.conversion_ts
      and timestamp_diff(
              c.conversion_ts, e.event_timestamp, day
          ) <= {{ var('attribution_window_days') }}

)

select * from windowed
