WITH channel_stats AS (
    SELECT
        channel_name,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date,
        COUNT(*) AS total_posts,
        AVG(views) AS avg_views,
        CASE
            WHEN channel_name ILIKE '%pharma%' THEN 'Pharmaceutical'
            WHEN channel_name ILIKE '%cosmet%' THEN 'Cosmetics'
            WHEN channel_name ILIKE '%chem%' THEN 'Medical'
            WHEN channel_name ILIKE '%doctor%' THEN 'Medical'
            ELSE 'Medical'
        END AS channel_type
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
)
SELECT
    ROW_NUMBER() OVER (ORDER BY channel_name) AS channel_key,
    channel_name,
    channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    ROUND(CAST(avg_views AS NUMERIC), 2) AS avg_views
FROM channel_stats
