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

- [ ] Create solve templates inside the challenge dir
- [ ] Libc version detection: Auto-download matching libc, find one-gadgets
- [ ] Auto generate exploit hints
- [ ] Vulnerability pattern detection

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

### 1. `pwn-pipeline` - Main Orchestrator ⚙️

**Purpose:** Coordinates all pipeline phases in sequence

**Functionality:**
- Runs the complete CTF setup workflow
- Calls `setup.py` → `analyze.sh` → `templates.py` in order
- Manages phase control (skip analysis/templates)
- Supports CTF-based organization
- Provides unified CLI and logging
- Handles errors across all phases

**Can run independently:** ✅ Yes (this is the main entry point)

**Usage:**
```bash
./pwn-pipeline --name challenge_name [options]

# With CTF organization
./pwn-pipeline --name heap_overflow --ctf picoCTF2024
```

---

### 2. `setup.py` - Extraction & Organization 📦

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

**Can run independently:** ✅ Yes

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

### 3. `analyze.sh` - Binary Analysis 🔍

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

**Can run independently:** ✅ Yes

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

### 4. `templates.py` - Template Generation 📝

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

**Can run independently:** ✅ Yes

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

**Can run independently:** ❌ No (this is a library module)

**Usage:**
```python
# Import in other modules
from utils import logger, check_dependencies, ensure_directories
from utils import build_challenge_path, build_vault_path
```

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

## CTF Organization

The pipeline supports organizing challenges by CTF name using the `--ctf` or `-c` argument.

### Without CTF Organization (Default)
```bash
./pwn-pipeline --name buffer_overflow

# Creates:
~/Desktop/Ctf/buffer_overflow/
~/Desktop/Vault/Ctf/buffer_overflow/
```

### With CTF Organization
```bash
./pwn-pipeline --name buffer_overflow --ctf picoCTF2024

# Creates:
~/Desktop/Ctf/picoCTF2024/buffer_overflow/
~/Desktop/Vault/Ctf/picoCTF2024/buffer_overflow/
```

### Benefits of CTF Organization
- **Grouped Challenges**: All challenges from the same CTF in one folder
- **Easy Navigation**: Find challenges by CTF name
- **Clean Structure**: Separate different CTFs cleanly
- **Vault Organization**: Writeups organized by CTF in Obsidian

### Example: Multiple Challenges from Same CTF
```bash
# Process multiple challenges from DEFCON31
./pwn-pipeline --name pwn1 --ctf DEFCON31
./pwn-pipeline --name pwn2 --ctf DEFCON31
./pwn-pipeline --name pwn3 --ctf DEFCON31

# Results in:
~/Desktop/Ctf/DEFCON31/
  ├── pwn1/
  ├── pwn2/
  └── pwn3/

~/Desktop/Vault/Ctf/DEFCON31/
  ├── pwn1/
  ├── pwn2/
  └── pwn3/
```

---

## Usage Scenarios

### Scenario 1: Full Automated Pipeline

**Use Case:** You want complete automation from archive to exploit template

```bash
# 1. Download challenge to ~/Downloads/ctf/
# 2. Run full pipeline
./pwn-pipeline --name heap_overflow

# Or with CTF organization
./pwn-pipeline --name heap_overflow --ctf picoCTF2024

# What happens:
# ✓ Extracts archive
# ✓ Organizes files
# ✓ Runs analysis
# ✓ Generates templates
# ✓ Creates writeup
# ✓ Cleans up archive
```

**Result:**
- `~/Desktop/Ctf/[ctf/]heap_overflow/` - Challenge files + templates
- `~/Desktop/Vault/Ctf/[ctf/]heap_overflow/` - Writeup + analysis

---

### Scenario 2: Setup Only (Manual Analysis)

**Use Case:** You want to extract and organize files, but do your own analysis

```bash
# Extract and organize only
./setup.py --name buffer_overflow --no-cleanup

# With CTF organization
./setup.py --name buffer_overflow --ctf CSAW2024 --no-cleanup

# What happens:
# ✓ Extracts archive
# ✓ Organizes files
# ✗ No analysis
# ✗ No templates
```

**Result:**
- `~/Desktop/Ctf/[ctf/]buffer_overflow/` - Organized challenge files
- Original archive kept in `~/Downloads/ctf/`

---

### Scenario 3: Analysis Only (Re-analyze)

