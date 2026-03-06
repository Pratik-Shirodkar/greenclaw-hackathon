#!/usr/bin/env python3
"""
GreenClaw Climate Monitor — Fetch weather, AQI, and disaster data.
Uses OpenWeatherMap, WAQI, and NASA EONET APIs.
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests library not installed. Run: pip install requests"}))
    sys.exit(1)
import re


# Common filler phrases users type that aren't part of a city name
FILLER_PATTERNS = [
    r'\bright\s*now\b', r'\bcurrently\b', r'\bcurrent\b', r'\btoday\b',
    r'\bweather\s*(in|for|at|of)?\b', r'\btemperature\s*(in|for|at|of)?\b',
    r'\bclimate\s*(in|for|at|of)?\b', r'\baqi\s*(in|for|at|of)?\b',
    r'\bair\s*quality\s*(in|for|at|of)?\b', r'\bhow\s*is\b', r"\bwhat'?s?\b",
    r'\bthe\b', r'\btell\s*me\b', r'\bshow\s*me\b', r'\bget\b',
    r'\bplease\b', r'\bcheck\b', r'\blook\s*up\b', r'\bfind\b',
    r'\bforecast\s*(in|for|at|of)?\b',
]


def sanitize_city(raw: str) -> str:
    """Strip common filler words/phrases from a user's city query."""
    cleaned = raw.strip()
    for pattern in FILLER_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    # Collapse multiple spaces and strip
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # If nothing is left after stripping, return original
    return cleaned if cleaned else raw.strip()


