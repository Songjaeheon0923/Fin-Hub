#!/usr/bin/env python3
"""
Gekko Data Downloader from Google Drive
Downloads Gekko cryptocurrency datasets using gdown library
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Configuration
GEKKO_DATA_DIR = Path(__file__).parent.parent / "data" / "gekko-history"

# Available datasets with Google Drive file IDs
DATASETS = {
    # Recent datasets (lightweight, recommended for testing)
    "binance_30d": {
        "name": "Binance 30 days",
        "folder_id": "1Ghoy6w3BfHNgoRjj5jI9dX1BV0WyS8l_",
        "description": "Recent 30 days from Binance",
        "size": "~100 MB",
        "recommended": True
    },
    "poloniex_30d": {
        "name": "Poloniex 30 days",
        "folder_id": "1Ghoy6w3BfHNgoRjj5jI9dX1BV0WyS8l_",
        "description": "Recent 30 days from Poloniex",
        "size": "~80 MB",
        "recommended": False
    },

    # Full history datasets (large, for production)
    "binance_usdt": {
        "name": "Binance USDT pairs (full history)",
        "folder_id": "1KiYD4jLRwwDkE6GWyQXLz-Lz59H3h_2v",
        "description": "Complete USDT trading pairs from Binance",
        "size": "~3 GB",
        "recommended": False
    },
    "binance_btc": {
        "name": "Binance BTC pairs (full history)",
        "folder_id": "1KiYD4jLRwwDkE6GWyQXLz-Lz59H3h_2v",
        "description": "Complete BTC trading pairs from Binance",
        "size": "~2 GB",
        "recommended": False
    }
}


def check_gdown_installed() -> bool:
    """
    Check if gdown is installed
    Returns: True if installed, False otherwise
    """
    try:
        import gdown
        return True
    except ImportError:
        return False


def install_gdown():
    """
    Install gdown package
    """
    print(f"{Colors.BLUE}[INFO] Installing gdown package...{Colors.RESET}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
        print(f"{Colors.GREEN}[OK] gdown installed successfully{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to install gdown: {e}{Colors.RESET}")
        return False


def list_available_datasets():
    """
    List all available datasets
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}Available Gekko Datasets:{Colors.RESET}\n")

    print(f"{Colors.BOLD}Lightweight (Recommended for testing):{Colors.RESET}")
    for key, dataset in DATASETS.items():
        if dataset.get("recommended"):
            print(f"  {Colors.GREEN}✓ {key}{Colors.RESET}")
            print(f"    Name: {dataset['name']}")
            print(f"    Size: {dataset['size']}")
            print(f"    Description: {dataset['description']}\n")

    print(f"{Colors.BOLD}Full History (For production):{Colors.RESET}")
    for key, dataset in DATASETS.items():
        if not dataset.get("recommended"):
            print(f"  • {key}")
            print(f"    Name: {dataset['name']}")
            print(f"    Size: {dataset['size']}")
            print(f"    Description: {dataset['description']}\n")


def download_from_gdrive_folder(folder_id: str, output_dir: Path):
    """
    Download files from Google Drive folder using gdown
    """
    try:
        import gdown

        print(f"{Colors.BLUE}[INFO] Downloading from Google Drive folder...{Colors.RESET}")
        print(f"{Colors.YELLOW}[WARN] This may take a while depending on file size{Colors.RESET}")

        # Download folder
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

        gdown.download_folder(
            url=folder_url,
            output=str(output_dir),
            quiet=False,
            use_cookies=False
        )

        print(f"{Colors.GREEN}[OK] Download completed!{Colors.RESET}")
        return True

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Download failed: {e}{Colors.RESET}")
        return False


