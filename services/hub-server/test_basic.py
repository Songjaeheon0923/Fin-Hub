"""
Basic integration tests for Hub Server
"""

import asyncio
import json
import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Test database connection
async def test_database_connection():
    """Test database connection"""
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://fin_hub:fin_hub_dev@localhost:5432/fin_hub"
        )

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        await engine.dispose()
        print("✅ Database connection test passed")

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        raise


# Test Hub Server health endpoint
async def test_hub_server_health():
    """Test Hub Server health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/health",
                timeout=10.0
            )

            print(f"Health check status: {response.status_code}")
            print(f"Response: {response.json()}")

            # Should be either 200 (healthy) or 503 (starting/unhealthy)
            assert response.status_code in [200, 503]

        print("✅ Hub Server health test passed")

    except Exception as e:
        print(f"❌ Hub Server health test failed: {e}")
        raise


# Test MCP protocol endpoint
async def test_mcp_protocol():
    """Test MCP protocol endpoint"""
    try:
        # Test initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": "test-init",
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "capabilities": {},
                "client_info": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/mcp",
                json=init_request,
                timeout=10.0
            )

            print(f"MCP initialize status: {response.status_code}")
            print(f"Response: {response.json()}")

            assert response.status_code == 200

            result = response.json()
            assert "result" in result
            assert "protocol_version" in result["result"]

        print("✅ MCP protocol test passed")

    except Exception as e:
        print(f"❌ MCP protocol test failed: {e}")
        raise


# Test service registration
async def test_service_registration():
    """Test service registration endpoint"""
    try:
        registration_data = {
            "service_id": "test-service-001",
            "service_name": "test-service",
            "address": "127.0.0.1",
            "port": 9000,
            "tags": ["test", "integration"],
            "meta": {"test": "true"},
            "health_check": {
                "http": "http://127.0.0.1:9000/health",
                "interval": 30
            },
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool for integration testing",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        },
                        "required": ["message"]
                    }
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/services/register",
                json=registration_data,
                timeout=10.0
            )

            print(f"Service registration status: {response.status_code}")
            print(f"Response: {response.json()}")

            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert result["service_id"] == "test-service-001"

        print("✅ Service registration test passed")

    except Exception as e:
        print(f"❌ Service registration test failed: {e}")
        raise


async def run_tests():
    """Run all basic tests"""
    print("🚀 Starting Hub Server integration tests...\n")

    tests = [
        test_database_connection,
        test_hub_server_health,
        test_mcp_protocol,
        test_service_registration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"Running {test.__name__}...")
            await test()
            passed += 1
            print()
        except Exception as e:
            print(f"Test {test.__name__} failed: {e}\n")
            failed += 1

    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the Hub Server deployment.")

    return failed == 0


if __name__ == "__main__":
    asyncio.run(run_tests())