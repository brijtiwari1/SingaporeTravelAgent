import asyncio
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


# test/ is one level below the project root
ROOT = Path(__file__).resolve().parents[1]

WEATHER_SERVER = ROOT / "mcp_servers" / "weather_server.py"


async def main():
    print("Project root:", ROOT)
    print("Weather server:", WEATHER_SERVER)
    print("Weather server exists:", WEATHER_SERVER.exists())

    client = MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(WEATHER_SERVER)],
            }
        }
    )

    print("\nConnecting to weather MCP server...")

    tools = await client.get_tools()

    print("\nAvailable tools:")
    for tool in tools:
        print("-", tool.name)

    weather_tool = next(
        tool for tool in tools
        if tool.name == "get_weather_forecast"
    )

    print("\nCalling weather MCP tool...")

    result = await weather_tool.ainvoke(
        {
            "location": "Singapore",
            "start_date": "2026-09-06",
            "days": 3,
        }
    )

    print("\nWeather result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())