#!/usr/bin/env python3
"""
Utility functions shared across the pwn pipeline modules.
"""
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class PathConfig:
    """Configuration for paths used in the pipeline."""
    _instance = None
    
    def __init__(self):
        self._downloads = None
        self._dest_ctf = None
        self._vault = None
        
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = PathConfig()
            # Default configuration (non-debug)
            cls._instance.configure()
        return cls._instance
        
    def configure(self, debug: bool = False):
        """
        Configure paths based on debug mode and environment variables.
        
        Args:
            debug: If True, use test environment variables and paths.
        """
        if debug:
            self._downloads = Path(os.getenv("PWN_TEST_DOWNLOADS", "/tmp/pwnflow/downloads"))
            self._dest_ctf = Path(os.getenv("PWN_TEST_DEST", "/tmp/pwnflow/ctf"))
            self._vault = Path(os.getenv("PWN_TEST_VAULT", "/tmp/pwnflow/vault"))
            logger.debug(f"Configured in DEBUG mode: {self._dest_ctf}")
        else:
            self._downloads = Path(os.getenv("PWN_DOWNLOADS", "~/Downloads/ctf")).expanduser()
            self._dest_ctf = Path(os.getenv("PWN_DEST", "~/Desktop/Ctf")).expanduser()
            self._vault = Path(os.getenv("PWN_VAULT", "~/Desktop/Vault/Ctf")).expanduser()
            
    @property
    def downloads(self) -> Path:
        return self._downloads
        
    @property
    def dest(self) -> Path:
        return self._dest_ctf
        
    @property
    def vault(self) -> Path:
        return self._vault


# Helper functions to access config
def configure_paths(debug: bool = False):
    """Configure the global path configuration."""
    PathConfig.get().configure(debug)

def get_downloads_dir() -> Path:
    return PathConfig.get().downloads

def get_dest_dir() -> Path:
    return PathConfig.get().dest

def get_vault_dir() -> Path:
    return PathConfig.get().vault


# Tool lists
REQUIRED_TOOLS = ["file", "ldd", "strings"]
OPTIONAL_TOOLS = ["pwninit", "pwn", "checksec", "7z", "rabin2", "rizin", "gdb", "readelf", "objdump"]


class ColorFormatter(logging.Formatter):
    """Custom formatter with color support."""
    
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMAT_STR = "[%(levelname)s] %(message)s"

    FORMATS = {
        logging.DEBUG: grey + FORMAT_STR + reset,
        logging.INFO: blue + FORMAT_STR + reset,
        logging.WARNING: yellow + FORMAT_STR + reset,
        logging.ERROR: red + FORMAT_STR + reset,
        logging.CRITICAL: bold_red + FORMAT_STR + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(verbose: bool = False):
    """Configure logging with color and level."""
    # Remove existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
            
    # Create handler with color formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter())
    
    # Configure logger
    logger.handlers = []
    logger.addHandler(handler)
    
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


def build_challenge_path(challenge_name: str, ctf_name: str = None, base_path: Path = None) -> Path:
    """
    Build the challenge directory path, optionally with CTF organization.

    Args:
        challenge_name: Name of the challenge
        ctf_name: Optional CTF name for organization
        base_path: Base directory for challenges (defaults to config)

    Returns:
        Path to challenge directory
    """
    if base_path is None:
        base_path = get_dest_dir()
        
    if ctf_name:
        return base_path / ctf_name / challenge_name
    return base_path / challenge_name


def build_vault_path(challenge_name: str, ctf_name: str = None, base_vault: Path = None) -> Path:
    """
    Build the vault directory path, optionally with CTF organization.

    Args:
        challenge_name: Name of the challenge
        ctf_name: Optional CTF name for organization
        base_vault: Base vault directory (defaults to config)

    Returns:
        Path to vault directory
    """
    if base_vault is None:
        base_vault = get_vault_dir()

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
