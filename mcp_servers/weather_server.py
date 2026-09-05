from datetime import date, timedelta

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Singapore Weather MCP")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@mcp.tool()
async def get_weather_forecast(
    location: str,
    start_date: str,
    days: int = 3,
) -> dict:
    """Get a current/future daily weather forecast for a destination.

    start_date must be YYYY-MM-DD.
    days must be between 1 and 16.
    """

    if days < 1 or days > 16:
        return {
            "ok": False,
            "error": "days must be between 1 and 16",
        }

    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        return {
            "ok": False,
            "error": "start_date must use YYYY-MM-DD",
        }

    end = start + timedelta(days=days - 1)

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            # Find destination coordinates
            geo = await client.get(
                GEOCODING_URL,
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )

            geo.raise_for_status()

            results = geo.json().get("results", [])

            if not results:
                return {
                    "ok": False,
                    "error": f"Location not found: {location}",
                }

            place = results[0]

            # Get weather forecast
            forecast = await client.get(
                FORECAST_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "timezone": "auto",
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "daily": ",".join(
                        [
                            "weather_code",
                            "temperature_2m_max",
                            "temperature_2m_min",
                            "precipitation_probability_max",
                            "precipitation_sum",
                        ]
                    ),
                },
            )

            forecast.raise_for_status()

            data = forecast.json()

        daily = data.get("daily", {})

        rows = []

        for i, day in enumerate(daily.get("time", [])):
            rows.append(
                {
                    "date": day,
                    "weather_code": daily.get(
                        "weather_code", [None]
                    )[i],
                    "temp_max_c": daily.get(
                        "temperature_2m_max", [None]
                    )[i],
                    "temp_min_c": daily.get(
                        "temperature_2m_min", [None]
                    )[i],
                    "rain_probability_percent": daily.get(
                        "precipitation_probability_max", [None]
                    )[i],
                    "rain_mm": daily.get(
                        "precipitation_sum", [None]
                    )[i],
                }
            )

        return {
            "ok": True,
            "location": place.get("name", location),
            "country": place.get("country", ""),
            "timezone": data.get("timezone"),
            "forecast": rows,
            "source": "Open-Meteo",
            "source_url": "https://open-meteo.com/",
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": f"Weather service failed: {exc}",
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")