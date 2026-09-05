import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Project root
ROOT = Path(__file__).resolve().parents[1]

# Currency MCP server
CURRENCY_SERVER = ROOT / "mcp_servers" / "currency_server.py"


async def main():
    print(f"Project root: {ROOT}")
    print(f"Currency server: {CURRENCY_SERVER}")
    print(f"Currency server exists: {CURRENCY_SERVER.exists()}")

    if not CURRENCY_SERVER.exists():
        print("\nERROR: currency_server.py was not found.")
        return

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(CURRENCY_SERVER)],
    )

    print("\nConnecting to currency MCP server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:

                # Initialize MCP session
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()

                print("\nAvailable tools:")

                for tool in tools_result.tools:
                    print(f"- {tool.name}")

                # Check whether our expected tool exists
                tool_names = [tool.name for tool in tools_result.tools]

                if "convert_currency" not in tool_names:
                    print(
                        "\nERROR: convert_currency tool was not found."
                    )
                    return

                print("\nCalling currency MCP tool...")

                # Call currency conversion tool
                result = await session.call_tool(
                    "convert_currency",
                    {
                        "from_currency": "INR",
                        "to_currency": "SGD",
                        "amount": 50000,
                    },
                )

                print("\nCurrency result:")
                print(result)

    except Exception as exc:
        print("\nERROR while connecting/calling currency MCP server:")
        print(type(exc).__name__)
        print(exc)


if __name__ == "__main__":
    asyncio.run(main())