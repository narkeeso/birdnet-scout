#!/usr/bin/env bash
# shellcheck shell=bash

# Configuration
RECORDINGS_DIR="recordings"
SLEEP_SECONDS=2

# Handle interrupt signal
trap 'echo "Stopping WAV file monitor..."; exit 0' INT TERM

echo "Starting WAV file monitor (checking every $SLEEP_SECONDS seconds)..."
echo "Press Ctrl+C to stop"

while true; do
    curl --fail http://localhost:5000/heartbeat/analzyer

    # Find WAV files
    wav_files=$(find "$RECORDINGS_DIR" -type f -name "*.wav")

    # Check if any WAV files were found
    if [ -n "$wav_files" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Found WAV files"
        poetry run python -m analyzer
    fi

    sleep "$SLEEP_SECONDS"
done
