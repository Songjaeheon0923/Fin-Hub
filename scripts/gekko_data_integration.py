#!/usr/bin/env python3
"""
Gekko Cryptocurrency Data Integration for Fin-Hub
Integrates Gekko SQLite databases into Fin-Hub's data infrastructure
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Configuration
GEKKO_DATA_DIR = Path(__file__).parent.parent / "data" / "gekko-history"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "crypto-cache"
METADATA_FILE = OUTPUT_DIR / "_gekko_metadata.json"

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class GekkoDataIntegration:
    """Main class for integrating Gekko data"""

    def __init__(self):
        self.databases = []
        self.metadata = {
            "last_scan": None,
            "databases": [],
            "total_pairs": 0,
            "total_candles": 0
        }

    def scan_databases(self) -> List[Path]:
        """
        Scan for Gekko database files
        Returns: List of database file paths
        """
        print(f"{Colors.BLUE}[INFO] Scanning for Gekko databases...{Colors.RESET}")

        if not GEKKO_DATA_DIR.exists():
            print(f"{Colors.YELLOW}[WARN] Gekko data directory not found: {GEKKO_DATA_DIR}{Colors.RESET}")
            print(f"{Colors.YELLOW}[WARN] Please download Gekko datasets first.{Colors.RESET}")
            return []

        db_files = list(GEKKO_DATA_DIR.glob("*.db"))

        if not db_files:
            print(f"{Colors.YELLOW}[WARN] No .db files found in {GEKKO_DATA_DIR}{Colors.RESET}")
            print(f"{Colors.YELLOW}[WARN] Please download Gekko datasets from Google Drive.{Colors.RESET}")
            return []

        print(f"{Colors.GREEN}[OK] Found {len(db_files)} database(s){Colors.RESET}")
        for db_file in db_files:
            size_mb = db_file.stat().st_size / 1024 / 1024
            print(f"  - {db_file.name} ({size_mb:.2f} MB)")

        self.databases = db_files
        return db_files

    def get_database_info(self, db_path: Path) -> Dict:
        """
        Get information about a Gekko database
        Returns: Dictionary with database metadata
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get list of tables (trading pairs)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Filter out candles tables
            candle_tables = [t for t in tables if t.startswith('candles_')]

            # Get statistics for each table
            pair_info = []
            total_candles = 0

            for table in candle_tables:
                # Extract currency and asset from table name
                # Format: candles_CURRENCY_ASSET (e.g., candles_USDT_BTC)
                parts = table.replace('candles_', '').split('_')
                if len(parts) >= 2:
                    currency = parts[0]
                    asset = '_'.join(parts[1:])

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_candles += count

                    # Get date range
                    cursor.execute(f"SELECT MIN(start), MAX(start) FROM {table}")
                    min_date, max_date = cursor.fetchone()

                    pair_info.append({
                        "table": table,
                        "currency": currency,
                        "asset": asset,
                        "candles": count,
                        "date_range": {
                            "start": min_date,
                            "end": max_date
                        }
                    })

            conn.close()

            return {
                "path": str(db_path),
                "name": db_path.name,
                "size_mb": db_path.stat().st_size / 1024 / 1024,
                "pairs_count": len(pair_info),
                "total_candles": total_candles,
                "pairs": pair_info
            }

        except Exception as e:
            print(f"{Colors.RED}[ERROR] Failed to read {db_path.name}: {e}{Colors.RESET}")
            return None

    def export_pair_to_csv(self, db_path: Path, table_name: str, output_path: Path) -> bool:
        """
        Export a trading pair to CSV format
        Returns: True if successful
        """
        try:
            conn = sqlite3.connect(db_path)

            # Read data into pandas
            query = f"SELECT * FROM {table_name} ORDER BY start"
            df = pd.read_sql_query(query, conn)

            # Convert Unix timestamp to readable date
            if 'start' in df.columns:
                df['datetime'] = pd.to_datetime(df['start'], unit='s')

            # Save to CSV
            df.to_csv(output_path, index=False)

            conn.close()
            return True

        except Exception as e:
            print(f"{Colors.RED}[ERROR] Export failed: {e}{Colors.RESET}")
            return False

    def query_pair_data(
        self,
        db_path: Path,
        currency: str,
        asset: str,
        limit: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Query data for a specific trading pair
        Returns: Pandas DataFrame or None
        """
        try:
            table_name = f"candles_{currency}_{asset}"
            conn = sqlite3.connect(db_path)

            query = f"""
            SELECT * FROM {table_name}
            ORDER BY start DESC
            LIMIT ?
            """

            df = pd.read_sql_query(query, conn, params=(limit,))

            # Convert timestamp to datetime
            if 'start' in df.columns:
                df['datetime'] = pd.to_datetime(df['start'], unit='s')

            conn.close()
            return df

        except Exception as e:
            print(f"{Colors.RED}[ERROR] Query failed: {e}{Colors.RESET}")
            return None

    def generate_metadata(self, db_infos: List[Dict]):
        """
        Generate metadata file for all databases
        """
        self.metadata = {
            "last_scan": datetime.now().isoformat(),
            "databases": db_infos,
            "total_pairs": sum(db["pairs_count"] for db in db_infos if db),
            "total_candles": sum(db["total_candles"] for db in db_infos if db),
            "total_size_mb": sum(db["size_mb"] for db in db_infos if db)
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with open(METADATA_FILE, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        print(f"{Colors.BLUE}[INFO] Metadata saved to {METADATA_FILE}{Colors.RESET}")

    def print_summary(self):
        """
        Print summary of available data
        """
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'Gekko Data Summary':^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

        if not self.metadata["databases"]:
            print(f"{Colors.YELLOW}[WARN] No Gekko data available{Colors.RESET}")
            return

        print(f"{Colors.BOLD}Overview:{Colors.RESET}")
        print(f"  Total databases: {len(self.metadata['databases'])}")
        print(f"  Total trading pairs: {self.metadata['total_pairs']}")
        print(f"  Total candles: {self.metadata['total_candles']:,}")
        print(f"  Total size: {self.metadata['total_size_mb']:.2f} MB")

        print(f"\n{Colors.BOLD}Available Databases:{Colors.RESET}")
        for db_info in self.metadata["databases"]:
            if db_info:
                print(f"\n  {Colors.GREEN}{db_info['name']}{Colors.RESET}")
                print(f"    Pairs: {db_info['pairs_count']}")
                print(f"    Candles: {db_info['total_candles']:,}")
                print(f"    Size: {db_info['size_mb']:.2f} MB")

                # Show top 5 pairs by candle count
                top_pairs = sorted(
                    db_info['pairs'],
                    key=lambda x: x['candles'],
                    reverse=True
                )[:5]

                if top_pairs:
                    print(f"    Top pairs:")
                    for pair in top_pairs:
                        print(f"      - {pair['asset']}/{pair['currency']}: {pair['candles']:,} candles")

        print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")


def main():
    """
    Main function
    """
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Gekko Data Integration':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    integrator = GekkoDataIntegration()

    # Scan for databases
    db_files = integrator.scan_databases()

    if not db_files:
        print(f"\n{Colors.YELLOW}[INFO] To download Gekko datasets:{Colors.RESET}")
        print(f"  1. Visit: https://drive.google.com/drive/folders/1Ghoy6w3BfHNgoRjj5jI9dX1BV0WyS8l_")
        print(f"  2. Download binance_30d.zip (or other datasets)")
        print(f"  3. Extract to: {GEKKO_DATA_DIR}")
        print(f"  4. Run this script again")
        print(f"\n{Colors.BLUE}[INFO] See docs/GEKKO_DATA_DOWNLOAD_GUIDE.md for details{Colors.RESET}")
        sys.exit(0)

    # Get info for all databases
    print(f"\n{Colors.BLUE}[INFO] Analyzing databases...{Colors.RESET}")
    db_infos = []
    for db_file in db_files:
        print(f"  Analyzing {db_file.name}...")
        info = integrator.get_database_info(db_file)
        if info:
            db_infos.append(info)

    # Generate metadata
    integrator.generate_metadata(db_infos)

    # Print summary
    integrator.print_summary()

    # Example usage
    print(f"\n{Colors.BOLD}Example Usage:{Colors.RESET}")
    print(f"""
# Query Bitcoin/USDT data from Binance
from scripts.gekko_data_integration import GekkoDataIntegration

integrator = GekkoDataIntegration()
integrator.scan_databases()

# Get recent 1000 candles
df = integrator.query_pair_data(
    db_path=Path("data/gekko-history/binance_0.1.db"),
    currency="USDT",
    asset="BTC",
    limit=1000
)

print(df.head())
    """)

    print(f"\n{Colors.GREEN}[OK] Integration complete!{Colors.RESET}")


if __name__ == "__main__":
    main()
