-- Staging: clean & normalise the raw GA4 BigQuery export.
-- One row per touchpoint event, de-duplicated, with channel mapped from the
-- GA4 traffic-source dimensions.

with source as (

    select * from {{ source('ga4', 'ga4_events') }}

),

cleaned as (

    select
        user_id,
        event_timestamp,
        step,
        -- Normalise channel grouping (default-channel-grouping logic).
        case
            when lower(channel) like '%paid search%' then 'Paid Search'
            when lower(channel) like '%organic%'     then 'Organic Search'
            when lower(channel) like '%display%'      then 'Display'
            when lower(channel) like '%social%'       then 'Paid Social'
            when lower(channel) like '%email%'        then 'Email'
            when lower(channel) like '%video%'        then 'Video'
            when lower(channel) like '%referr%'       then 'Referral'
            else coalesce(channel, 'Direct')
        end as channel,
        is_conversion,
        event_value
    from source
    where user_id is not null

),

deduped as (

    -- Remove duplicate events emitted by GTM double-fires.
    select *,
        row_number() over (
            partition by user_id, event_timestamp, channel
            order by step
        ) as rn
    from cleaned

)

select
    user_id,
    event_timestamp,
    step,
    channel,
    is_conversion,
    event_value
from deduped
where rn = 1
