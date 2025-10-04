#!/usr/bin/env python3
"""
MCP Server Tester - CLI tool to test MCP servers
"""
import asyncio
import json
import sys
from pathlib import Path

async def test_mcp_server(server_path: str):
    """Test MCP server by sending initialize message"""

    # Start the server process
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        server_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    request_json = json.dumps(init_request) + "\n"
    process.stdin.write(request_json.encode())
    await process.stdin.drain()

    # Read response with timeout
    try:
        response = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=5.0
        )

        if response:
            result = json.loads(response.decode())
            print("[OK] Server initialized successfully!")
            print(f"  Server: {result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            print(f"  Version: {result.get('result', {}).get('serverInfo', {}).get('version', 'Unknown')}")

            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            request_json = json.dumps(tools_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            tools_response = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=2.0
            )

            if tools_response:
                tools_result = json.loads(tools_response.decode())
                tools = tools_result.get('result', {}).get('tools', [])
                print(f"\n[OK] Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.get('name')}: {tool.get('description')}")

            return True
    except asyncio.TimeoutError:
        print("[FAIL] Server initialization timed out")
        stderr = await process.stderr.read()
        if stderr:
            print(f"  Error: {stderr.decode()}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        process.terminate()
        await process.wait()

async def main():
    """Test all MCP servers"""
    servers = [
        ("Market Spoke", "services/market-spoke/mcp_server.py"),
        ("Risk Spoke", "services/risk-spoke/mcp_server.py"),
    ]

    print("Testing MCP Servers...\n")

    for name, path in servers:
        print(f"Testing {name}...")
        server_path = Path(__file__).parent / path
        if server_path.exists():
            await test_mcp_server(str(server_path))
        else:
            print(f"[FAIL] Server not found: {server_path}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
