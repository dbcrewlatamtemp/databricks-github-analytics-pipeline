
{{ config(
    materialized='incremental',
    unique_key='user_id',
    incremental_strategy='merge'
) }}

with fuente as (
    select
        cast(user_id as string)         as user_id,
        lower(trim(user_name))          as user_name,
        cast(event_ts as timestamp)     as event_ts
    from {{ source('bronze', 'events_raw') }}
), dedup as (
    select *
    from (
      select
        *,
        row_number() over (partition by user_id order by event_ts desc) as rn
      from fuente
    ) x
    where rn = 1
)

select user_id, user_name, event_ts
from dedup

{% if is_incremental() %}
  where event_ts > coalesce((select max(event_ts) from {{ this }}), '1900-01-01')
{% endif %}
