SELECT message_id
FROM {{ ref('stg_telegram_messages') }}
WHERE message_date > NOW()
