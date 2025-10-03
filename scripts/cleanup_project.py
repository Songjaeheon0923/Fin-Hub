#!/usr/bin/env python3
"""
Fin-Hub Project Cleanup Script
Removes unnecessary files and directories
"""

import os
import shutil
from pathlib import Path

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

PROJECT_ROOT = Path(__file__).parent.parent

# Items to remove
CLEANUP_ITEMS = {
    "directories": [
        "shared;C",  # Duplicate/corrupted directory
        "documentation",  # Empty directory
        "examples",  # Empty directory
        "tools",  # Empty directory
        "data/fred-cache",  # Empty cache directory
    ],
    "files": [
        "services/market-spoke/app/__pycache__/__init__.cpython-313.pyc",
        "services/market-spoke/app/clients/__pycache__/unified_api_manager.cpython-313.pyc",
        "data/finnhub_test_data.json",  # Old test data
    ],
    "optional_large": [
        "data/Gekko-Datasets",  # 157K - Contains only scripts, no actual data
    ]
}


def cleanup_directories():
    """Remove unnecessary directories"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Cleaning up directories...{Colors.RESET}")

    removed_count = 0
    for dir_path in CLEANUP_ITEMS["directories"]:
        full_path = PROJECT_ROOT / dir_path

        if full_path.exists():
            try:
                shutil.rmtree(full_path)
                print(f"{Colors.GREEN}[REMOVED]{Colors.RESET} {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to remove {dir_path}: {e}")
        else:
            print(f"{Colors.YELLOW}[SKIP]{Colors.RESET} {dir_path} (not found)")

    return removed_count


def cleanup_files():
    """Remove unnecessary files"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Cleaning up files...{Colors.RESET}")

    removed_count = 0
    for file_path in CLEANUP_ITEMS["files"]:
        full_path = PROJECT_ROOT / file_path

        if full_path.exists():
            try:
                full_path.unlink()
                print(f"{Colors.GREEN}[REMOVED]{Colors.RESET} {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to remove {file_path}: {e}")
        else:
            print(f"{Colors.YELLOW}[SKIP]{Colors.RESET} {file_path} (not found)")

    return removed_count


def cleanup_pycache():
    """Remove all __pycache__ directories"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Cleaning up __pycache__ directories...{Colors.RESET}")

    removed_count = 0
    for pycache_dir in PROJECT_ROOT.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            print(f"{Colors.GREEN}[REMOVED]{Colors.RESET} {pycache_dir.relative_to(PROJECT_ROOT)}")
            removed_count += 1
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to remove {pycache_dir}: {e}")

    return removed_count


def show_optional_cleanup():
    """Show optional large items that can be removed"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Optional cleanup (large items):{Colors.RESET}")

    for item_path in CLEANUP_ITEMS["optional_large"]:
        full_path = PROJECT_ROOT / item_path

        if full_path.exists():
            if full_path.is_dir():
                size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            else:
                size = full_path.stat().st_size
                size_str = f"{size / 1024:.1f} KB"

            print(f"  {Colors.CYAN}[OPTIONAL]{Colors.RESET} {item_path} ({size_str})")
            print(f"    Reason: Contains only Gekko scripts, no actual database files")
            print(f"    To remove: rm -rf \"{full_path}\"")


def create_gitignore_additions():
    """Add recommended .gitignore entries"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Checking .gitignore...{Colors.RESET}")

    gitignore_path = PROJECT_ROOT / ".gitignore"

    recommended_entries = [
        "# Python cache",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        "",
        "# Cache directories",
        "*-cache/",
        "*.cache",
        "",
        "# Test data",
        "*_test_data.json",
        "",
        "# Logs",
        "*.log",
        "logs/",
    ]

    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            current_content = f.read()

        # Check if entries already exist
        missing_entries = [entry for entry in recommended_entries if entry not in current_content]

        if missing_entries:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Some recommended .gitignore entries are missing")
            print(f"  Run this script with --update-gitignore to add them")
        else:
            print(f"{Colors.GREEN}[OK]{Colors.RESET} .gitignore is up to date")
    else:
        print(f"{Colors.YELLOW}[WARN]{Colors.RESET} .gitignore not found")


def print_summary(dir_count, file_count, pycache_count):
    """Print cleanup summary"""
    total = dir_count + file_count + pycache_count

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Cleanup Summary':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    print(f"  {Colors.GREEN}Directories removed: {dir_count}{Colors.RESET}")
    print(f"  {Colors.GREEN}Files removed: {file_count}{Colors.RESET}")
    print(f"  {Colors.GREEN}__pycache__ removed: {pycache_count}{Colors.RESET}")
    print(f"\n  {Colors.BOLD}Total items removed: {total}{Colors.RESET}")

    if total > 0:
        print(f"\n{Colors.GREEN}[OK] Cleanup completed successfully!{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}[INFO] Nothing to clean up{Colors.RESET}")


def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Fin-Hub Project Cleanup':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")

    # Cleanup
    dir_count = cleanup_directories()
    file_count = cleanup_files()
    pycache_count = cleanup_pycache()

    # Optional items
    show_optional_cleanup()

    # Check .gitignore
    create_gitignore_additions()

    # Summary
    print_summary(dir_count, file_count, pycache_count)


if __name__ == "__main__":
    main()
