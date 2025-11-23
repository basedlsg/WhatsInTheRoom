#!/bin/bash
# Resilient inference runner - automatically restarts if process stops

FLOORPLAN_DIR="data/floorplans"
IMAGE_DIR="data/images"
OUTPUT_FILE="data/results/predictions.parquet"
LOG_FILE="/tmp/inference_resilient.log"
BATCH_DELAY=0.5

echo "Starting resilient inference runner at $(date)" | tee -a "$LOG_FILE"
echo "This script will automatically restart inference if it stops" | tee -a "$LOG_FILE"

# Function to get current prediction count
get_prediction_count() {
    python3 -c "
import pandas as pd
import os
try:
    if os.path.exists('$OUTPUT_FILE'):
        df = pd.read_parquet('$OUTPUT_FILE')
        print(len(df))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0"
}

# Run inference in a loop until we have all 2391 predictions
TARGET=2391
CONSECUTIVE_FAILURES=0
MAX_CONSECUTIVE_FAILURES=5

while true; do
    CURRENT=$(get_prediction_count)
    echo "[$(date '+%H:%M:%S')] Current progress: $CURRENT/$TARGET predictions" | tee -a "$LOG_FILE"

    if [ "$CURRENT" -ge "$TARGET" ]; then
        echo "[$(date '+%H:%M:%S')] ✓ Inference complete! All $TARGET predictions saved." | tee -a "$LOG_FILE"
        break
    fi

    echo "[$(date '+%H:%M:%S')] Starting inference (resume from $CURRENT)..." | tee -a "$LOG_FILE"

    # Run inference
    export NVIDIA_API_KEY="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"
    python -m src.pipeline.run_inference \
        --floorplan-dir "$FLOORPLAN_DIR" \
        --image-dir "$IMAGE_DIR" \
        --output "$OUTPUT_FILE" \
        --batch-delay "$BATCH_DELAY" \
        2>&1 | tee -a "$LOG_FILE"

    EXIT_CODE=$?
    NEW_CURRENT=$(get_prediction_count)

    if [ "$NEW_CURRENT" -eq "$CURRENT" ]; then
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
        echo "[$(date '+%H:%M:%S')] ⚠ Warning: No progress made (failure #$CONSECUTIVE_FAILURES)" | tee -a "$LOG_FILE"

        if [ "$CONSECUTIVE_FAILURES" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
            echo "[$(date '+%H:%M:%S')] ✗ Error: $MAX_CONSECUTIVE_FAILURES consecutive failures, giving up" | tee -a "$LOG_FILE"
            exit 1
        fi

        # Wait longer on consecutive failures
        WAIT_TIME=$((10 * CONSECUTIVE_FAILURES))
        echo "[$(date '+%H:%M:%S')] Waiting $WAIT_TIME seconds before retry..." | tee -a "$LOG_FILE"
        sleep "$WAIT_TIME"
    else
        CONSECUTIVE_FAILURES=0
        PROGRESS=$((NEW_CURRENT - CURRENT))
        echo "[$(date '+%H:%M:%S')] ✓ Made progress: +$PROGRESS predictions (now at $NEW_CURRENT/$TARGET)" | tee -a "$LOG_FILE"

        if [ "$NEW_CURRENT" -lt "$TARGET" ]; then
            echo "[$(date '+%H:%M:%S')] Restarting inference after 2 seconds..." | tee -a "$LOG_FILE"
            sleep 2
        fi
    fi
done

echo "[$(date '+%H:%M:%S')] Inference pipeline complete!" | tee -a "$LOG_FILE"
