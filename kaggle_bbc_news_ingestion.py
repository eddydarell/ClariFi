#!/usr/bin/env python3
"""
Kaggle BBC News Ingestion Script for ClariFi
Ingests news events from a Kaggle-style BBC RSS CSV export (e.g. bbc_sample.csv)
with columns: title, pubDate, guid, link, description
and populates the events table used for event correlation.
"""

import os
import re
import sys
import csv
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from email.utils import parsedate_to_datetime

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from database.models import DatabaseManager

# Very small keyword lists to give a rough sentiment/impact hint for correlation weighting
NEGATIVE_KEYWORDS = [
    "war",
    "attack",
    "crisis",
    "crash",
    "recession",
    "collapse",
    "conflict",
    "sanction",
    "death",
    "killed",
    "shortage",
    "inflation",
    "layoff",
    "strike",
    "lawsuit",
    "fraud",
    "default",
    "plunge",
    "ban",
    "bankrupt",
]
POSITIVE_KEYWORDS = [
    "growth",
    "deal",
    "agreement",
    "record",
    "surge",
    "profit",
    "recovery",
    "breakthrough",
    "rally",
    "win",
    "boost",
    "expansion",
    "approval",
]

REQUIRED_COLUMNS = {"title", "pubDate", "link"}


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def parse_pub_date(pub_date_raw: str) -> Optional[str]:
    """Parse a (possibly messy) RFC 2822 pubDate string into an ISO date (YYYY-MM-DD)."""
    if not pub_date_raw:
        return None
    # The Kaggle export has irregular whitespace, e.g. "Sun      , 06 Mar 2022 ..."
    normalized = re.sub(r"\s+", " ", pub_date_raw).strip()
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    try:
        dt = parsedate_to_datetime(normalized)
        return dt.date().isoformat()
    except (TypeError, ValueError):
        logging.warning(f"Could not parse pubDate '{pub_date_raw}'")
        return None


def derive_category(link: str) -> str:
    """Derive a category from the BBC news URL path, e.g. .../news/world-europe-60638042 -> world-europe."""
    if link:
        match = re.search(r"/news/([a-zA-Z-]+)-\d+", link)
        if match:
            return match.group(1)
    return "general"


def classify_impact(title: str, description: str) -> str:
    """Very small keyword-based heuristic for expected market impact."""
    text = f"{title} {description}".lower()
    if any(word in text for word in NEGATIVE_KEYWORDS):
        return "negative"
    if any(word in text for word in POSITIVE_KEYWORDS):
        return "positive"
    return "neutral"


