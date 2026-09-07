#!/bin/bash
# peak-forecast daily job: forecast then delta digest. Logs to data/logs/.
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
LOG="data/logs/$(date +%F).log"
echo "=== $(date '+%F %T') run ===" >> "$LOG"
python scripts/run_forecast.py >> "$LOG" 2>&1
python scripts/tg_digest.py >> "$LOG" 2>&1
echo "=== done ===" >> "$LOG"
