#!/usr/bin/env python3
"""
Start Market Spoke MCP Server
Supports both HTTP server mode and MCP stdio mode
"""
import sys
import os
from pathlib import Path
import asyncio
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

if __name__ == "__main__":
    # Check if running in MCP stdio mode
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        # MCP stdio mode for Claude Desktop
        # Import here to avoid loading FastAPI in stdio mode
        from services.market_spoke.app.main import mcp_app

        # Run MCP server using mcp.run()
        import mcp
        mcp.run(mcp_app)
    else:
        # HTTP server mode
        import uvicorn

        print("=" * 60)
        print("Starting Market Spoke MCP Server (HTTP Mode)")
        print("=" * 60)
        print(f"Server will be available at: http://localhost:8001")
        print(f"MCP endpoint: http://localhost:8001/mcp")
        print(f"Health check: http://localhost:8001/health")
        print(f"Tools list: http://localhost:8001/")
        print("=" * 60)
        print()

        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
