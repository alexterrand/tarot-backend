#!/bin/bash
# Monitor training progress by extracting key metrics

LOG_FILE="/tmp/claude/-home-terrand-Work-tarot-project/tasks/b4ae8b5.output"

echo "==================================================================="
echo "MONITORING TRAINING PROGRESS"
echo "==================================================================="
echo ""

# Wait for log file to be created
while [ ! -f "$LOG_FILE" ]; do
    sleep 1
done

echo "Training started! Monitoring metrics..."
echo ""

# Extract and display metrics as they come
tail -f "$LOG_FILE" | grep --line-buffered -E "rollout/|time/|train/" | while read line; do
    echo "$line"
done
