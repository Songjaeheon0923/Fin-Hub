#!/usr/bin/env python3
"""
Start Risk Spoke MCP Server
MCP stdio mode for Claude Desktop integration
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

if __name__ == "__main__":
    from services.risk_spoke.mcp_server import main

    print("=" * 60)
    print("Starting Risk Spoke MCP Server")
    print("=" * 60)
    print("Mode: MCP stdio (Claude Desktop)")
    print("Tools: 8 Risk Management Tools")
    print("=" * 60)
    print()

    main()
