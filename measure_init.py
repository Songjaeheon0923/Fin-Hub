import subprocess
import time
import sys

server_path = sys.argv[1] if len(sys.argv) > 1 else "services/market-spoke/mcp_server.py"

start = time.time()
proc = subprocess.Popen(
    [sys.executable, server_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

request = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n'
proc.stdin.write(request.encode())
proc.stdin.flush()

response = proc.stdout.readline()
end = time.time()

if response:
    print(f"[OK] Initialized in {end - start:.2f} seconds")
else:
    print(f"[FAIL] No response after {end - start:.2f} seconds")

proc.terminate()