def print_manual_instructions(dataset_key: str):
    """
    Print manual download instructions
    """
    dataset = DATASETS[dataset_key]

    print(f"\n{Colors.BOLD}{Colors.YELLOW}Manual Download Instructions:{Colors.RESET}\n")
    print(f"If automatic download fails, follow these steps:\n")
    print(f"1. Open this link in your browser:")
    print(f"   {Colors.BLUE}https://drive.google.com/drive/folders/{dataset['folder_id']}{Colors.RESET}\n")
    print(f"2. Look for files matching: {Colors.BOLD}{dataset_key}*.zip{Colors.RESET}\n")
    print(f"3. Right-click the file → Download\n")
    print(f"4. Move the downloaded file to:")
    print(f"   {Colors.GREEN}{GEKKO_DATA_DIR}{Colors.RESET}\n")
    print(f"5. Extract the .zip file:")
    print(f"   {Colors.BLUE}unzip {dataset_key}.zip{Colors.RESET}\n")
    print(f"6. You should see .db files like:")
    print(f"   {Colors.GREEN}binance_0.1.db, poloniex_0.1.db, etc.{Colors.RESET}\n")


def main():
    """
    Main function
    """
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Gekko Data Downloader':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    # Create output directory
    GEKKO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{Colors.GREEN}[OK] Output directory: {GEKKO_DATA_DIR}{Colors.RESET}")

    # Check if gdown is installed
    if not check_gdown_installed():
        print(f"{Colors.YELLOW}[WARN] gdown package not found{Colors.RESET}")
        response = input(f"Install gdown now? (y/n): ")
        if response.lower() == 'y':
            if not install_gdown():
                print(f"{Colors.RED}[ERROR] Cannot proceed without gdown{Colors.RESET}")
                sys.exit(1)
        else:
            print(f"{Colors.YELLOW}[INFO] Manual download required{Colors.RESET}")
            list_available_datasets()
            print_manual_instructions("binance_30d")
            sys.exit(0)

    # List available datasets
    list_available_datasets()

    # Get user choice
    print(f"{Colors.BOLD}Choose a dataset to download:{Colors.RESET}")
    print(f"  1. binance_30d (Recommended - Quick test)")
    print(f"  2. binance_usdt (Full history - 3GB)")
    print(f"  3. binance_btc (Full history - 2GB)")
    print(f"  4. Manual download instructions")
    print(f"  5. Exit\n")

    try:
        choice = input(f"{Colors.BOLD}Enter choice (1-5): {Colors.RESET}")
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Colors.YELLOW}[INFO] Cancelled{Colors.RESET}")
        sys.exit(0)

    dataset_map = {
        "1": "binance_30d",
        "2": "binance_usdt",
        "3": "binance_btc"
    }

    if choice == "4":
        print_manual_instructions("binance_30d")
        sys.exit(0)
    elif choice == "5":
        print(f"{Colors.YELLOW}[INFO] Exiting{Colors.RESET}")
        sys.exit(0)
    elif choice in dataset_map:
        dataset_key = dataset_map[choice]
        dataset = DATASETS[dataset_key]

        print(f"\n{Colors.BLUE}[INFO] Selected: {dataset['name']}{Colors.RESET}")
        print(f"{Colors.YELLOW}[WARN] Size: {dataset['size']}{Colors.RESET}")

        # Confirm
        try:
            confirm = input(f"\nProceed with download? (y/n): ")
            if confirm.lower() != 'y':
                print(f"{Colors.YELLOW}[INFO] Download cancelled{Colors.RESET}")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}[INFO] Cancelled{Colors.RESET}")
            sys.exit(0)

        # Download
        success = download_from_gdrive_folder(dataset['folder_id'], GEKKO_DATA_DIR)

        if success:
            print(f"\n{Colors.GREEN}[OK] Download completed!{Colors.RESET}")
            print(f"\n{Colors.BOLD}Next steps:{Colors.RESET}")
            print(f"1. Check downloaded files:")
            print(f"   {Colors.BLUE}ls -lh {GEKKO_DATA_DIR}/*.db{Colors.RESET}")
            print(f"\n2. Verify data:")
            print(f"   {Colors.BLUE}python scripts/gekko_data_integration.py{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}[ERROR] Automatic download failed{Colors.RESET}")
            print_manual_instructions(dataset_key)
    else:
        print(f"{Colors.RED}[ERROR] Invalid choice{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
