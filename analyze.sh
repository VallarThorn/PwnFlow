#!/usr/bin/env bash

set -e

TARGET_DIR="$1"
OUTPUT="$TARGET_DIR/analysis.md"

echo "# Analysis" > "$OUTPUT"
echo "" >> "$OUTPUT"

# Detect binary (MVP: first executable file)
BINARY=$(find "$TARGET_DIR" -maxdepth 1 -type f -perm -111 | head -n 1)

if [ -z "$BINARY" ]; then
    echo "No executable binary found."
    exit 1
fi

echo "## Binary" >> "$OUTPUT"
echo "\`$BINARY\`" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "## pwninit" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
pwninit --bin "$BINARY" 2>&1 >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "## file" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
file "$BINARY" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "## ldd" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
ldd "$BINARY" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "## checksec" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
pwn checksec "$BINARY" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "## strings" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
strings -a "$BINARY" | head -n 200 >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo "" >> "$OUTPUT"

