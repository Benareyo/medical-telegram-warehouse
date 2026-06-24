# ============================================================
# Task 5: Dagster Pipeline Orchestration
# Kara Solutions — Medical Telegram Warehouse
# ============================================================

from dagster import op, job, ScheduleDefinition, DefaultScheduleStatus
import subprocess
import os

BASE_DIR = r'C:\Users\HP\Desktop\my files\medical-telegram-warehouse'


@op
def scrape_telegram_data(context):
    """Op 1: Run Telegram scraper."""
    context.log.info("Starting Telegram scraping...")
    result = subprocess.run(
        ["venv/Scripts/python.exe", "src/scraper.py"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Scraper failed: {result.stderr}")
    context.log.info("Scraping complete!")


@op
def load_raw_to_postgres(context, scrape_result):
    """Op 2: Load JSON files to PostgreSQL."""
    context.log.info("Loading raw data to PostgreSQL...")
    result = subprocess.run(
        ["venv/Scripts/python.exe", "src/load_to_postgres.py"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Load failed: {result.stderr}")
    context.log.info("Data loaded to PostgreSQL!")


@op
def run_dbt_transformations(context, load_result):
    """Op 3: Run dbt models."""
    context.log.info("Running dbt transformations...")
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "medical_warehouse"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.warning(f"dbt warning: {result.stderr}")
    context.log.info("dbt transformations complete!")


@op
def run_yolo_enrichment(context, dbt_result):
    """Op 4: Run YOLO object detection."""
    context.log.info("Running YOLO enrichment...")
    result = subprocess.run(
        ["venv/Scripts/python.exe", "src/yolo_detect.py"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"YOLO failed: {result.stderr}")
    context.log.info("YOLO enrichment complete!")


@job
def medical_pipeline():
    """Full ELT pipeline for medical Telegram data."""
    scrape = scrape_telegram_data()
    load = load_raw_to_postgres(scrape)
    dbt = run_dbt_transformations(load)
    run_yolo_enrichment(dbt)


# Daily schedule at 6 AM UTC
daily_schedule = ScheduleDefinition(
    job=medical_pipeline,
    cron_schedule="0 6 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)