def get_weather(city: str, api_key: str) -> dict:
    """Fetch current weather and 5-day forecast from OpenWeatherMap."""
    city = sanitize_city(city)
    # Current weather
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        current = resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            return {"error": f"City '{city}' not found. Please check the spelling."}
        return {"error": f"Weather API error: {e}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {e}"}

    # 5-day forecast
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
    forecast_params = {"q": city, "appid": api_key, "units": "metric", "cnt": 40}
    
    try:
        forecast_resp = requests.get(forecast_url, params=forecast_params, timeout=10)
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()
    except Exception:
        forecast_data = None

    # Build structured response
    weather_icons = {
        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️",
        "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️",
        "Haze": "🌫️", "Dust": "🌪️", "Tornado": "🌪️"
    }
    
    main_weather = current["weather"][0]["main"]
    icon = weather_icons.get(main_weather, "🌤️")

    result = {
        "type": "weather",
        "city": current["name"],
        "country": current["sys"]["country"],
        "icon": icon,
        "current": {
            "temperature_c": round(current["main"]["temp"], 1),
            "feels_like_c": round(current["main"]["feels_like"], 1),
            "humidity_pct": current["main"]["humidity"],
            "wind_speed_ms": current["wind"]["speed"],
            "condition": current["weather"][0]["description"].title(),
            "pressure_hpa": current["main"]["pressure"],
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Add daily forecast summary
    if forecast_data and "list" in forecast_data:
        daily_forecasts = {}
        for entry in forecast_data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    "temp_min": entry["main"]["temp_min"],
                    "temp_max": entry["main"]["temp_max"],
                    "condition": entry["weather"][0]["description"].title(),
                }
            else:
                daily_forecasts[date]["temp_min"] = min(
                    daily_forecasts[date]["temp_min"], entry["main"]["temp_min"]
                )
                daily_forecasts[date]["temp_max"] = max(
                    daily_forecasts[date]["temp_max"], entry["main"]["temp_max"]
                )
        
        result["forecast_5day"] = [
            {"date": date, **data} for date, data in list(daily_forecasts.items())[:5]
        ]

    return result


def get_aqi(city: str, api_key: str) -> dict:
    """Fetch Air Quality Index from WAQI."""
    city = sanitize_city(city)
    url = f"https://api.waqi.info/feed/{city}/"
    params = {"token": api_key}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"AQI API error: {e}"}

    if data.get("status") != "ok":
        # Try with city search
        search_url = f"https://api.waqi.info/search/"
        search_params = {"token": api_key, "keyword": city}
        try:
            search_resp = requests.get(search_url, params=search_params, timeout=10)
            search_data = search_resp.json()
            if search_data.get("status") == "ok" and search_data.get("data"):
                station = search_data["data"][0]
                aqi_value = station.get("aqi", "N/A")
                station_name = station.get("station", {}).get("name", city)
                
                # Categorize AQI
                aqi_int = int(aqi_value) if str(aqi_value).isdigit() else 0
                category, icon, health_advice = categorize_aqi(aqi_int)
                
                return {
                    "type": "aqi",
                    "city": city,
                    "station": station_name,
                    "aqi": aqi_int,
                    "category": category,
                    "icon": icon,
                    "health_advice": health_advice,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
        except Exception:
            pass
        return {"error": f"Could not find AQI data for '{city}'. Try a major city name."}

    aqi_data = data["data"]
    aqi_value = aqi_data.get("aqi", 0)
    
    category, icon, health_advice = categorize_aqi(aqi_value)
    
    # Extract pollutant details
    iaqi = aqi_data.get("iaqi", {})
    pollutants = {}
    pollutant_names = {"pm25": "PM2.5", "pm10": "PM10", "o3": "Ozone", "no2": "NO₂", "so2": "SO₂", "co": "CO"}
    for key, name in pollutant_names.items():
        if key in iaqi:
            pollutants[name] = iaqi[key].get("v", "N/A")

    return {
        "type": "aqi",
        "city": city,
        "station": aqi_data.get("city", {}).get("name", city),
        "aqi": aqi_value,
        "category": category,
        "icon": icon,
        "health_advice": health_advice,
        "pollutants": pollutants,
        "dominant_pollutant": aqi_data.get("dominentpol", "N/A"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def categorize_aqi(aqi: int) -> tuple:
    """Categorize AQI value into human-readable category with health advice."""
    if aqi <= 50:
        return "Good", "🟢", "Air quality is satisfactory. Enjoy outdoor activities!"
    elif aqi <= 100:
        return "Moderate", "🟡", "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🟠", "People with respiratory or heart conditions should reduce outdoor activity."
    elif aqi <= 200:
        return "Unhealthy", "🔴", "Everyone may experience health effects. Limit prolonged outdoor exertion."
    elif aqi <= 300:
        return "Very Unhealthy", "🟣", "Health alert! Avoid outdoor activities. Use air purifiers indoors."
    else:
        return "Hazardous", "⚫", "Emergency! Stay indoors, seal windows, use air purifiers. Seek medical attention if feeling unwell."


def get_disasters() -> dict:
    """Fetch active natural disaster events from NASA EONET."""
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    params = {"status": "open", "limit": 15}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"NASA EONET API error: {e}"}

    category_icons = {
        "Wildfires": "🔥", "Severe Storms": "🌪️", "Volcanoes": "🌋",
        "Floods": "🌊", "Earthquakes": "🫨", "Sea and Lake Ice": "🧊",
        "Drought": "☀️", "Dust and Haze": "🌫️", "Landslides": "⛰️",
        "Snow": "❄️", "Temperature Extremes": "🌡️"
    }

    events = []
    for event in data.get("events", []):
        categories = [c["title"] for c in event.get("categories", [])]
        icon = "⚠️"
        for cat in categories:
            if cat in category_icons:
                icon = category_icons[cat]
                break

        geometry = event.get("geometry", [])
        location = None
        if geometry:
            latest = geometry[-1]
            coords = latest.get("coordinates", [])
            if coords:
                location = {"longitude": coords[0], "latitude": coords[1]}

        events.append({
            "title": event["title"],
            "categories": categories,
            "icon": icon,
            "date": event.get("geometry", [{}])[-1].get("date", "Unknown") if geometry else "Unknown",
            "location": location,
            "source": event.get("sources", [{}])[0].get("url", "") if event.get("sources") else "",
        })

    return {
        "type": "disasters",
        "count": len(events),
        "events": events,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def main():
    parser = argparse.ArgumentParser(description="GreenClaw Climate Monitor")
    parser.add_argument("--mode", choices=["weather", "aqi", "disasters", "all"], required=True,
                        help="Type of climate data to fetch")
    parser.add_argument("--city", type=str, help="City name (required for weather/aqi/all)")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data for testing")
    args = parser.parse_args()

    if args.dry_run:
        mock = {
            "weather": {"type": "weather", "city": "London", "icon": "☁️",
                        "current": {"temperature_c": 12.5, "humidity_pct": 78, "condition": "Overcast Clouds"},
                        "status": "dry_run"},
            "aqi": {"type": "aqi", "city": "London", "aqi": 42, "category": "Good", "icon": "🟢",
                    "status": "dry_run"},
            "disasters": {"type": "disasters", "count": 2,
                          "events": [{"title": "Test Wildfire", "icon": "🔥"}], "status": "dry_run"},
        }
        if args.mode == "all":
            print(json.dumps({"weather": mock["weather"], "aqi": mock["aqi"]}, indent=2))
        else:
            print(json.dumps(mock.get(args.mode, {}), indent=2))
        return

    if args.mode in ("weather", "aqi", "all") and not args.city:
        print(json.dumps({"error": "City is required for weather/aqi/all mode. Use --city 'CityName'"}))
        sys.exit(1)

    results = {}

    if args.mode in ("weather", "all"):
        api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        if not api_key:
            results["weather"] = {"error": "OPENWEATHER_API_KEY not set. Get a free key at https://openweathermap.org/api"}
        else:
            results["weather"] = get_weather(args.city, api_key)

    if args.mode in ("aqi", "all"):
        api_key = os.environ.get("WAQI_API_KEY", "")
        if not api_key:
            results["aqi"] = {"error": "WAQI_API_KEY not set. Get a free key at https://aqicn.org/data-platform/token/"}
        else:
            results["aqi"] = get_aqi(args.city, api_key)

    if args.mode == "disasters":
        results["disasters"] = get_disasters()

    # Flatten if single mode
    if len(results) == 1:
        print(json.dumps(list(results.values())[0], indent=2))
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
