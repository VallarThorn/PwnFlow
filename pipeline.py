#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import pathlib
import tarfile
import zipfile

DOWNLOADS = pathlib.Path.home() / "Downloads" / "ctf"
DEST_CTF = pathlib.Path.home() / "Desktop" / "Ctf"
VAULT = pathlib.Path("~/Desktop/Vault/Ctf")


def extract_archive(archive_path: pathlib.Path, dest_dir: pathlib.Path):
    dest_dir.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(dest_dir)
        return

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as t:
            t.extractall(dest_dir)
        return

    # fallback to 7z
    subprocess.run(["7z", "x", str(archive_path), f"-o{dest_dir}"], check=True)


def copy_template(ctf_name: str):
    vault_path = VAULT / ctf_name
    vault_path.mkdir(parents=True, exist_ok=True)

    template_src = pathlib.Path("templates/writeup_template.md")
    template_dst = vault_path / f"{ctf_name}.md"

    shutil.copy(template_src, template_dst)
    return template_dst


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="CTF challenge name")
    args = parser.parse_args()

    ctf = args.name
    archive = None

    # 1. Locate archive in ~/Downloads/ctf
    for ext in ["zip", "tar", "tar.gz", "tgz", "7z"]:
        candidate = DOWNLOADS / f"{ctf}.{ext}"
        if candidate.exists():
            archive = candidate
            break

    if archive is None:
        raise FileNotFoundError(f"No archive found in {DOWNLOADS} for name {ctf}")

    # 2. Extract to ~/Desktop/Ctf/ctf_name/
    dest = DEST_CTF / ctf
    extract_archive(archive, dest)

    # 3. Run analysis
    subprocess.run(["bash", "analyze.sh", str(dest)], check=True)

    # 4. Move analysis.md into Obsidian vault
    vault_writeup = copy_template(ctf)
    shutil.move(dest / "analysis.md", vault_writeup.parent / "analysis.md")

    print(f"[OK] Pipeline complete for {ctf}")


if __name__ == "__main__":
    main()

