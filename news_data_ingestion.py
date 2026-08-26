#!/usr/bin/env python3
"""
News Data Ingestion Script for ClariFi
Ingests news articles from newsdata.io-style JSON exports (top-level list of
response pages, each with status/totalResults/results/nextPage) and populates
the events table used for event correlation.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from database.models import DatabaseManager

# Very small keyword lists to give a rough sentiment/impact hint for correlation weighting
NEGATIVE_KEYWORDS = [
    "war", "attack", "crisis", "crash", "recession", "collapse", "conflict",
    "sanction", "death", "killed", "shortage", "inflation", "layoff", "strike",
    "lawsuit", "fraud", "default", "plunge", "ban", "bankrupt", "downgrade",
    "investigation", "recall",
]
POSITIVE_KEYWORDS = [
    "growth", "deal", "agreement", "record", "surge", "profit", "recovery",
    "breakthrough", "rally", "win", "boost", "expansion", "approval",
    "upgrade", "partnership", "launch",
]

REQUIRED_ARTICLE_FIELDS = {"title", "pubDate", "link"}


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
    """Parse a 'YYYY-MM-DD HH:MM:SS' (or ISO) pubDate string into an ISO date (YYYY-MM-DD)."""
    if not pub_date_raw:
        return None
    raw = pub_date_raw.strip()
    date_part = raw.split(" ")[0].split("T")[0]
    try:
        from datetime import datetime
        datetime.strptime(date_part, "%Y-%m-%d")
        return date_part
    except ValueError:
        logging.warning(f"Could not parse pubDate '{pub_date_raw}'")
        return None


def derive_category(categories: Any) -> str:
    """Flatten a newsdata.io category list/string into a single comma-joined category string."""
    if isinstance(categories, list) and categories:
        return ", ".join(str(c) for c in categories if c)
    if isinstance(categories, str) and categories:
        return categories
    return "general"


def classify_impact(title: str, description: str) -> str:
    """Very small keyword-based heuristic for expected market impact."""
    text = f"{title} {description or ''}".lower()
    if any(word in text for word in NEGATIVE_KEYWORDS):
        return "negative"
    if any(word in text for word in POSITIVE_KEYWORDS):
        return "positive"
    return "neutral"


def extract_articles(raw_data: Any) -> List[Dict[str, Any]]:
    """
    Flatten a newsdata.io-style export into a list of article dicts.

    Handles:
      - a top-level list of response pages, each with a "results" list
      - a single response page dict with a "results" list
      - an already-flat list of article dicts
    """
    pages: List[Any]
    if isinstance(raw_data, dict):
        pages = [raw_data]
    elif isinstance(raw_data, list):
        pages = raw_data
    else:
        return []

    articles: List[Dict[str, Any]] = []
    for page in pages:
        if isinstance(page, dict) and isinstance(page.get("results"), list):
            articles.extend(a for a in page["results"] if isinstance(a, dict))
        elif isinstance(page, dict) and REQUIRED_ARTICLE_FIELDS.issubset(page.keys()):
            # Already a flat article dict
            articles.append(page)
    return articles


def _import_articles(
    raw_data: Any,
    source_label: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_filter: Optional[str] = None,
    language: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """Shared import loop: flattens parsed JSON into articles and writes them to the events table."""
    articles = extract_articles(raw_data)
    if not articles:
        logging.error(f"No articles found in {source_label} (expected a 'results' list)")
        return 0

    db_manager = DatabaseManager(db_path)

    existing_events = db_manager.get_all_events() if skip_duplicates else []
    existing_ids = {e["id"] for e in existing_events}

    imported_count = 0
    skipped_count = 0
    duplicate_count = 0
    filtered_count = 0

    for article in articles:
        if limit is not None and imported_count >= limit:
            break
        try:
            article_id = article.get("article_id")
            title = (article.get("title") or "").strip()
            link = (article.get("link") or "").strip()
            description = (article.get("description") or "").strip()
            event_date = parse_pub_date(article.get("pubDate", ""))
            categories = article.get("category")
            article_language = (article.get("language") or "").strip()

            if not event_date or not title:
                logging.warning(f"Skipping article with missing date or title: {article.get('title', article_id)}")
                skipped_count += 1
                continue

            if language and article_language and article_language.lower() != language.lower():
                filtered_count += 1
                continue

            if category_filter and category_filter.lower() not in [
                str(c).lower() for c in (categories if isinstance(categories, list) else [categories])
            ]:
                filtered_count += 1
                continue

            if skip_duplicates and article_id and article_id in existing_ids:
                logging.debug(f"Skipping duplicate article: {title} ({article_id})")
                duplicate_count += 1
                continue

            category = derive_category(categories)
            impact = classify_impact(title, description)

            db_manager.insert_event(
                event_date=event_date,
                event=title,
                category=category,
                impact=impact,
                summary=description,
                link=link,
                event_id=article_id,
            )

            if article_id:
                existing_ids.add(article_id)
            imported_count += 1

        except Exception as e:
            logging.error(f"Error importing article {article.get('title', 'Unknown')}: {e}")
            skipped_count += 1
            continue

    logging.info(f"Imported {imported_count} news events successfully")
    if skipped_count > 0:
        logging.warning(f"Skipped {skipped_count} articles due to errors")
    if duplicate_count > 0:
        logging.info(f"Skipped {duplicate_count} duplicate articles")
    if filtered_count > 0:
        logging.info(f"Filtered out {filtered_count} articles not matching filters")

    return imported_count


def import_news_from_file(
    json_file_path: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_filter: Optional[str] = None,
    language: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """Import news articles from a newsdata.io-style JSON file into the events table."""
    logging.info(f"Importing news articles from {json_file_path}...")

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"File {json_file_path} not found")
        return 0
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {json_file_path}: {e}")
        return 0

    return _import_articles(
        raw_data, json_file_path, db_path, skip_duplicates, category_filter, language, limit
    )


def import_news_from_string(
    json_string: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_filter: Optional[str] = None,
    language: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """Import news articles from an inline JSON string into the events table."""
    logging.info("Importing news articles from inline JSON string...")

    try:
        raw_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid inline JSON: {e}")
        return 0

    return _import_articles(
        raw_data, "inline JSON", db_path, skip_duplicates, category_filter, language, limit
    )


def process_ingest_folder(
    ingest_dir: str,
    ingested_dir: str,
    db_path: str = "clarifi.db",
    skip_duplicates: bool = True,
    category_filter: Optional[str] = None,
    language: Optional[str] = None,
) -> int:
    """Process all JSON files in the ingest folder and move them to ingested folder after processing."""
    ingest_path = Path(ingest_dir)
    ingested_path = Path(ingested_dir)

    ingested_path.mkdir(exist_ok=True)

    json_files = list(ingest_path.glob("*.json"))

    if not json_files:
        logging.info(f"No JSON files found in {ingest_dir}")
        return 0

    logging.info(f"Found {len(json_files)} JSON files to process")

    total_imported = 0

    for json_file in json_files:
        logging.info(f"Processing {json_file.name}...")

        imported_count = import_news_from_file(
            str(json_file), db_path, skip_duplicates, category_filter, language
        )
        total_imported += imported_count

        if imported_count > 0:
            ingested_file = ingested_path / json_file.name
            try:
                json_file.rename(ingested_file)
                logging.info(f"Moved {json_file.name} to {ingested_dir}")
            except Exception as e:
                logging.error(f"Error moving {json_file.name}: {e}")
        else:
            logging.warning(f"No events imported from {json_file.name}, file not moved")

    logging.info(f"Processing complete! Total events imported: {total_imported}")
    return total_imported


def main():
    parser = argparse.ArgumentParser(
        description="Ingest newsdata.io-style news articles (JSON) into the ClariFi database for event correlation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import a specific JSON export
  python news_data_ingestion.py --file news_data.json

  # Import an inline JSON string
  python news_data_ingestion.py --inline '[{"status": "success", "results": [...]}]'

  # Pipe JSON in via stdin
  curl ... | python news_data_ingestion.py --inline -

  # Process all JSON files in the ingest folder
  python news_data_ingestion.py --process

  # Only import english business articles, capped at 200
  python news_data_ingestion.py --file news_data.json --language english --category business --limit 200
        """,
    )

    parser.add_argument("--file", "-f", help="Path to a specific news JSON export to import")
    parser.add_argument("--inline", "-j", help="Inline JSON string to import (pass '-' to read JSON from stdin)")
    parser.add_argument("--ingest-dir", "-i", default="ingest", help="Directory containing JSON files (default: ingest)")
    parser.add_argument("--ingested-dir", "-o", default="ingested", help="Directory for processed files (default: ingested)")
    parser.add_argument("--db-path", "-d", default="clarifi.db", help="Path to SQLite database (default: clarifi.db)")
    parser.add_argument("--process", action="store_true", help="Process all JSON files in the ingest folder")
    parser.add_argument("--category", help="Only import articles matching this category (e.g. business)")
    parser.add_argument("--language", help="Only import articles matching this language (e.g. english)")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to import from a single file")
    parser.add_argument("--no-skip-duplicates", action="store_true", help="Do not skip articles already imported")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level (default: INFO)")
    parser.add_argument("--log-file", help="Log to file in addition to console")

    args = parser.parse_args()

    setup_logging(args.log_level, args.log_file)

    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    skip_duplicates = not args.no_skip_duplicates

    if args.file:
        imported_count = import_news_from_file(
            args.file, args.db_path, skip_duplicates, args.category, args.language, args.limit
        )
        logging.info(f"Import Summary: {imported_count} events imported from {args.file}")
    elif args.inline is not None:
        json_string = sys.stdin.read() if args.inline == "-" else args.inline
        imported_count = import_news_from_string(
            json_string, args.db_path, skip_duplicates, args.category, args.language, args.limit
        )
        logging.info(f"Import Summary: {imported_count} events imported from inline JSON")
    elif args.process:
        total_imported = process_ingest_folder(
            args.ingest_dir, args.ingested_dir, args.db_path, skip_duplicates, args.category, args.language
        )
        logging.info(f"Processing Summary: {total_imported} total events imported")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
