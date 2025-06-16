#!/bin/bash

echo "Checking for audio devices..."
if ! arecord -l | grep -q "card"; then
    echo "Error: No audio devices found!" >&2
    echo "Available devices:" >&2
    arecord -l >&2
    exit 1
fi

# Directory for recordings
RECORDINGS_DIR="recordings"
mkdir -p "$RECORDINGS_DIR"
mkdir -p "/tmp/birdnet/$RECORDINGS_DIR"

# Recording parameters
DURATION=12
FORMAT="cd"
CHANNELS=1
RATE=44100

echo "Starting recorder process..."

while true; do
    # Get current timestamp
    START_TIMESTAMP=$(date +%s)
    
    # Create recording filename
    RECORDING_KEY="${RECORDINGS_DIR}/${START_TIMESTAMP}_${DURATION}.wav"
    TEMP_FILE="/tmp/birdnet/${RECORDING_KEY}"
    
    echo "Recording for $DURATION seconds"
    
    # Record audio
    arecord \
        -d "$DURATION" \
        -f "$FORMAT" \
        -c "$CHANNELS" \
        -r "$RATE" \
        "$TEMP_FILE"
    
    # Move from temp to final location
    mv "$TEMP_FILE" "$RECORDING_KEY"
    
    echo "Recording saved to $RECORDING_KEY"
done
