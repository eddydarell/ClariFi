#!/bin/bash
# ClariFi Event Ingestion Runner
# This script runs the automated event ingestion process

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
    --monitor)
      ACTION="monitor"
      shift
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
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
      echo "ClariFi Event Ingestion Runner"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --monitor          Monitor ingest folder continuously"
      echo "  --interval SECS    Monitoring interval in seconds (default: 60)"
      echo "  --log-level LEVEL  Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
      echo "  --log-file FILE    Log to file in addition to console"
      echo "  --help             Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                          # Process files once"
      echo "  $0 --monitor                # Monitor continuously"
      echo "  $0 --monitor --interval 300 # Monitor every 5 minutes"
      echo "  $0 --log-level DEBUG        # Enable debug logging"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build the command
CMD="python3 ingest_events.py --$ACTION --ingest-dir $INGEST_DIR --ingested-dir $INGESTED_DIR --db-path $DB_PATH --log-level $LOG_LEVEL"

if [[ -n "$INTERVAL" ]]; then
  CMD="$CMD --interval $INTERVAL"
fi

if [[ -n "$LOG_FILE" ]]; then
  CMD="$CMD --log-file $LOG_FILE"
fi

echo "🚀 Starting ClariFi Event Ingestion..."
echo "Command: $CMD"
echo ""

# Run the command
exec $CMD
