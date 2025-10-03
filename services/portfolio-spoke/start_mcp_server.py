"""
Start Portfolio Spoke MCP Server

Launcher script for the Portfolio Spoke MCP server.
Ensures proper environment setup before starting the server.
"""

import sys
import os
from pathlib import Path
import subprocess

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def check_dependencies():
    """
    Check if required dependencies are installed.
    """
    required_packages = [
        'numpy',
        'pandas',
        'pypfopt',
        'scipy'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"WARNING: Missing required packages: {', '.join(missing)}", file=sys.stderr)
        print(f"Install with: pip install -r requirements.txt", file=sys.stderr)
        return False

    return True


def main():
    """
    Main entry point.
    """
    print("Starting Portfolio Spoke MCP Server...", file=sys.stderr)

    # Check dependencies
    if not check_dependencies():
        print("ERROR: Missing dependencies. Please install requirements.", file=sys.stderr)
        sys.exit(1)

    # Start MCP server
    print("Portfolio Spoke MCP Server ready", file=sys.stderr)

    # Import and run server
    from mcp_server import main as server_main
    import asyncio

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\nShutting down Portfolio Spoke MCP Server", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