def import_events_from_csv(
    csv_file_path: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_override: str = None,
    limit: int = None,
) -> int:
    """
    Import news events from a Kaggle BBC CSV file into the database.

    Args:
        csv_file_path: Path to the CSV file (title, pubDate, guid, link, description)
        db_path: Path to the SQLite database file
        skip_duplicates: Whether to skip events that already exist
        category_override: If set, use this category for all rows instead of deriving it
        limit: Optional maximum number of rows to import

    Returns:
        Number of events imported
    """
    logging.info(f"Importing news events from {csv_file_path}...")

    try:
        with open(csv_file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            if not REQUIRED_COLUMNS.issubset(fieldnames):
                logging.error(
                    f"CSV {csv_file_path} is missing required columns {REQUIRED_COLUMNS - fieldnames}"
                )
                return 0
            rows = list(reader)
    except FileNotFoundError:
        logging.error(f"File {csv_file_path} not found")
        return 0
    except csv.Error as e:
        logging.error(f"Error reading CSV {csv_file_path}: {e}")
        return 0

    db_manager = DatabaseManager(db_path)

    existing_events = db_manager.get_all_events() if skip_duplicates else []
    existing_keys = {(e["event_date"], e["event"]) for e in existing_events}

    imported_count = 0
    skipped_count = 0
    duplicate_count = 0

    for row in rows:
        if limit is not None and imported_count >= limit:
            break
        try:
            title = (row.get("title") or "").strip()
            description = (row.get("description") or "").strip()
            link = (row.get("link") or row.get("guid") or "").strip()
            event_date = parse_pub_date(row.get("pubDate", ""))

            if not event_date or not title:
                logging.warning(f"Skipping row with missing date or title: {row}")
                skipped_count += 1
                continue

            if skip_duplicates and (event_date, title) in existing_keys:
                logging.debug(f"Skipping duplicate event: {title} on {event_date}")
                duplicate_count += 1
                continue

            category = category_override or derive_category(link)
            impact = classify_impact(title, description)

            db_manager.insert_event(
                event_date=event_date,
                event=title,
                category=category,
                impact=impact,
                summary=description,
                link=link,
            )

            existing_keys.add((event_date, title))
            imported_count += 1

        except Exception as e:
            logging.error(f"Error importing row {row.get('title', 'Unknown')}: {e}")
            skipped_count += 1
            continue

    logging.info(f"Imported {imported_count} news events successfully")
    if skipped_count > 0:
        logging.warning(f"Skipped {skipped_count} rows due to errors")
    if duplicate_count > 0:
        logging.info(f"Skipped {duplicate_count} duplicate events")

    return imported_count


def process_ingest_folder(
    ingest_dir: str,
    ingested_dir: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_override: str = None,
) -> int:
    """Process all CSV files in the ingest folder and move them to ingested folder after processing."""
    ingest_path = Path(ingest_dir)
    ingested_path = Path(ingested_dir)

    ingested_path.mkdir(exist_ok=True)

    csv_files = list(ingest_path.glob("*.csv"))

    if not csv_files:
        logging.info(f"No CSV files found in {ingest_dir}")
        return 0

    logging.info(f"Found {len(csv_files)} CSV files to process")

    total_imported = 0

    for csv_file in csv_files:
        logging.info(f"Processing {csv_file.name}...")

        imported_count = import_events_from_csv(
            str(csv_file), db_path, skip_duplicates, category_override
        )
        total_imported += imported_count

        if imported_count > 0:
            ingested_file = ingested_path / csv_file.name
            try:
                csv_file.rename(ingested_file)
                logging.info(f"Moved {csv_file.name} to {ingested_dir}")
            except Exception as e:
                logging.error(f"Error moving {csv_file.name}: {e}")
        else:
            logging.warning(f"No events imported from {csv_file.name}, file not moved")

    logging.info(f"Processing complete! Total events imported: {total_imported}")
    return total_imported


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Kaggle BBC news events (CSV) into the ClariFi database for event correlation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import a specific CSV file
  python kaggle_bbc_news_ingestion.py --file bbc_sample.csv

  # Process all CSV files in the ingest folder
  python kaggle_bbc_news_ingestion.py --process

  # Override category and limit the number of rows imported
  python kaggle_bbc_news_ingestion.py --file bbc_sample.csv --category world-news --limit 100
        """,
    )

    parser.add_argument(
        "--file", "-f", help="Path to a specific Kaggle BBC CSV file to import"
    )
    parser.add_argument(
        "--ingest-dir",
        "-i",
        default="ingest",
        help="Directory containing CSV files (default: ingest)",
    )
    parser.add_argument(
        "--ingested-dir",
        "-o",
        default="ingested",
        help="Directory for processed files (default: ingested)",
    )
    parser.add_argument(
        "--db-path",
        "-d",
        default="clarifi.db",
        help="Path to SQLite database (default: clarifi.db)",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process all CSV files in the ingest folder",
    )
    parser.add_argument(
        "--category", help="Override the derived category for all imported events"
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum number of rows to import from a single file"
    )
    parser.add_argument(
        "--no-skip-duplicates", action="store_true", help="Do not skip duplicate events"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument("--log-file", help="Log to file in addition to console")

    args = parser.parse_args()

    setup_logging(args.log_level, args.log_file)

    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    skip_duplicates = not args.no_skip_duplicates

    if args.file:
        imported_count = import_events_from_csv(
            args.file, args.db_path, skip_duplicates, args.category, args.limit
        )
        logging.info(
            f"Import Summary: {imported_count} events imported from {args.file}"
        )
    elif args.process:
        total_imported = process_ingest_folder(
            args.ingest_dir,
            args.ingested_dir,
            args.db_path,
            skip_duplicates,
            args.category,
        )
        logging.info(f"Processing Summary: {total_imported} total events imported")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
