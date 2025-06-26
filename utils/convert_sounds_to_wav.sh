#!/bin/bash

SOUNDS_DIR="$(dirname "$0")/sounds"
cd "$SOUNDS_DIR" || exit 1

for file in *.m4a; do
  [ -e "$file" ] || continue
  base="${file%.m4a}"
  if [ ! -f "$base.wav" ]; then
    echo "Converting $file to $base.wav..."
    ffmpeg -y -i "$file" "$base.wav"
  else
    echo "$base.wav already exists, skipping."
  fi
done

echo "All conversions complete."
