import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Currency MCP")

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"


@mcp.tool()
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict:
    """Convert currency using the latest Frankfurter/ECB rate."""

    if amount <= 0:
        return {
            "ok": False,
            "error": "amount must be greater than zero",
        }

    source = from_currency.upper().strip()
    target = to_currency.upper().strip()

    if len(source) != 3 or len(target) != 3:
        return {
            "ok": False,
            "error": (
                "Currencies must be ISO 4217 codes "
                "such as INR or SGD"
            ),
        }

    if source == target:
        return {
            "ok": True,
            "amount": amount,
            "from_currency": source,
            "to_currency": target,
            "rate": 1.0,
            "converted_amount": amount,
            "source": "Frankfurter",
            "source_url": "https://api.frankfurter.dev",
        }

    try:

        async with httpx.AsyncClient(timeout=15) as client:

            response = await client.get(
                FRANKFURTER_URL,
                params={
                    "amount": amount,
                    "from": source,
                    "to": target,
                },
            )

            response.raise_for_status()

            data = response.json()

        rates = data.get("rates", {})

        if target not in rates:
            return {
                "ok": False,
                "error": (
                    f"No rate returned for "
                    f"{source}->{target}"
                ),
            }

        converted = float(rates[target])

        rate = converted / amount

        return {
            "ok": True,
            "amount": amount,
            "from_currency": source,
            "to_currency": target,
            "rate": rate,
            "converted_amount": converted,
            "date": data.get("date"),
            "source": "Frankfurter",
            "source_url": "https://api.frankfurter.dev/",
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": f"Currency service failed: {exc}",
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")