**Use Case:** You already have the files, just want to run analysis again

```bash
# Run analysis on existing directory
./analyze.sh ~/Desktop/Ctf/existing_challenge

# Or with CTF organization
./analyze.sh ~/Desktop/Ctf/picoCTF2024/existing_challenge

# What happens:
# ✓ Analyzes all binaries
# ✓ Creates analysis.md
```

**Result:**
- `analysis.md` in the target directory - Fresh analysis report

---

### Scenario 4: Templates Only (Late Generation)

**Use Case:** You set up the challenge earlier, now want templates

```bash
# Generate templates for existing challenge
./templates.py --name rop_chain \
               --challenge-dir ~/Desktop/Ctf/rop_chain \
               --binary ~/Desktop/Ctf/rop_chain/rop_chain

# With CTF organization
./templates.py --name rop_chain --ctf HackTheBox \
               --challenge-dir ~/Desktop/Ctf/HackTheBox/rop_chain \
               --binary ~/Desktop/Ctf/HackTheBox/rop_chain/rop_chain

# What happens:
# ✓ Generates exploit.py
# ✓ Generates .gdbinit
# ✓ Generates solve.sh
# ✓ Creates writeup template
# ✓ Moves analysis.md to vault (if exists)
```

**Result:**
- Templates in challenge directory
- Writeup in vault (organized by CTF if specified)

---

### Scenario 5: Custom Workflow

**Use Case:** Mix and match components for your workflow

```bash
# 1. Setup with specific archive and CTF organization
./setup.py --name custom_challenge --ctf DEFCON31 \
           --archive ~/Downloads/special.tar.gz \
           --no-cleanup

# 2. Analyze
./analyze.sh ~/Desktop/Ctf/DEFCON31/custom_challenge

# 3. Generate templates later
./templates.py --name custom_challenge --ctf DEFCON31 \
               --challenge-dir ~/Desktop/Ctf/DEFCON31/custom_challenge \
               --binary ~/Desktop/Ctf/DEFCON31/custom_challenge/bin \
               --vault-path ~/Documents/MyVault/CTF
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

## Generated Files

### Without CTF Organization

```
~/Desktop/Ctf/challenge_name/
├── binary                   # The main binary
├── libc.so.6                # Provided libc (if any)
├── ld-2.31.so               # Provided linker (if any)
├── exploit.py               # Pwntools exploit template
├── solve.sh                 # Quick solve script
└── .gdbinit                 # GDB initialization

~/Desktop/Vault/Ctf/challenge_name/
├── challenge_name.md        # Writeup template
└── analysis.md              # Binary analysis report
```

### With CTF Organization

```
~/Desktop/Ctf/picoCTF2024/challenge_name/
├── binary                   # The main binary
├── libc.so.6                # Provided libc (if any)
├── ld-2.31.so               # Provided linker (if any)
├── exploit.py               # Pwntools exploit template
├── solve.sh                 # Quick solve script
└── .gdbinit                 # GDB initialization

~/Desktop/Vault/Ctf/picoCTF2024/challenge_name/
├── challenge_name.md        # Writeup template
└── analysis.md              # Binary analysis report
```

### exploit.py
```bash
# Run locally
./exploit.py LOCAL

# Run with GDB
./exploit.py LOCAL GDB

# Run remotely
./exploit.py HOST=ctf.example.com PORT=1337
```

### solve.sh
```bash
./solve.sh local     # Quick local run
./solve.sh remote    # Quick remote run (edit script for host/port)
```

### .gdbinit
```bash
gdb -x .gdbinit ./binary
```

---

## Python API

You can also import and use the modules programmatically:

```python
from setup import setup_challenge, cleanup_archive
from templates import generate_all_templates
from utils import check_dependencies, logger, build_challenge_path

# Check dependencies
if not check_dependencies():
    print("Missing dependencies!")
    exit(1)

# Setup challenge with CTF organization
challenge_dir, archive, files = setup_challenge(
    challenge_name="my_challenge",
    archive_path=None,  # None = find latest
    dest_base=Path("~/Desktop/Ctf"),
    ctf_name="DEFCON31"  # Optional CTF organization
)

print(f"Found {len(files['binaries'])} binaries")
print(f"Challenge directory: {challenge_dir}")

