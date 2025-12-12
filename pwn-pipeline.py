#!/usr/bin/env python3
"""
Main orchestrator for the pwn CTF automation pipeline.
Coordinates setup, analysis, and template generation.
"""
import argparse
import subprocess
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    logger, setup_logging, check_dependencies,
    DOWNLOADS, DEST_CTF, VAULT, get_script_dir
)
from setup import setup_challenge, cleanup_archive
from templates import generate_all_templates, move_analysis_to_vault


def run_analysis(challenge_dir: Path, script_path: Path) -> bool:
    """
    Run the analysis script on the challenge directory.

    Args:
        challenge_dir: Path to challenge directory
        script_path: Path to analyze.sh script

    Returns:
        True if analysis succeeded, False otherwise
    """
    logger.info("Starting analysis pipeline")

    try:
        result = subprocess.run(
            ["bash", str(script_path), str(challenge_dir)],
            check=True,
            capture_output=True,
            text=True
        )

        if result.stdout:
            logger.debug(f"Analysis output:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"Analysis stderr:\n{result.stderr}")

        logger.info("Analysis complete")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Analysis failed: {e}")
        if e.stdout:
            logger.debug(f"stdout: {e.stdout}")
        if e.stderr:
            logger.debug(f"stderr: {e.stderr}")
        return False


def run_pipeline(challenge_name: str, archive_path: Path = None,
                dest_base: Path = DEST_CTF, vault_path: Path = VAULT,
                ctf_name: str = None, no_cleanup: bool = False,
                skip_analysis: bool = False, skip_templates: bool = False) -> int:
    """
    Run the complete pwn pipeline.

    Args:
        challenge_name: Name of the challenge
        archive_path: Path to archive (if None, finds latest)
        dest_base: Base directory for challenges
        vault_path: Base vault path
        ctf_name: Optional CTF name for organization
        no_cleanup: Don't delete archive after processing
        skip_analysis: Skip binary analysis
        skip_templates: Skip template generation

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    script_dir = get_script_dir()

    try:
        # Phase 1: Setup (extraction and file organization)
        logger.info(f"{'='*60}")
        logger.info(f"PHASE 1: Setup - {challenge_name}")
        if ctf_name:
            logger.info(f"CTF: {ctf_name}")
        logger.info(f"{'='*60}")

        challenge_dir, archive, categorized_files = setup_challenge(
            challenge_name, archive_path, dest_base, ctf_name
        )

        logger.debug(f"Challenge directory: {challenge_dir}")

        # Phase 2: Analysis
        if not skip_analysis:
            logger.info(f"\n{'='*60}")
            logger.info(f"PHASE 2: Binary Analysis")
            logger.info(f"{'='*60}")

            analyze_script = script_dir / "analyze.sh"
            if not analyze_script.exists():
                logger.warning(f"analyze.sh not found at {analyze_script}, skipping analysis")
            else:
                if not run_analysis(challenge_dir, analyze_script):
                    logger.warning("Analysis phase had errors, but continuing...")
        else:
            logger.info("Skipping analysis phase (--skip-analysis)")

        # Phase 3: Template Generation
        if not skip_templates:
            logger.info(f"\n{'='*60}")
            logger.info(f"PHASE 3: Template Generation")
            logger.info(f"{'='*60}")

            # Get primary binary for templates
            primary_binary = None
            if categorized_files["binaries"]:
                primary_binary = categorized_files["binaries"][0]

            templates = generate_all_templates(
                challenge_name,
                challenge_dir,
                primary_binary,
                vault_path,
                ctf_name
            )

            # Move analysis to vault
            move_analysis_to_vault(challenge_dir, challenge_name, vault_path, ctf_name)
        else:
            logger.info("Skipping template generation (--skip-templates)")
            templates = {}

        # Phase 4: Cleanup
        if not no_cleanup:
            logger.info(f"\n{'='*60}")
            logger.info(f"PHASE 4: Cleanup")
            logger.info(f"{'='*60}")
            cleanup_archive(archive)
        else:
            logger.info("\nSkipping cleanup (--no-cleanup)")

        # Final Summary
        print(f"\n{'='*60}")
        print(f"✓ PIPELINE COMPLETE: {challenge_name}")
        print(f"{'='*60}")
        print(f"\nChallenge Setup:")
        print(f"  Directory: {challenge_dir}")
        print(f"  Binaries: {len(categorized_files['binaries'])}")
        print(f"  Libraries: {len(categorized_files['libraries'])}")
        print(f"  Sources: {len(categorized_files['sources'])}")

        if not skip_templates:
            print(f"\nGenerated Files:")
            for name, path in templates.items():
                print(f"  - {name}: {path.name}")

            print(f"\nWriteup Location:")
            print(f"  {vault_path / challenge_name}")

        print(f"\nNext Steps:")
        print(f"  1. Review analysis.md in your vault")
        print(f"  2. Start exploiting with: cd {challenge_dir} && ./exploit.py LOCAL")
        print(f"  3. Debug with: gdb -x .gdbinit ./<binary>")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{'='*60}")
        logger.error(f"✗ PIPELINE FAILED")
        logger.error(f"{'='*60}")
        logger.error(f"Error: {e}")
        logger.error(f"{'='*60}\n")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated CTF pwn challenge pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - process latest archive
  pwn-pipeline --name buffer_overflow

  # Organize by CTF name
  pwn-pipeline --name heap_exploit --ctf picoCTF2024

  # Use specific archive
  pwn-pipeline --name heap_exploit --archive ~/Downloads/ctf/chall.zip

  # Custom vault location
  pwn-pipeline --name rop_chain --vault-path ~/Documents/CTF-Vault/Ctf

  # Keep archive after processing
  pwn-pipeline --name format_string --no-cleanup

  # Skip analysis or templates
  pwn-pipeline --name challenge --skip-analysis
  pwn-pipeline --name challenge --skip-templates

  # Verbose output for debugging
  pwn-pipeline --name challenge -v
        """
    )

    # Required arguments
    parser.add_argument("--name", required=True,
                       help="CTF challenge name")

    # Optional arguments
    parser.add_argument("-c", "--ctf",
                       help="CTF name for organization (creates ~/Desktop/Ctf/{ctf}/{name})")
    parser.add_argument("--archive", type=Path,
                       help="Specific archive to process (default: latest in ~/Downloads/ctf)")
    parser.add_argument("--dest", type=Path, default=DEST_CTF,
                       help=f"Challenge destination directory (default: {DEST_CTF})")
    parser.add_argument("--vault-path", type=Path, default=VAULT,
                       help=f"Obsidian vault path (default: {VAULT})")

    # Flags
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Don't delete archive after processing")
    parser.add_argument("--skip-analysis", action="store_true",
                       help="Skip binary analysis phase")
    parser.add_argument("--skip-templates", action="store_true",
                       help="Skip template generation phase")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Please install missing tools.")
        return 1

    # Run pipeline
    return run_pipeline(
        args.name,
        args.archive,
        args.dest,
        args.vault_path,
        args.ctf,
        args.no_cleanup,
        args.skip_analysis,
        args.skip_templates
    )


if __name__ == "__main__":
    sys.exit(main())
