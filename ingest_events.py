#!/usr/bin/env python3
"""
Automated Event Ingestion Script for ClariFi
Monitors the ingest folder and processes new JSON files automatically
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from database.models import DatabaseManager


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def import_events_from_json(json_file_path: str, db_path: str = "clarifi.db", skip_duplicates: bool = True) -> int:
    """
    Import events from a JSON file into the database.

    Args:
        json_file_path: Path to the JSON file containing events
        db_path: Path to the SQLite database file
        skip_duplicates: Whether to skip events that already exist

    Returns:
        Number of events imported
    """
    logging.info(f"Importing events from {json_file_path}...")

    # Load JSON data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"File {json_file_path} not found")
        return 0
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {json_file_path}: {e}")
        return 0

    if not isinstance(events_data, list):
        logging.error(f"Expected a list of events in {json_file_path}")
        return 0

    # Initialize database manager
    db_manager = DatabaseManager(db_path)

    imported_count = 0
    skipped_count = 0
    duplicate_count = 0

    for event_data in events_data:
        try:
            # Extract fields from JSON
            event_date = event_data.get('date', '')
            event_title = event_data.get('event', '')
            summary = event_data.get('summary', '')
            link = event_data.get('link', '')
            impact = event_data.get('impact', '')
            category = event_data.get('category', '')

            # Validate required fields
            if not event_date or not event_title:
                logging.warning(f"Skipping event with missing date or title: {event_data}")
                skipped_count += 1
                continue

            # Check for duplicates if requested
            if skip_duplicates:
                existing_events = db_manager.get_all_events()
                is_duplicate = any(
                    e['event_date'] == event_date and e['event'] == event_title
                    for e in existing_events
                )
                if is_duplicate:
                    logging.debug(f"Skipping duplicate event: {event_title} on {event_date}")
                    duplicate_count += 1
                    continue

            # Insert event into database
            db_manager.insert_event(
                event_date=event_date,
                event=event_title,
                category=category,
                impact=impact,
                summary=summary,
                link=link
            )

            imported_count += 1

        except Exception as e:
            logging.error(f"Error importing event {event_data.get('event', 'Unknown')}: {e}")
            skipped_count += 1
            continue

    logging.info(f"Imported {imported_count} events successfully")
    if skipped_count > 0:
        logging.warning(f"Skipped {skipped_count} events due to errors")
    if duplicate_count > 0:
        logging.info(f"Skipped {duplicate_count} duplicate events")

    return imported_count


def process_ingest_folder(ingest_dir: str, ingested_dir: str, db_path: str = "clarifi.db",
                         skip_duplicates: bool = True) -> int:
    """
    Process all JSON files in the ingest folder and move them to ingested folder after processing.

    Args:
        ingest_dir: Path to the ingest directory
        ingested_dir: Path to the ingested directory
        db_path: Path to the SQLite database file
        skip_duplicates: Whether to skip duplicate events

    Returns:
        Total number of events imported
    """
    ingest_path = Path(ingest_dir)
    ingested_path = Path(ingested_dir)

    # Ensure ingested directory exists
    ingested_path.mkdir(exist_ok=True)

    # Find all JSON files in ingest directory
    json_files = list(ingest_path.glob("*.json"))

    if not json_files:
        logging.info(f"No JSON files found in {ingest_dir}")
        return 0

    logging.info(f"Found {len(json_files)} JSON files to process")

    total_imported = 0

    for json_file in json_files:
        logging.info(f"Processing {json_file.name}...")

        # Import events from the file
        imported_count = import_events_from_json(str(json_file), db_path, skip_duplicates)
        total_imported += imported_count

        if imported_count > 0:
            # Move file to ingested directory
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


def monitor_ingest_folder(ingest_dir: str, ingested_dir: str, db_path: str = "clarifi.db",
                         interval: int = 60, skip_duplicates: bool = True):
    """
    Monitor the ingest folder and process new files periodically.

    Args:
        ingest_dir: Path to the ingest directory
        ingested_dir: Path to the ingested directory
        db_path: Path to the SQLite database file
        interval: Monitoring interval in seconds
        skip_duplicates: Whether to skip duplicate events
    """
    logging.info(f"Starting ingest folder monitor (interval: {interval}s)")

    while True:
        try:
            process_ingest_folder(ingest_dir, ingested_dir, db_path, skip_duplicates)
        except Exception as e:
            logging.error(f"Error during monitoring: {e}")

        logging.debug(f"Sleeping for {interval} seconds...")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description='Automated event data ingestion for ClariFi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process files once
  python ingest_events.py --process

  # Monitor folder continuously
  python ingest_events.py --monitor --interval 300

  # Process with custom paths
  python ingest_events.py --process --ingest-dir /path/to/ingest --ingested-dir /path/to/processed

  # Import specific file
  python ingest_events.py --file data/2024.json

  # Enable debug logging
  python ingest_events.py --process --log-level DEBUG
        """
    )

    parser.add_argument('--file', '-f', help='Path to a specific JSON file to import')
    parser.add_argument('--ingest-dir', '-i', default='ingest', help='Directory containing JSON files (default: ingest)')
    parser.add_argument('--ingested-dir', '-o', default='ingested', help='Directory for processed files (default: ingested)')
    parser.add_argument('--db-path', '-d', default='clarifi.db', help='Path to SQLite database (default: clarifi.db)')
    parser.add_argument('--process', action='store_true', help='Process all files in ingest folder once')
    parser.add_argument('--monitor', action='store_true', help='Monitor ingest folder continuously')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--no-skip-duplicates', action='store_true', help='Do not skip duplicate events')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Logging level (default: INFO)')
    parser.add_argument('--log-file', help='Log to file in addition to console')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    skip_duplicates = not args.no_skip_duplicates

    if args.file:
        # Import specific file
        imported_count = import_events_from_json(args.file, args.db_path, skip_duplicates)
        logging.info(f"Import Summary: {imported_count} events imported from {args.file}")

    elif args.monitor:
        # Monitor folder continuously
        monitor_ingest_folder(args.ingest_dir, args.ingested_dir, args.db_path,
                            args.interval, skip_duplicates)

    elif args.process:
        # Process folder once
        total_imported = process_ingest_folder(args.ingest_dir, args.ingested_dir,
                                             args.db_path, skip_duplicates)
        logging.info(f"Processing Summary: {total_imported} total events imported")

    else:
        # Default: process folder once
        logging.info("No action specified, processing ingest folder once...")
        total_imported = process_ingest_folder(args.ingest_dir, args.ingested_dir,
                                             args.db_path, skip_duplicates)
        logging.info(f"Processing Summary: {total_imported} total events imported")


if __name__ == "__main__":
    main()
