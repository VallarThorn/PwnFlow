#!/usr/bin/env python3
"""
Setup module for pwn pipeline.
Handles archive extraction, directory creation, and file categorization.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List

from utils import (
    logger, setup_logging, ensure_directories,
    get_downloads_dir, get_dest_dir, configure_paths,
    is_library, is_linker, is_source, get_file_info,
    build_challenge_path, check_directory_exists
)


def find_latest_archive(downloads_dir: Path = None) -> Path:
    """
    Find the most recently modified archive in the downloads directory.

    Args:
        downloads_dir: Directory to search for archives (default: configured downloads)

    Returns:
        Path to the most recent archive

    Raises:
        FileNotFoundError: If no archives found or directory doesn't exist
    """
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()

    if not downloads_dir.exists():
        raise FileNotFoundError(f"Downloads directory does not exist: {downloads_dir}")

    archives = [
        p for p in downloads_dir.iterdir()
        if p.is_file() and (
            p.suffix in [".zip", ".tar", ".gz", ".tgz", ".7z", ".bz2", ".xz", ".rar"]
            or p.name.endswith((".tar.gz", ".tar.xz", ".tar.bz2"))
        )
    ]

    if not archives:
        raise FileNotFoundError(f"No archives found in {downloads_dir}")

    archive = max(archives, key=lambda p: p.stat().st_mtime)
    logger.info(f"Selected archive: {archive.name}")
    return archive


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """
    Extract archive to destination directory.

    Args:
        archive_path: Path to the archive file
        dest_dir: Destination directory for extraction

    Raises:
        RuntimeError: If extraction fails
    """
    logger.info(f"Extracting {archive_path.name} to {dest_dir}")
    ensure_directories(dest_dir)

    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(dest_dir)
            logger.info("Successfully extracted ZIP archive")
            return

        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as t:
                t.extractall(dest_dir)
            logger.info("Successfully extracted TAR archive")
            return

        # Fallback to 7z if available
        if shutil.which("7z"):
            result = subprocess.run(
                ["7z", "x", str(archive_path), f"-o{dest_dir}"],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Successfully extracted with 7z")
            return
        else:
            raise RuntimeError("Archive format not supported and 7z not available")

    except Exception as e:
        logger.error(f"Failed to extract archive: {e}")
        raise


def get_file_type(file_path: Path) -> str:
    """
    Get file type using the 'file' command.

    Args:
        file_path: Path to the file

    Returns:
        File type string, or empty string if detection fails
    """
    try:
        result = subprocess.run(
            ["file", "-b", str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip().lower()
    except Exception as e:
        logger.debug(f"Failed to detect file type for {file_path.name}: {e}")
        return ""


def is_elf_binary(file_path: Path, file_type: str = None) -> bool:
    """
    Check if file is an ELF executable binary.

    Args:
        file_path: Path to the file
        file_type: Optional pre-fetched file type string

    Returns:
        True if file is an ELF executable
    """
    if file_type is None:
        file_type = get_file_type(file_path)

    # Check for ELF executable indicators
    if not file_type:
        return False

    # ELF executable (not shared object or relocatable)
    is_elf = "elf" in file_type
    is_executable = "executable" in file_type
    is_not_shared = "shared object" not in file_type

    return is_elf and is_executable and is_not_shared


def is_elf_library(file_path: Path, file_type: str = None) -> bool:
    """
    Check if file is an ELF shared library.

    Args:
        file_path: Path to the file
        file_type: Optional pre-fetched file type string

    Returns:
        True if file is an ELF shared library
    """
    if file_type is None:
        file_type = get_file_type(file_path)

    if not file_type:
        return False

    # Check both file command output and filename
    is_shared = "shared object" in file_type or "elf" in file_type
    has_so_extension = ".so" in file_path.name or file_path.suffix == ".so"

    return is_shared and has_so_extension


def is_elf_linker(file_path: Path, file_type: str = None) -> bool:
    """
    Check if file is a dynamic linker.

    Args:
        file_path: Path to the file
        file_type: Optional pre-fetched file type string

    Returns:
        True if file is a dynamic linker
    """
    name = file_path.name.lower()

    # Common linker names
    linker_patterns = ["ld-", "ld.so", "ld-linux"]

    return any(pattern in name for pattern in linker_patterns)


def categorize_files(directory: Path) -> Dict[str, List[Path]]:
    """
    Scan directory and categorize all relevant files using advanced detection.

    Uses the 'file' command to accurately detect ELF binaries, libraries,
    and other file types, even if they're not marked executable.

    Args:
        directory: Directory to scan

    Returns:
        Dictionary with categorized file lists
    """
    logger.info(f"Scanning directory for files: {directory}")

    files = {
        "binaries": [],
        "libraries": [],
        "linkers": [],
        "sources": [],
        "other": []
    }

    for item in directory.rglob("*"):
        if not item.is_file():
            continue

        # Skip hidden files and common non-binary files
        if item.name.startswith('.') and item.name not in ['.gdbinit']:
            continue

        # Get file type once for efficiency
        file_type = get_file_type(item)

        # Check for source files first (quick check)
        if is_source(item):
            files["sources"].append(item)
            logger.info(f"Found source: {item.name}")
            continue

        # Check for linker (highest priority for ELF files)
        if is_elf_linker(item, file_type):
            files["linkers"].append(item)
            logger.info(f"Found linker: {item.name}")
            continue

        # Check for ELF executable (using file command)
        if is_elf_binary(item, file_type):
            # Ensure binary is executable
            if not os.access(item, os.X_OK):
                try:
                    item.chmod(item.stat().st_mode | 0o111)
                    logger.info(f"Made executable: {item.name}")
                except Exception as e:
                    logger.warning(f"Failed to make {item.name} executable: {e}")

            files["binaries"].append(item)
            logger.info(f"Found binary: {item.name} (ELF executable)")
            continue

        # Check for ELF shared library
        if is_elf_library(item, file_type):
            files["libraries"].append(item)
            logger.info(f"Found library: {item.name} (ELF shared object)")
            continue

        # Fallback: check by executable bit and name patterns
        # This handles cases where 'file' command might fail
        if os.access(item, os.X_OK):
            if is_linker(item):
                files["linkers"].append(item)
                logger.info(f"Found linker: {item.name} (by name pattern)")
            elif is_library(item):
                files["libraries"].append(item)
                logger.info(f"Found library: {item.name} (by name pattern)")
            else:
                # Executable but not detected as ELF - still consider it binary
                files["binaries"].append(item)
                logger.info(f"Found binary: {item.name} (executable, type: {file_type[:50]})")
            continue

        # Final fallback: check library by name only
        if is_library(item):
            files["libraries"].append(item)
            logger.info(f"Found library: {item.name} (by extension)")
            continue

        # Everything else
        files["other"].append(item)
        logger.debug(f"Other file: {item.name} (type: {file_type[:50] if file_type else 'unknown'})")

    logger.info(f"Scan complete: {len(files['binaries'])} binaries, "
                f"{len(files['libraries'])} libraries, "
                f"{len(files['linkers'])} linkers, "
                f"{len(files['sources'])} sources")

    return files


def setup_challenge(challenge_name: str, archive_path: Path = None,
                   dest_base: Path = None, ctf_name: str = None) -> tuple:
    """
    Set up challenge directory and extract files.

    Args:
        challenge_name: Name of the challenge
        archive_path: Path to archive (if None, will find latest)
        dest_base: Base directory for challenges (defaults to config)
        ctf_name: Optional CTF name for organization

    Returns:
        Tuple of (challenge_dir, archive_path, categorized_files)
    """
    # Find archive if not provided
    if archive_path is None:
        archive_path = find_latest_archive()

    # Build challenge directory path
    challenge_dir = build_challenge_path(challenge_name, ctf_name, dest_base)

    # Check if directory already exists
    check_directory_exists(challenge_dir, "Challenge directory")

    # Extract archive
    extract_archive(archive_path, challenge_dir)

    # Categorize files
    categorized_files = categorize_files(challenge_dir)

    if not categorized_files["binaries"]:
        logger.warning("No executable binaries found in archive")

    logger.info(f"Challenge setup complete: {challenge_dir}")
    return challenge_dir, archive_path, categorized_files


def cleanup_archive(archive_path: Path) -> None:
    """
    Remove the processed archive from downloads.

    Args:
        archive_path: Path to the archive to remove
    """
    try:
        logger.info(f"Cleaning up: removing {archive_path.name}")
        archive_path.unlink()
        logger.info("Cleanup complete")
    except Exception as e:
        logger.warning(f"Failed to cleanup archive: {e}")


def main():
    """Main entry point for setup script."""
    parser = argparse.ArgumentParser(
        description="CTF challenge setup - extraction and file organization",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--name", required=True, help="CTF challenge name")
    parser.add_argument("-c", "--ctf", help="CTF name for organization (creates ~/Desktop/Ctf/{ctf}/{name})")
    parser.add_argument("--archive", type=Path, help="Specific archive to extract (optional)")
    parser.add_argument("--dest", type=Path,
                       help="Base destination directory (defaults to config)")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Don't delete archive after extraction")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode (use test paths)")
    args = parser.parse_args()

    setup_logging(args.verbose)
    configure_paths(args.debug)

    try:
        # Setup challenge
        challenge_dir, archive_path, files = setup_challenge(
            args.name,
            args.archive,
            args.dest,
            args.ctf
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"Setup Complete: {args.name}")
        print(f"{'='*60}")
        print(f"Challenge directory: {challenge_dir}")
        print(f"Files found:")
        print(f"  - Binaries: {len(files['binaries'])}")
        print(f"  - Libraries: {len(files['libraries'])}")
        print(f"  - Linkers: {len(files['linkers'])}")
        print(f"  - Sources: {len(files['sources'])}")
        print(f"  - Other: {len(files['other'])}")
        print(f"{'='*60}\n")

        # Cleanup
        if not args.no_cleanup:
            cleanup_archive(archive_path)

        return 0

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
