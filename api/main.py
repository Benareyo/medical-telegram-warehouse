# ============================================================
# Task 4: FastAPI Analytical API
# Kara Solutions — Medical Telegram Warehouse
# ============================================================

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from api.database import get_db
from api.schemas import TopProduct, ChannelActivity, VisualContentStats, SearchResult

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="Analytical API for Ethiopian medical Telegram channel data",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Medical Telegram Warehouse API", "status": "running"}


@app.get("/api/reports/top-products", response_model=List[TopProduct])
def get_top_products(
    limit: int = Query(default=10, description="Number of top products to return"),
    db: Session = Depends(get_db)
):
    """Returns the most frequently mentioned medical terms across all channels."""
    query = text("""
        SELECT word AS term, COUNT(*) AS frequency
        FROM (
            SELECT regexp_split_to_table(
                lower(message_text), E'\\\\s+'
            ) AS word
            FROM raw.telegram_messages
            WHERE message_text IS NOT NULL AND message_text != ''
        ) words
        WHERE length(word) > 4
        AND word NOT IN ('this','that','with','from','have','been','they',
                         'will','your','what','when','which','about','would')
        GROUP BY word
        ORDER BY frequency DESC
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return [{"term": row[0], "frequency": row[1]} for row in result]


@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivity)
def get_channel_activity(
    channel_name: str,
    db: Session = Depends(get_db)
):
    """Returns posting activity and trends for a specific channel."""
    query = text("""
        SELECT
            channel_name,
            COUNT(*) as total_messages,
            COALESCE(SUM(views), 0) as total_views,
            COALESCE(AVG(views), 0) as avg_views,
            COUNT(CASE WHEN has_media = true THEN 1 END) as messages_with_images
        FROM raw.telegram_messages
        WHERE channel_name = :channel_name
        GROUP BY channel_name
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
    return {
        "channel_name": result[0],
        "total_messages": result[1],
        "total_views": result[2],
        "avg_views": round(float(result[3]), 2),
        "messages_with_images": result[4],
    }


@app.get("/api/search/messages", response_model=List[SearchResult])
def search_messages(
    query: str = Query(..., description="Keyword to search for"),
    limit: int = Query(default=20, description="Max results to return"),
    db: Session = Depends(get_db)
):
    """Search for messages containing a specific keyword."""
    sql = text("""
        SELECT message_id, channel_name, message_date, message_text, views
        FROM raw.telegram_messages
        WHERE lower(message_text) LIKE lower(:query)
        ORDER BY views DESC NULLS LAST
        LIMIT :limit
    """)
    result = db.execute(sql, {"query": f"%{query}%", "limit": limit}).fetchall()
    return [
        {"message_id": r[0], "channel_name": r[1], "message_date": r[2],
         "message_text": r[3], "views": r[4]}
        for r in result
    ]


@app.get("/api/reports/visual-content", response_model=List[VisualContentStats])
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Returns statistics about image usage across all channels."""
    query = text("""
        SELECT
            channel_name,
            COUNT(*) as total_messages,
            COUNT(CASE WHEN has_media = true THEN 1 END) as messages_with_images,
            ROUND(
                COUNT(CASE WHEN has_media = true THEN 1 END) * 100.0 / COUNT(*), 2
            ) as image_percentage
        FROM raw.telegram_messages
        GROUP BY channel_name
        ORDER BY image_percentage DESC
    """)
    result = db.execute(query).fetchall()
    return [
        {"channel_name": r[0], "total_messages": r[1],
         "messages_with_images": r[2], "image_percentage": float(r[3])}
        for r in result
    ]


@app.get("/api/channels")
def list_channels(db: Session = Depends(get_db)):
    """List all available channels."""
    query = text("SELECT DISTINCT channel_name FROM raw.telegram_messages ORDER BY channel_name")
    result = db.execute(query).fetchall()
    return {"channels": [r[0] for r in result]}