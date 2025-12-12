#!/usr/bin/env bash

set -e

TARGET_DIR="$1"
OUTPUT="$TARGET_DIR/analysis.md"

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <target_directory>"
    exit 1
fi

echo "[*] Starting analysis of $TARGET_DIR"

# Initialize output file
echo "# Binary Analysis" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "Generated on: $(date)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Find all executables
BINARIES=($(find "$TARGET_DIR" -maxdepth 2 -type f -executable ! -name "*.so*" ! -name "ld-*"))

if [ ${#BINARIES[@]} -eq 0 ]; then
    echo "[!] No executable binaries found."
    echo "**No executable binaries found in the challenge directory.**" >> "$OUTPUT"
    exit 0
fi

echo "[+] Found ${#BINARIES[@]} binary/binaries"

# Analyze each binary
for BINARY in "${BINARIES[@]}"; do
    BINARY_NAME=$(basename "$BINARY")
    echo "" >> "$OUTPUT"
    echo "---" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "## Binary: \`$BINARY_NAME\`" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    echo "[*] Analyzing $BINARY_NAME"

    # File type information
    echo "### File Information" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    file "$BINARY" >> "$OUTPUT" 2>&1
    echo '```' >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    # Basic properties
    echo "### Basic Properties" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    echo "Size: $(stat -f%z "$BINARY" 2>/dev/null || stat -c%s "$BINARY") bytes" >> "$OUTPUT"
    echo "MD5: $(md5sum "$BINARY" | cut -d' ' -f1)" >> "$OUTPUT"
    echo "SHA256: $(sha256sum "$BINARY" | cut -d' ' -f1)" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    # Checksec (security features)
    echo "### Security Features (checksec)" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    if command -v pwn &> /dev/null; then
        pwn checksec "$BINARY" >> "$OUTPUT" 2>&1
    elif command -v checksec &> /dev/null; then
        checksec --file="$BINARY" >> "$OUTPUT" 2>&1
    else
        echo "checksec not available" >> "$OUTPUT"
    fi
    echo '```' >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    # Library dependencies
    echo "### Library Dependencies (ldd)" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    ldd "$BINARY" 2>&1 >> "$OUTPUT" || echo "Not a dynamic executable" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    # Rabin2 analysis (if available)
    if command -v rabin2 &> /dev/null; then
        echo "### Binary Info (rabin2)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rabin2 -I "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Imports
        echo "### Imported Functions (rabin2 -i)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rabin2 -i "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Exports/Symbols
        echo "### Exported Symbols (rabin2 -E)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rabin2 -E "$BINARY" 2>&1 | head -n 50 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Sections
        echo "### Sections (rabin2 -S)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rabin2 -S "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Strings from data sections
        echo "### Strings (rabin2 -z)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rabin2 -z "$BINARY" 2>&1 | head -n 100 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi

    # Rizin analysis (if available and rabin2 not present)
    if command -v rizin &> /dev/null && ! command -v rabin2 &> /dev/null; then
        echo "### Rizin Analysis" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rizin -q -c 'iI' "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        echo "### Functions (rizin)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rizin -q -c 'aa; afl' "$BINARY" 2>&1 | head -n 50 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        echo "### Imports (rizin)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        rizin -q -c 'ii' "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi

    # Readelf analysis (GOT/PLT)
    if command -v readelf &> /dev/null; then
        echo "### GOT/PLT Entries (readelf)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        readelf -r "$BINARY" 2>&1 | grep -A 200 "Relocation section" >> "$OUTPUT" || echo "No relocations found" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        echo "### Program Headers" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        readelf -l "$BINARY" 2>&1 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        echo "### Dynamic Section" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        readelf -d "$BINARY" 2>&1 >> "$OUTPUT" || echo "No dynamic section" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi

    # Object dump - functions/symbols
    if command -v objdump &> /dev/null; then
        echo "### Functions/Symbols (objdump)" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        objdump -t "$BINARY" 2>&1 | grep -E "F .text" | head -n 50 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Disassembly of main (if exists)
        if objdump -t "$BINARY" 2>&1 | grep -q " main$"; then
            echo "### Disassembly of main() function" >> "$OUTPUT"
            echo '```asm' >> "$OUTPUT"
            objdump -d "$BINARY" -M intel 2>&1 | sed -n '/<main>:/,/^$/p' | head -n 100 >> "$OUTPUT"
            echo '```' >> "$OUTPUT"
            echo "" >> "$OUTPUT"
        fi
    fi

    # Syscalls detection (using strace on a quick run, or static analysis)
    if command -v rabin2 &> /dev/null; then
        echo "### Potential Syscalls" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        # Look for syscall instructions in the binary
        objdump -d "$BINARY" 2>&1 | grep -E "syscall|int.*0x80|sysenter" | head -n 30 >> "$OUTPUT" || echo "No direct syscalls found in disassembly" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi

    # Strings analysis (fallback if rabin2 not available)
    if ! command -v rabin2 &> /dev/null; then
        echo "### Interesting Strings" >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        strings -a "$BINARY" | head -n 200 >> "$OUTPUT"
        echo '```' >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi

    # Search for potential vulnerabilities patterns
    echo "### Vulnerability Patterns" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
    echo "Dangerous functions found in imports:" >> "$OUTPUT"
    if command -v rabin2 &> /dev/null; then
        rabin2 -i "$BINARY" 2>&1 | grep -E "(gets|strcpy|strcat|sprintf|scanf|system|exec|malloc|realloc|free)" >> "$OUTPUT" || echo "None of the common dangerous functions found" >> "$OUTPUT"
    else
        objdump -T "$BINARY" 2>&1 | grep -E "(gets|strcpy|strcat|sprintf|scanf|system|exec|malloc|realloc|free)" >> "$OUTPUT" || echo "None of the common dangerous functions found" >> "$OUTPUT"
    fi
    echo '```' >> "$OUTPUT"
    echo "" >> "$OUTPUT"

done

# Check for additional files (libc, linker, source code)
echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## Additional Files" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Libraries
LIBS=($(find "$TARGET_DIR" -maxdepth 2 -type f \( -name "*.so*" -o -name "libc*" \)))
if [ ${#LIBS[@]} -gt 0 ]; then
    echo "### Provided Libraries" >> "$OUTPUT"
    for LIB in "${LIBS[@]}"; do
        LIB_NAME=$(basename "$LIB")
        echo "- \`$LIB_NAME\`" >> "$OUTPUT"
        echo "  - File: \`$(file "$LIB" | cut -d: -f2-)\`" >> "$OUTPUT"
        if command -v strings &> /dev/null; then
            VERSION=$(strings "$LIB" | grep -E "^GNU C Library.*release version" | head -n 1)
            if [ ! -z "$VERSION" ]; then
                echo "  - Version: $VERSION" >> "$OUTPUT"
            fi
        fi
        if command -v pwn &> /dev/null; then
            pwn checksec "$LIB" >> "$OUTPUT" 2>&1
        fi
    done
    echo "" >> "$OUTPUT"
fi

# Linkers
LINKERS=($(find "$TARGET_DIR" -maxdepth 2 -type f \( -name "ld-*" -o -name "ld.so*" \)))
if [ ${#LINKERS[@]} -gt 0 ]; then
    echo "### Provided Linkers" >> "$OUTPUT"
    for LD in "${LINKERS[@]}"; do
        LD_NAME=$(basename "$LD")
        echo "- \`$LD_NAME\`" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

# Source files
SOURCES=($(find "$TARGET_DIR" -maxdepth 2 -type f \( -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.s" -o -name "*.asm" \)))
if [ ${#SOURCES[@]} -gt 0 ]; then
    echo "### Source Files" >> "$OUTPUT"
    for SRC in "${SOURCES[@]}"; do
        SRC_NAME=$(basename "$SRC")
        echo "- \`$SRC_NAME\`" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

# Other notable files
OTHER_FILES=($(find "$TARGET_DIR" -maxdepth 2 -type f \( -name "*.txt" -o -name "README*" -o -name "*.md" -o -name "flag*" \)))
if [ ${#OTHER_FILES[@]} -gt 0 ]; then
    echo "### Other Files" >> "$OUTPUT"
    for FILE in "${OTHER_FILES[@]}"; do
        FILE_NAME=$(basename "$FILE")
        echo "- \`$FILE_NAME\`" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

# Run pwninit (if available)
echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## Pwninit Setup" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if command -v pwninit &> /dev/null && [ ${#BINARIES[@]} -gt 0 ]; then
    echo '```' >> "$OUTPUT"
    cd "$TARGET_DIR"
    pwninit --bin "${BINARIES[0]}" 2>&1 >> "$OUTPUT" || echo "pwninit setup completed (or failed gracefully)" >> "$OUTPUT"
    echo '```' >> "$OUTPUT"
else
    echo "pwninit not available or no binaries to process" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "*Analysis complete*" >> "$OUTPUT"

echo "[+] Analysis written to $OUTPUT"
echo "[+] Analysis complete!"