# Generate templates with CTF organization
if files['binaries']:
    templates = generate_all_templates(
        challenge_name="my_challenge",
        challenge_dir=challenge_dir,
        binary_path=files['binaries'][0],
        vault_path=Path("~/Desktop/Vault/Ctf"),
        ctf_name="DEFCON31"  # Optional CTF organization
    )

# Cleanup
cleanup_archive(archive)
```

---

## Workflow Examples

### Example 1: Quick CTF Challenge Setup

```bash
# Download challenge.zip to ~/Downloads/ctf/
# Run pipeline with CTF organization
./pwn-pipeline --name quick_challenge --ctf picoCTF2024

# Start working
cd ~/Desktop/Ctf/picoCTF2024/quick_challenge
cat ~/Desktop/Vault/Ctf/picoCTF2024/quick_challenge/analysis.md
./exploit.py LOCAL
```

### Example 2: Manual Control with CTF Organization

```bash
# Step 1: Extract only
./setup.py --name manual_challenge --ctf CSAW2024 --no-cleanup

# Step 2: Review files manually
ls ~/Desktop/Ctf/CSAW2024/manual_challenge

# Step 3: Run analysis when ready
./analyze.sh ~/Desktop/Ctf/CSAW2024/manual_challenge

# Step 4: Review analysis
cat ~/Desktop/Ctf/CSAW2024/manual_challenge/analysis.md

# Step 5: Generate templates
./templates.py --name manual_challenge --ctf CSAW2024 \
               --challenge-dir ~/Desktop/Ctf/CSAW2024/manual_challenge \
               --binary ~/Desktop/Ctf/CSAW2024/manual_challenge/chall
```

### Example 3: Organize Existing CTF

```bash
# You're competing in DEFCON31, multiple challenges
./pwn-pipeline --name pwn1 --ctf DEFCON31
./pwn-pipeline --name pwn2 --ctf DEFCON31
./pwn-pipeline --name pwn3 --ctf DEFCON31
./pwn-pipeline --name pwn4 --ctf DEFCON31

# All organized under:
# ~/Desktop/Ctf/DEFCON31/
# ~/Desktop/Vault/Ctf/DEFCON31/
```

### Example 4: Re-analyze Existing Challenge

```bash
# Already have files, just need fresh analysis
./analyze.sh ~/Desktop/Ctf/old_challenge

# Or with CTF organization
./analyze.sh ~/Desktop/Ctf/picoCTF2023/old_challenge

# Generate new templates
./templates.py --name old_challenge --ctf picoCTF2023 \
               --challenge-dir ~/Desktop/Ctf/picoCTF2023/old_challenge \
               --binary ~/Desktop/Ctf/picoCTF2023/old_challenge/binary
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

## Troubleshooting

### Module Import Errors

If you get import errors when running individual modules:
```bash
# Make sure you're in the pwn-pipeline directory
cd /path/to/pwn-pipeline

# Run scripts from here
./setup.py --name challenge
```

Or add to PYTHONPATH:
```bash
export PYTHONPATH="/path/to/pwn-pipeline:$PYTHONPATH"
```

### Missing Dependencies

The pipeline checks dependencies on startup:
```bash
./pwn-pipeline --name test
# [ERROR] Missing required tools: file, ldd
# [ERROR] Install them with: sudo apt install file binutils
```

### No Archive Found

```bash
./setup.py --name challenge
# [ERROR] No archives found in /home/user/Downloads/ctf
```

Solution: Place your .zip/.tar.gz file in `~/Downloads/ctf/`

### Directory Already Exists

```bash
./setup.py --name challenge --ctf picoCTF2024
# [WARNING] Challenge directory already exists: ~/Desktop/Ctf/picoCTF2024/challenge
# [WARNING] Existing files may be overwritten
```

The pipeline warns you but continues. Files may be overwritten.

### Permission Denied

```bash
chmod +x pwn-pipeline setup.py templates.py analyze.sh
```

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

---

## Development

To extend the pipeline:

1. **Add analysis tools**: Edit `analyze.sh` to include new analysis commands
2. **Add template types**: Edit `templates.py` to create new templates
3. **Add utilities**: Edit `utils.py` for shared functions
4. **Modify workflow**: Edit `pwn-pipeline` to change orchestration

All modules follow a consistent pattern:
- CLI with argparse
- Logging via `utils.logger`
- Return values for programmatic use
- Can run independently
- Support CTF organization via `--ctf` argument

---

## Contributing

Feel free to submit issues or pull requests!

## License

MIT License
