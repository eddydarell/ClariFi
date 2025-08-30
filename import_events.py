#!/usr/bin/env python3
"""
Event Data Import Script for ClariFi
Imports event data from JSON files into the SQLite database
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add the database module to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from database.models import DatabaseManager


def import_events_from_json(json_file_path: str, db_path: str = "clarifi.db") -> int:
    """
    Import events from a JSON file into the database.

    Args:
        json_file_path: Path to the JSON file containing events
        db_path: Path to the SQLite database file

    Returns:
        Number of events imported
    """
    print(f"📥 Importing events from {json_file_path}...")

    # Load JSON data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {json_file_path} not found")
        return 0
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {json_file_path}: {e}")
        return 0

    if not isinstance(events_data, list):
        print(f"❌ Error: Expected a list of events in {json_file_path}")
        return 0

    # Initialize database manager
    db_manager = DatabaseManager(db_path)

    imported_count = 0
    skipped_count = 0

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
                print(f"⚠️  Skipping event with missing date or title: {event_data}")
                skipped_count += 1
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
            print(f"❌ Error importing event {event_data.get('event', 'Unknown')}: {e}")
            skipped_count += 1
            continue

    print(f"✅ Imported {imported_count} events successfully")
    if skipped_count > 0:
        print(f"⚠️  Skipped {skipped_count} events due to errors")

    return imported_count


def process_ingest_folder(ingest_dir: str, ingested_dir: str, db_path: str = "clarifi.db") -> None:
    """
    Process all JSON files in the ingest folder and move them to ingested folder after processing.

    Args:
        ingest_dir: Path to the ingest directory
        ingested_dir: Path to the ingested directory
        db_path: Path to the SQLite database file
    """
    ingest_path = Path(ingest_dir)
    ingested_path = Path(ingested_dir)

    # Ensure ingested directory exists
    ingested_path.mkdir(exist_ok=True)

    # Find all JSON files in ingest directory
    json_files = list(ingest_path.glob("*.json"))

    if not json_files:
        print(f"📭 No JSON files found in {ingest_dir}")
        return

    print(f"🔍 Found {len(json_files)} JSON files to process")

    total_imported = 0

    for json_file in json_files:
        print(f"\n📄 Processing {json_file.name}...")

        # Import events from the file
        imported_count = import_events_from_json(str(json_file), db_path)
        total_imported += imported_count

        if imported_count > 0:
            # Move file to ingested directory
            ingested_file = ingested_path / json_file.name
            try:
                json_file.rename(ingested_file)
                print(f"✅ Moved {json_file.name} to {ingested_dir}")
            except Exception as e:
                print(f"❌ Error moving {json_file.name}: {e}")
        else:
            print(f"⚠️  No events imported from {json_file.name}, file not moved")

    print(f"\n🎉 Processing complete! Total events imported: {total_imported}")


def main():
    parser = argparse.ArgumentParser(
        description='Import event data from JSON files into ClariFi database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import a specific JSON file
  python import_events.py --file ingest/2024.json

  # Process all files in ingest folder
  python import_events.py --ingest-dir ingest --ingested-dir ingested

  # Use custom database path
  python import_events.py --file ingest/2024.json --db-path custom.db
        """
    )

    parser.add_argument('--file', '-f', help='Path to a specific JSON file to import')
    parser.add_argument('--ingest-dir', '-i', default='ingest', help='Directory containing JSON files to process (default: ingest)')
    parser.add_argument('--ingested-dir', '-o', default='ingested', help='Directory to move processed files (default: ingested)')
    parser.add_argument('--db-path', '-d', default='clarifi.db', help='Path to SQLite database file (default: clarifi.db)')
    parser.add_argument('--process-folder', action='store_true', help='Process all files in ingest folder (default behavior when no --file specified)')

    args = parser.parse_args()

    # Change to the script's directory to ensure relative paths work
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    if args.file:
        # Import specific file
        imported_count = import_events_from_json(args.file, args.db_path)
        print(f"\n📊 Import Summary: {imported_count} events imported from {args.file}")
    else:
        # Process ingest folder
        process_ingest_folder(args.ingest_dir, args.ingested_dir, args.db_path)


if __name__ == "__main__":
    main()
