-- Path construction: collapse stitched sessions into one row per journey with
-- the ordered channel path. This is the table the Python Shapley & Markov
-- engines consume (mirrors data/journey_generator output schema).

with stitched as (

    select * from {{ ref('int_session_stitched') }}

),

ordered as (

    select
        user_id,
        converted,
        revenue,
        channel,
        step,
        row_number() over (
            partition by user_id order by event_timestamp, step
        ) as touch_order
    from stitched

)

select
    user_id,
    string_agg(channel, ' > ' order by touch_order) as path,
    count(*)                                         as path_length,
    count(distinct channel)                          as n_unique_channels,
    max(converted)                                   as converted,
    max(revenue)                                     as revenue,
    array_agg(channel order by touch_order)[safe_offset(0)]  as first_touch,
    array_agg(channel order by touch_order desc)[safe_offset(0)] as last_touch
from ordered
group by user_id
