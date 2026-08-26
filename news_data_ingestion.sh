#!/bin/bash
# ClariFi News Data Ingestion Runner
# Ingests newsdata.io-style news JSON exports (from a file or inline JSON) into the events table

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
INGEST_DIR="ingest"
INGESTED_DIR="ingested"
DB_PATH="clarifi.db"
LOG_LEVEL="INFO"
ACTION="process"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --file)
      ACTION="file"
      FILE="$2"
      shift 2
      ;;
    --inline)
      ACTION="inline"
      INLINE_JSON="$2"
      shift 2
      ;;
    --process)
      ACTION="process"
      shift
      ;;
    --ingest-dir)
      INGEST_DIR="$2"
      shift 2
      ;;
    --ingested-dir)
      INGESTED_DIR="$2"
      shift 2
      ;;
    --db-path)
      DB_PATH="$2"
      shift 2
      ;;
    --category)
      CATEGORY="$2"
      shift 2
      ;;
    --language)
      LANGUAGE="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --no-skip-duplicates)
      NO_SKIP_DUPLICATES=1
      shift
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift 2
      ;;
    --log-file)
      LOG_FILE="$2"
      shift 2
      ;;
    --help)
      echo "ClariFi News Data Ingestion Runner"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --file PATH         Import a specific news JSON export"
      echo "  --inline JSON       Import an inline JSON string (pass '-' to read JSON from stdin)"
      echo "  --process           Process all JSON files in the ingest folder (default)"
      echo "  --ingest-dir DIR    Directory containing JSON files (default: ingest)"
      echo "  --ingested-dir DIR  Directory for processed files (default: ingested)"
      echo "  --db-path PATH      Path to SQLite database (default: clarifi.db)"
      echo "  --category CAT      Only import articles matching this category (e.g. business)"
      echo "  --language LANG     Only import articles matching this language (e.g. english)"
      echo "  --limit N           Maximum number of articles to import from a single file"
      echo "  --no-skip-duplicates  Do not skip articles already imported"
      echo "  --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
      echo "  --log-file FILE     Log to file in addition to console"
      echo "  --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --file news_data.json                      # Import a specific export"
      echo "  $0 --inline '[{\"status\": \"success\", \"results\": [...]}]'"
      echo "  curl ... | $0 --inline -                      # Pipe JSON in via stdin"
      echo "  $0 --process                                  # Process ingest/ folder once"
      echo "  $0 --file news_data.json --category business   # Only import business news"
      echo "  $0 --file news_data.json --language english --limit 200"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build the command as an array so inline JSON with spaces/quotes stays intact
CMD_ARGS=("news_data_ingestion.py" "--db-path" "$DB_PATH" "--log-level" "$LOG_LEVEL")

case "$ACTION" in
  file)
    if [[ -z "$FILE" ]]; then
      echo "❌ --file requires a path to a JSON export"
      exit 1
    fi
    CMD_ARGS+=("--file" "$FILE")
    ;;
  inline)
    if [[ -z "$INLINE_JSON" ]]; then
      echo "❌ --inline requires a JSON string (or '-' to read from stdin)"
      exit 1
    fi
    CMD_ARGS+=("--inline" "$INLINE_JSON")
    ;;
  *)
    CMD_ARGS+=("--process" "--ingest-dir" "$INGEST_DIR" "--ingested-dir" "$INGESTED_DIR")
    ;;
esac

if [[ -n "$CATEGORY" ]]; then
  CMD_ARGS+=("--category" "$CATEGORY")
fi

if [[ -n "$LANGUAGE" ]]; then
  CMD_ARGS+=("--language" "$LANGUAGE")
fi

if [[ -n "$LIMIT" ]]; then
  CMD_ARGS+=("--limit" "$LIMIT")
fi

if [[ -n "$NO_SKIP_DUPLICATES" ]]; then
  CMD_ARGS+=("--no-skip-duplicates")
fi

if [[ -n "$LOG_FILE" ]]; then
  CMD_ARGS+=("--log-file" "$LOG_FILE")
fi

echo "🚀 Starting ClariFi News Data Ingestion..."
echo "Command: python3 ${CMD_ARGS[*]}"
echo ""

# Run the command (array form preserves quoting for inline JSON payloads)
exec python3 "${CMD_ARGS[@]}"

