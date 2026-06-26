WITH dates AS (
    SELECT DISTINCT
        CAST(message_date AS DATE) AS full_date
    FROM {{ ref('stg_telegram_messages') }}
    WHERE message_date IS NOT NULL
)
SELECT
    TO_CHAR(full_date, 'YYYYMMDD')::INT AS date_key,
    full_date,
    EXTRACT(DOW FROM full_date)::INT AS day_of_week,
    TO_CHAR(full_date, 'Day') AS day_name,
    EXTRACT(WEEK FROM full_date)::INT AS week_of_year,
    EXTRACT(MONTH FROM full_date)::INT AS month,
    TO_CHAR(full_date, 'Month') AS month_name,
    EXTRACT(QUARTER FROM full_date)::INT AS quarter,
    EXTRACT(YEAR FROM full_date)::INT AS year,
    CASE WHEN EXTRACT(DOW FROM full_date) IN (0,6) THEN TRUE ELSE FALSE END AS is_weekend
FROM dates
