# ============================================================
# Task 3: YOLO Object Detection
# Kara Solutions — Medical Telegram Warehouse
# ============================================================

import os
import csv
import logging
from pathlib import Path
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGES_DIR = Path("data/raw/images")
OUTPUT_CSV = Path("data/yolo_detections.csv")

# Objects that indicate a product
PRODUCT_OBJECTS = {"bottle", "cup", "bowl", "box", "vase", "book"}
PERSON_OBJECTS = {"person"}


def classify_image(detected_classes):
    """Classify image based on detected objects."""
    has_person = any(c in PERSON_OBJECTS for c in detected_classes)
    has_product = any(c in PRODUCT_OBJECTS for c in detected_classes)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"


def run_detection():
    """Run YOLO detection on all downloaded images."""
    logger.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")

    results_data = []

    for channel_dir in IMAGES_DIR.iterdir():
        if not channel_dir.is_dir():
            continue
        channel_name = channel_dir.name

        for img_file in channel_dir.glob("*.jpg"):
            message_id = img_file.stem
            logger.info(f"Detecting: {img_file}")

            try:
                results = model(str(img_file), verbose=False)

                for result in results:
                    detected_classes = []
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        confidence = float(box.conf[0])
                        detected_classes.append(class_name)

                        results_data.append({
                            "message_id": message_id,
                            "channel_name": channel_name,
                            "image_path": str(img_file),
                            "detected_class": class_name,
                            "confidence_score": round(confidence, 4),
                            "image_category": classify_image(detected_classes),
                        })

                    if not result.boxes:
                        results_data.append({
                            "message_id": message_id,
                            "channel_name": channel_name,
                            "image_path": str(img_file),
                            "detected_class": "none",
                            "confidence_score": 0.0,
                            "image_category": "other",
                        })

            except Exception as e:
                logger.error(f"Error processing {img_file}: {e}")

    # Save to CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "message_id", "channel_name", "image_path",
            "detected_class", "confidence_score", "image_category"
        ])
        writer.writeheader()
        writer.writerows(results_data)

    logger.info(f"Saved {len(results_data)} detections to {OUTPUT_CSV}")


if __name__ == "__main__":
    run_detection()