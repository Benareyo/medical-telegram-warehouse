# ============================================================
# Task 2: Load Raw Data to PostgreSQL
# Kara Solutions — Medical Telegram Warehouse
# ============================================================

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── DB CONNECTION ────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "medical_warehouse"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )


def create_raw_table(conn):
    """Create raw schema and table if not exists."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                message_id      BIGINT,
                channel_name    VARCHAR(255),
                message_date    TIMESTAMP,
                message_text    TEXT,
                has_media       BOOLEAN,
                image_path      TEXT,
                views           INTEGER,
                forwards        INTEGER,
                scraped_at      TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
    logger.info("Raw table created/verified.")


def load_json_files(conn):
    """Read all JSON files from data lake and load into PostgreSQL."""
    data_lake = Path("data/raw/telegram_messages")
    total_loaded = 0

    for date_dir in sorted(data_lake.iterdir()):
        if not date_dir.is_dir():
            continue
        for json_file in date_dir.glob("*.json"):
            logger.info(f"Loading: {json_file}")
            with open(json_file, "r", encoding="utf-8") as f:
                messages = json.load(f)

            rows = []
            for msg in messages:
                rows.append((
                    msg.get("message_id"),
                    msg.get("channel_name"),
                    msg.get("message_date"),
                    msg.get("message_text", ""),
                    msg.get("has_media", False),
                    msg.get("image_path"),
                    msg.get("views", 0),
                    msg.get("forwards", 0),
                ))

            if rows:
                with conn.cursor() as cur:
                    execute_values(cur, """
                        INSERT INTO raw.telegram_messages
                        (message_id, channel_name, message_date, message_text,
                         has_media, image_path, views, forwards)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                    """, rows)
                conn.commit()
                total_loaded += len(rows)
                logger.info(f"Loaded {len(rows)} rows from {json_file.name}")

    logger.info(f"Total rows loaded: {total_loaded}")


if __name__ == "__main__":
    conn = get_connection()
    create_raw_table(conn)
    load_json_files(conn)
    conn.close()
    logger.info("Done!")