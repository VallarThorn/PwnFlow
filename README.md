# Pwn Pipeline

A modular, automated pipeline for setting up and analyzing CTF pwn challenges. This tool extracts challenge files, performs comprehensive binary analysis, generates exploit templates, and creates organized writeup directories in your Obsidian vault.

## Features

- **CTF Organization**: Organize challenges by CTF name for better management
- **Automatic Extraction**: Supports zip, tar.gz, 7z, and more
- **Smart File Detection**: Categorizes binaries, libraries, linkers, and source files
- **Comprehensive Analysis**: Security features, functions, GOT/PLT, syscalls, vulnerability patterns
- **Template Generation**: Pwntools exploit, GDB scripts, solve scripts, and writeup templates
- **Modular Design**: Use individual components or the full pipeline
- **Directory Checking**: Warns before overwriting existing directories

## Todo

We're actively improving PwnFlow and would love your help! Here are some features we'd like to add:

- [ ] Create solve templates inside the challenge dir
- [ ] Libc version detection: Auto-download matching libc, find one-gadgets
- [ ] Auto generate exploit hints
- [ ] Vulnerability pattern detection

**Want to contribute?** We welcome contributions of all kinds! Whether you want to tackle one of these TODOs, suggest new features, fix bugs, or improve documentation, your help is appreciated. Feel free to open an issue to discuss ideas or submit a pull request with your improvements.

## Project Structure

```
pwn-pipeline/
├── pwn-pipeline              # Main orchestrator (executable)
├── setup.py                  # Setup module (executable independently)
├── analyze.sh                # Analysis script (executable independently)
├── templates.py              # Template generator (executable independently)
├── utils.py                  # Shared utilities (library module)
├── templates/
│   └── writeup_template.md  # Writeup template file
├── .gitignore
└── README.md
```

## Component Overview

### 1. `pwn-pipeline` - Main Orchestrator

**Purpose:** Coordinates all pipeline phases in sequence

**Functionality:**
- Runs the complete CTF setup workflow
- Calls `setup.py` → `analyze.sh` → `templates.py` in order
- Manages phase control (skip analysis/templates)
- Supports CTF-based organization
- Provides unified CLI and logging
- Handles errors across all phases

**Can run independently:** Yes (this is the main entry point)

**Usage:**
```bash
./pwn-pipeline --name challenge_name [options]

# With CTF organization
./pwn-pipeline --name heap_overflow --ctf picoCTF2024
```

---

### 2. `setup.py` - Extraction & Organization

**Purpose:** Extract archives and organize challenge files

**Functionality:**
- Finds the latest archive in `~/Downloads/ctf/`
- Extracts archives (supports .zip, .tar.gz, .7z, etc.)
- Creates organized directory structure
  - Without `--ctf`: `~/Desktop/Ctf/{name}/`
  - With `--ctf`: `~/Desktop/Ctf/{ctf}/{name}/`
- Categorizes files:
  - Binaries (executable files)
  - Libraries (libc.so, ld.so, etc.)
  - Linkers (ld-*.so)
  - Source files (.c, .cpp, .h, .s)
  - Other files
- Checks if directory already exists (warns before overwriting)
- Optional: Cleanup downloaded archive

**Can run independently:** Yes

**Usage:**
```bash
# Basic usage - extract latest archive
./setup.py --name challenge_name

# With CTF organization
./setup.py --name challenge_name --ctf DEFCON31

# Specify archive manually
./setup.py --name challenge_name --archive ~/Downloads/file.zip

# Keep original archive
./setup.py --name challenge_name --no-cleanup

# Custom destination
./setup.py --name challenge_name --dest ~/CTF/Challenges

# Verbose mode
./setup.py --name challenge_name -v
```

**Output:**
- Creates organized directory with all extracted files
- Prints summary of found files (binaries, libraries, etc.)
- Returns file categorization data

---

### 3. `analyze.sh` - Binary Analysis

**Purpose:** Perform comprehensive binary analysis

**Functionality:**
- Analyzes all executable binaries in a directory
- Generates `analysis.md` with:
  - File information (type, size, hashes)
  - Security features (checksec: PIE, NX, Canary, RELRO)
  - Library dependencies (ldd)
  - Binary info (rabin2/rizin if available)
  - Imported/exported functions
  - GOT/PLT entries (readelf)
  - Disassembly of main function
  - Strings and potential vulnerabilities
  - Syscall detection
  - Detection of dangerous functions
- Supports multiple binaries
- Detects and reports on libraries, linkers, and source files
- Runs pwninit for setup

**Can run independently:** Yes

**Usage:**
```bash
# Analyze a challenge directory
./analyze.sh /path/to/challenge/directory

# Examples
./analyze.sh ~/Desktop/Ctf/buffer_overflow
./analyze.sh ~/Desktop/Ctf/picoCTF2024/heap_challenge
```

**Output:**
- Creates `analysis.md` in the target directory
- Comprehensive markdown report with all findings

---

### 4. `templates.py` - Template Generation

**Purpose:** Generate exploit and writeup templates

**Functionality:**
- Creates pwntools exploit template (`exploit.py`)
  - ELF loading and context setup
  - Local/remote connection handling
  - GDB integration
  - Command-line argument parsing
- Generates GDB initialization script (`.gdbinit`)
  - Intel syntax
  - Common breakpoints
  - Helpful commands
- Creates solve script (`solve.sh`)
  - Quick wrapper for local/remote execution
- Generates Obsidian writeup template
  - Structured markdown for documentation
  - Substitutes challenge name
- Organizes vault by CTF name (if specified)
- Moves `analysis.md` to Obsidian vault
- Checks if vault directory already exists

**Can run independently:** Yes

