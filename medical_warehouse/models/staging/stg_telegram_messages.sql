WITH source AS (
    SELECT * FROM raw.telegram_messages
),
cleaned AS (
    SELECT
        message_id,
        channel_name,
        CAST(message_date AS TIMESTAMP) AS message_date,
        TRIM(message_text) AS message_text,
        LENGTH(TRIM(COALESCE(message_text,''))) AS message_length,
        has_media AS has_image,
        image_path,
        COALESCE(views, 0) AS views,
        COALESCE(forwards, 0) AS forwards,
        scraped_at
    FROM source
    WHERE message_text IS NOT NULL
      AND TRIM(message_text) != ''
      AND message_date <= NOW()
)
SELECT * FROM cleaned
