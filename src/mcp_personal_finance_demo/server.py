import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_URL = "http://localhost:8000"

server = Server("mcp-personal-finance-demo")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_transactions",
            description="List transactions from the personal finance app. Optionally filter by month (YYYY-MM) or date range (from_date/to_date as YYYY-MM-DD). Supports pagination via page and page_size.",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Filter by month, e.g. '2026-01'"},
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "page": {"type": "integer", "description": "Page number (default 1)"},
                    "page_size": {"type": "integer", "description": "Items per page (default 20)"},
                },
            },
        ),
        types.Tool(
            name="get_summary",
            description="Get total income, total expenses, and balance. Optionally filter by month (YYYY-MM) or date range (from_date/to_date as YYYY-MM-DD).",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Filter by month, e.g. '2026-01'"},
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
            },
        ),
        types.Tool(
            name="get_categories",
            description="List all available transaction categories.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="add_transaction",
            description="Add a new income or expense transaction to the personal finance app.",
            inputSchema={
                "type": "object",
                "required": ["amount", "type", "category", "date"],
                "properties": {
                    "amount": {"type": "number", "description": "Amount as a positive number"},
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "'income' or 'expense'",
                    },
                    "category": {"type": "string", "description": "Category name (use get_categories to see options)"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "note": {"type": "string", "description": "Optional note"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if name == "get_transactions":
                params = {k: v for k, v in arguments.items() if v is not None}
                resp = await client.get(f"{BASE_URL}/transactions", params=params)
                resp.raise_for_status()
                return [types.TextContent(type="text", text=resp.text)]

            elif name == "get_summary":
                params = {k: v for k, v in arguments.items() if v is not None}
                resp = await client.get(f"{BASE_URL}/summary", params=params)
                resp.raise_for_status()
                return [types.TextContent(type="text", text=resp.text)]

            elif name == "get_categories":
                resp = await client.get(f"{BASE_URL}/categories")
                resp.raise_for_status()
                return [types.TextContent(type="text", text=resp.text)]

            elif name == "add_transaction":
                resp = await client.post(f"{BASE_URL}/transactions", json=arguments)
                resp.raise_for_status()
                return [types.TextContent(type="text", text=resp.text)]

            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.ConnectError:
        return [types.TextContent(type="text", text=f"ERROR: Cannot reach the personal-finance backend at {BASE_URL}. Make sure the FastAPI server is running (cd personal-finance/backend && uvicorn main:app --port 8000).")]
    except httpx.HTTPStatusError as e:
        return [types.TextContent(type="text", text=f"ERROR: Backend returned {e.response.status_code}: {e.response.text}")]


async def serve():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    asyncio.run(serve())
