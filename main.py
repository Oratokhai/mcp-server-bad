"""
Bad MCP server — fundamentally broken across multiple layers.
Target verdict: NON-COMPLIANT (~21%)

Deliberate failures:
  CHECK-01 WARN  — initialize returns no serverInfo → partial handshake
  CHECK-02 FAIL  — protocolVersion is an integer (123) not a string
  CHECK-03 FAIL  — capabilities is an array, not an object
  CHECK-04 FAIL  — "jsonrpc": "1.0" on all responses
  CHECK-05 FAIL  — all responses echo id=999 regardless of request id
  CHECK-06 FAIL  — tools/list returns a JSON-RPC error → cascades to SKIP 07–12
  CHECK-13 FAIL  — unknown methods return a success result (not an error)
  CHECK-14 FAIL  — notifications (no id) return HTTP 500
  CHECK-15 FAIL  — string params return a success result
  CHECK-17 FAIL  — Content-Type: text/html on all responses
  CHECK-16 PASS  — still responds fast
  CHECK-18 PASS  — no stack traces or file paths in error messages
"""
import json
from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI(title="MCP Server — Bad")

BAD_CT = "text/html"


def resp(data):
    return Response(content=json.dumps(data), media_type=BAD_CT)


@app.get("/")
async def health():
    return {"status": "ok", "server": "mcp-server-bad"}


@app.post("/mcp")
async def handle(request: Request):
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    req_id = body.get("id")
    method = body.get("method", "")

    # Notifications (no id) — deliberately crash with 500 → fails CHECK-14
    if req_id is None:
        return Response(status_code=500)

    if method == "initialize":
        # protocolVersion is int (not str) → CHECK-02 FAIL
        # capabilities is array (not object) → CHECK-03 FAIL
        # no serverInfo → CHECK-01 WARN
        # jsonrpc "1.0" → CHECK-04 FAIL
        # id 999 (not echoed) → CHECK-05 FAIL
        return resp({
            "jsonrpc": "1.0",
            "id": 999,
            "result": {
                "protocolVersion": 123,
                "capabilities": ["tools"]
            }
        })

    elif method == "tools/list":
        # Return a JSON-RPC error → CHECK-06 FAIL → SKIPs 07-12
        return resp({
            "jsonrpc": "1.0",
            "id": 999,
            "error": {"code": -1, "message": "Not implemented"}
        })

    else:
        # All other methods (including unknown ones): return success — fails CHECK-13
        # String params also get success — fails CHECK-15
        return resp({
            "jsonrpc": "1.0",
            "id": 999,
            "result": {"ok": True}
        })
