# ============================================================
# Task 1: Telegram Scraper
# Kara Solutions — Medical Telegram Warehouse
# ============================================================

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ── SETUP ────────────────────────────────────────────────────
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# Directories
DATA_LAKE = Path("data/raw/telegram_messages")
IMAGES_DIR = Path("data/raw/images")
LOGS_DIR = Path("logs")

DATA_LAKE.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── LOGGING ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── CHANNELS ─────────────────────────────────────────────────
CHANNELS = [
    "CheMed123",
    "lobelia_cosmetics",
    "tikvahpharma",
    "DoctorsETBot",
]

# ── SCRAPER ──────────────────────────────────────────────────
async def scrape_channel(client, channel_name, limit=200):
    """Scrape messages from a single Telegram channel."""
    logger.info(f"Scraping channel: {channel_name}")
    messages_data = []

    try:
        entity = await client.get_entity(channel_name)
        today = datetime.now().strftime("%Y-%m-%d")

        # Create image directory for this channel
        channel_img_dir = IMAGES_DIR / channel_name
        channel_img_dir.mkdir(parents=True, exist_ok=True)

        async for message in client.iter_messages(entity, limit=limit):
            has_media = False
            image_path = None

            # Download image if message has photo
            if message.media and isinstance(message.media, MessageMediaPhoto):
                has_media = True
                img_filename = channel_img_dir / f"{message.id}.jpg"
                try:
                    await client.download_media(message.media, file=str(img_filename))
                    image_path = str(img_filename)
                    logger.info(f"Downloaded image: {img_filename}")
                except Exception as e:
                    logger.error(f"Failed to download image {message.id}: {e}")

            # Build message record
            msg_data = {
                "message_id": message.id,
                "channel_name": channel_name,
                "message_date": message.date.isoformat() if message.date else None,
                "message_text": message.text or "",
                "has_media": has_media,
                "image_path": image_path,
                "views": message.views or 0,
                "forwards": message.forwards or 0,
            }
            messages_data.append(msg_data)

        # Save to data lake: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
        output_dir = DATA_LAKE / today
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{channel_name}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(messages_data)} messages from {channel_name} to {output_file}")
        return messages_data

    except Exception as e:
        logger.error(f"Error scraping {channel_name}: {e}")
        return []


async def main():
    """Main scraping function."""
    logger.info("Starting Telegram scraper...")

    async with TelegramClient("medical_session", API_ID, API_HASH) as client:
        await client.start(phone=PHONE)
        logger.info("Connected to Telegram!")

        all_data = {}
        for channel in CHANNELS:
            data = await scrape_channel(client, channel, limit=200)
            all_data[channel] = data
            await asyncio.sleep(2)  # Rate limiting

        total = sum(len(v) for v in all_data.values())
        logger.info(f"Scraping complete! Total messages: {total}")


if __name__ == "__main__":
    asyncio.run(main())