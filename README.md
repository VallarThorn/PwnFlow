# Pwn Pipeline

This project provides a minimal automation pipeline for preparing CTF pwn challenges. It extracts downloaded archives, organizes each challenge into a consistent directory structure, runs a basic analysis pipeline (pwninit, file, ldd, strings, checksec), and generates a writeup template inside an Obsidian vault. The goal is to streamline the initial setup process so you can focus directly on exploitation and analysis.

## Structure

ctf-pipeline/
├── pipeline.py          # Extraction, templating, and orchestration
├── analyze.sh           # Runs analysis tools and writes analysis.md
└── templates/
    └── writeup\_template.md

