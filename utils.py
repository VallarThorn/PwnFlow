#!/usr/bin/env python3
"""
Utility functions shared across the pwn pipeline modules.
"""
import logging
import shutil
import sys
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Default paths
DOWNLOADS = Path.home() / "Downloads" / "ctf"
DEST_CTF = Path.home() / "Desktop" / "Ctf"
VAULT = Path.home() / "Desktop" / "Vault" / "Ctf"

# Tool lists
REQUIRED_TOOLS = ["file", "ldd", "strings"]
OPTIONAL_TOOLS = ["pwninit", "pwn", "checksec", "7z", "rabin2", "rizin", "gdb", "readelf", "objdump"]


def setup_logging(verbose: bool = False):
    """Configure logging level."""
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def check_dependencies(required_only: bool = False) -> bool:
    """
    Check if required and optional tools are installed.

    Args:
        required_only: If True, only check required tools

    Returns:
        True if all required dependencies are met
    """
    logger.info("Checking dependencies...")

    missing_required = []
    missing_optional = []

    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            missing_required.append(tool)
        else:
            logger.debug(f"✓ Found {tool}")

    if not required_only:
        for tool in OPTIONAL_TOOLS:
            if shutil.which(tool) is None:
                missing_optional.append(tool)
                logger.debug(f"⚠ Optional tool {tool} not found")
            else:
                logger.debug(f"✓ Found {tool}")

    if missing_required:
        logger.error(f"Missing required tools: {', '.join(missing_required)}")
        logger.error("Install them with: sudo apt install file binutils coreutils")
        return False

    if missing_optional and not required_only:
        logger.warning(f"Missing optional tools (some features will be limited): {', '.join(missing_optional)}")

    logger.info("All required dependencies satisfied")
    return True


def ensure_directories(*paths: Path):
    """Ensure directories exist, create them if they don't."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")


def build_challenge_path(challenge_name: str, ctf_name: str = None, base_path: Path = DEST_CTF) -> Path:
    """
    Build the challenge directory path, optionally with CTF organization.

    Args:
        challenge_name: Name of the challenge
        ctf_name: Optional CTF name for organization
        base_path: Base directory for challenges

    Returns:
        Path to challenge directory
    """
    if ctf_name:
        return base_path / ctf_name / challenge_name
    return base_path / challenge_name


def build_vault_path(challenge_name: str, ctf_name: str = None, base_vault: Path = VAULT) -> Path:
    """
    Build the vault directory path, optionally with CTF organization.

    Args:
        challenge_name: Name of the challenge
        ctf_name: Optional CTF name for organization
        base_vault: Base vault directory

    Returns:
        Path to vault directory
    """
    if ctf_name:
        return base_vault / ctf_name / challenge_name
    return base_vault / challenge_name


def check_directory_exists(path: Path, entity_name: str = "Directory") -> bool:
    """
    Check if a directory exists and warn if it does.

    Args:
        path: Path to check
        entity_name: Name of the entity for logging

    Returns:
        True if directory exists, False otherwise
    """
    if path.exists():
        logger.warning(f"{entity_name} already exists: {path}")
        logger.warning("Existing files may be overwritten")
        return True
    return False


def get_file_info(file_path: Path) -> dict:
    """
    Get basic information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    import os

    stat = file_path.stat()
    return {
        "name": file_path.name,
        "path": file_path,
        "size": stat.st_size,
        "is_executable": os.access(file_path, os.X_OK),
        "suffix": file_path.suffix,
    }


def is_library(file_path: Path) -> bool:
    """Check if a file is a library."""
    name = file_path.name.lower()
    return (
        file_path.suffix == ".so" or
        ".so." in name or
        "libc" in name or
        name.endswith(".a")
    )


def is_linker(file_path: Path) -> bool:
    """Check if a file is a dynamic linker."""
    name = file_path.name
    return "ld-" in name or name.startswith("ld.so")


def is_source(file_path: Path) -> bool:
    """Check if a file is source code."""
    return file_path.suffix in [".c", ".cpp", ".h", ".hpp", ".s", ".asm", ".cc", ".cxx"]


def get_script_dir() -> Path:
    """Get the directory where the scripts are located."""
    return Path(__file__).parent.absolute()
