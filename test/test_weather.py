import asyncio
import httpx


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": "Singapore",
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )

        print("Geocoding status:", geo.status_code)
        print("Geocoding:", geo.json())

        forecast = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 1.3521,
                "longitude": 103.8198,
                "timezone": "Asia/Singapore",
                "forecast_days": 3,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
            },
        )

        print("Forecast status:", forecast.status_code)
        print("Forecast:", forecast.json())


asyncio.run(main())