**Usage:**
```bash
# Generate all templates
./templates.py --name challenge_name \
               --challenge-dir ~/Desktop/Ctf/challenge_name \
               --binary ~/Desktop/Ctf/challenge_name/binary

# With CTF organization
./templates.py --name heap_overflow --ctf picoCTF2024 \
               --challenge-dir ~/Desktop/Ctf/picoCTF2024/heap_overflow \
               --binary ~/Desktop/Ctf/picoCTF2024/heap_overflow/chall

# Custom vault location
./templates.py --name challenge_name \
               --challenge-dir ~/Desktop/Ctf/challenge_name \
               --binary ~/Desktop/Ctf/challenge_name/binary \
               --vault-path ~/Documents/Vault/Ctf

# Verbose mode
./templates.py --name challenge_name \
               --challenge-dir ~/Desktop/Ctf/challenge_name -v
```

**Output:**
- `exploit.py` in challenge directory
- `.gdbinit` in challenge directory
- `solve.sh` in challenge directory
- Writeup template in vault (organized by CTF if specified)
- Moves `analysis.md` to vault

---

### 5. `utils.py` - Shared Utilities 🛠️

**Purpose:** Shared functions and configurations

**Functionality:**
- Logging configuration
- Dependency checking (required and optional tools)
- Path management (default directories)
- File type detection helpers
- Directory creation utilities
- CTF-based path building
- Directory existence checking

---

## Installation

### Requirements

**Required tools:**
```bash
sudo apt install python3 file binutils coreutils findutils
pip install pwntools
```

**Optional tools (for enhanced analysis):**
```bash
# Radare2 suite
sudo apt install radare2

# Rizin (alternative to radare2)
sudo apt install rizin

# 7zip (for additional archive formats)
sudo apt install p7zip-full

# Checksec
sudo apt install checksec

# GDB with pwndbg or gef
git clone https://github.com/pwndbg/pwndbg
cd pwndbg && ./setup.sh
```

### Setup

1. Clone this repository:
```bash
git clone <your-repo-url>
cd pwn-pipeline
```

2. Make scripts executable:
```bash
chmod +x pwn-pipeline setup.py templates.py analyze.sh
```

3. Create required directories:
```bash
mkdir -p ~/Downloads/ctf
mkdir -p ~/Desktop/Ctf
mkdir -p ~/Desktop/Vault/Ctf
```

---

## Pipeline Options

### Main Pipeline (`pwn-pipeline`)

```bash
# Basic usage
./pwn-pipeline --name challenge_name

# With CTF organization
./pwn-pipeline --name challenge_name --ctf CTF_NAME
./pwn-pipeline --name challenge_name -c CTF_NAME

# Custom archive
./pwn-pipeline --name challenge --archive ~/Downloads/file.zip

# Custom paths
./pwn-pipeline --name challenge --dest ~/CTF --vault-path ~/Vault

# Keep archive
./pwn-pipeline --name challenge --no-cleanup

# Skip phases
./pwn-pipeline --name challenge --skip-analysis
./pwn-pipeline --name challenge --skip-templates

# Verbose output
./pwn-pipeline --name challenge -v

# Combined options
./pwn-pipeline --name challenge --ctf picoCTF2024 --no-cleanup -v
```

### Setup Module (`setup.py`)

```bash
./setup.py --name CHALLENGE_NAME [OPTIONS]

Options:
  --name NAME           Challenge name (required)
  -c, --ctf CTF_NAME    CTF name for organization
  --archive PATH        Specific archive file (optional)
  --dest PATH           Destination directory (default: ~/Desktop/Ctf)
  --no-cleanup          Keep archive after extraction
  -v, --verbose         Verbose logging
```

### Analysis Script (`analyze.sh`)

```bash
./analyze.sh TARGET_DIRECTORY

Arguments:
  TARGET_DIRECTORY      Directory containing challenge files

Examples:
  ./analyze.sh ~/Desktop/Ctf/challenge_name
  ./analyze.sh ~/Desktop/Ctf/picoCTF2024/challenge_name
```

### Templates Module (`templates.py`)

```bash
./templates.py --name CHALLENGE_NAME --challenge-dir PATH [OPTIONS]

Options:
  --name NAME           Challenge name (required)
  -c, --ctf CTF_NAME    CTF name for organization
  --challenge-dir PATH  Challenge directory (required)
  --binary PATH         Path to primary binary (optional)
  --vault-path PATH     Vault base path (default: ~/Desktop/Vault/Ctf)
  -v, --verbose         Verbose logging
```

---

## Configuration

Default paths (defined in `utils.py`):
```python
DOWNLOADS = ~/Downloads/ctf         # Where archives are downloaded
DEST_CTF = ~/Desktop/Ctf            # Where challenges are extracted
VAULT = ~/Desktop/Vault/Ctf         # Where writeups are created
```

Override with command-line arguments:
- `--ctf` / `-c` - CTF name for organization
- `--archive` - Specific archive file
- `--dest` - Challenge destination
- `--vault-path` - Vault location

---

## Tips

1. **Use CTF organization**: Add `--ctf` to keep challenges organized by competition
2. **Start with full pipeline**: Use `./pwn-pipeline` first to see complete automation
3. **Consistent CTF names**: Use the same CTF name for all challenges (e.g., "picoCTF2024")
4. **Use setup.py for extraction**: When you just need files extracted quickly
5. **Re-run analyze.sh**: If you modify the binary or want fresh analysis
6. **Generate templates later**: Use `templates.py` if you forgot to generate them initially
7. **Keep archives**: Use `--no-cleanup` during CTFs to preserve original files
8. **Verbose mode**: Add `-v` when debugging issues
9. **Vault organization**: CTF-organized vault makes writeups easier to find in Obsidian

