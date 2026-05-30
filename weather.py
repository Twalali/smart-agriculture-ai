"""
weather.py — Free weather integration using Open-Meteo + Nominatim.

No API key required. Both services are completely free.
- Geocoding:  https://nominatim.openstreetmap.org  (OpenStreetMap)
- Weather:    https://api.open-meteo.com           (Open-Meteo)
"""

import os
import requests
from dataclasses import dataclass

_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
_HEADERS     = {"User-Agent": "SmartAgricultureAI/2.0 (Burundi)"}
_TIMEOUT     = 8  # seconds


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class WeatherData:
    location:        str
    country:         str
    temperature:     float       # Celsius
    humidity:        int         # %
    precipitation:   float       # mm current hour
    wind_speed:      float       # km/h
    weather_code:    int         # WMO code
    condition:       str         # human-readable condition
    rain_3days:      list[float] # mm per day for next 3 days
    temp_max:        list[float] # °C max per day
    temp_min:        list[float] # °C min per day
    farming_risk:    str         # "low" | "medium" | "high"
    farming_advice:  list[str]   # 3-5 actionable tips
    error:           str | None = None


# ---------------------------------------------------------------------------
# WMO weather code → human-readable condition
# ---------------------------------------------------------------------------

_WMO_CONDITIONS = {
    0:  "Clear sky",
    1:  "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm",
}


def _condition(code: int) -> str:
    return _WMO_CONDITIONS.get(code, "Unknown")


# ---------------------------------------------------------------------------
# Farming risk + advice logic
# ---------------------------------------------------------------------------

def _assess_farming(humidity: int, precipitation: float,
                    rain_3days: list[float], temp: float,
                    weather_code: int) -> tuple[str, list[str]]:
    """
    Derive farming risk level and actionable advice from weather data.
    Logic tuned for Burundian crops: beans, cassava, maize, coffee, banana.
    """
    total_rain_3d = sum(rain_3days)
    advice = []
    risk_score = 0

    # High humidity → fungal disease risk
    if humidity >= 80:
        risk_score += 2
        advice.append(
            f"Humidity is {humidity}% — conditions favour fungal diseases. "
            "Inspect crops for leaf spots, rust, and mildew."
        )
    elif humidity >= 65:
        risk_score += 1
        advice.append(
            f"Moderate humidity ({humidity}%). Monitor crops for early signs of fungal infection."
        )

    # Heavy rain forecast
    if total_rain_3d >= 30:
        risk_score += 2
        advice.append(
            f"{total_rain_3d:.0f} mm of rain expected over 3 days. "
            "Ensure field drainage is clear to prevent root rot and waterlogging."
        )
    elif total_rain_3d >= 10:
        risk_score += 1
        advice.append(
            f"Light to moderate rain expected ({total_rain_3d:.0f} mm). "
            "Good time to apply fertilizer before rain for absorption."
        )
    elif total_rain_3d == 0:
        advice.append(
            "No rain forecast for 3 days. Consider irrigating if crops show drought stress."
        )

    # Current rain
    if precipitation > 5:
        advice.append("Active rainfall — avoid pesticide or fungicide application now; wait for dry conditions.")
    elif precipitation == 0 and humidity < 60:
        advice.append("Dry conditions — good time for harvesting, pesticide spraying, or field work.")

    # Temperature extremes
    if temp >= 32:
        risk_score += 1
        advice.append(
            f"High temperature ({temp}°C). Beans and coffee are heat-sensitive — "
            "water early morning or evening."
        )
    elif temp <= 14:
        risk_score += 1
        advice.append(
            f"Cool temperature ({temp}°C). Growth may slow. "
            "Protect seedlings from cold stress."
        )

    # Thunderstorm
    if weather_code >= 95:
        risk_score += 2
        advice.append("Thunderstorm conditions — do not work in open fields. Secure equipment and young plants.")

    # Ensure at least one positive tip
    if not advice:
        advice.append("Weather conditions are currently favourable for field work and crop growth.")

    # Determine risk level
    if risk_score >= 4:
        risk = "high"
    elif risk_score >= 2:
        risk = "medium"
    else:
        risk = "low"

    return risk, advice[:5]  # cap at 5 tips


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_weather(location: str) -> WeatherData:
    """
    Fetch current weather and 3-day forecast for a given location string.
    Returns WeatherData; on failure sets error field.
    """
    location = location.strip()
    if not location:
        return _error_weather("Please enter a location name.")

    # Step 1 — Geocode location name to lat/lon
    try:
        geo_resp = requests.get(
            _GEOCODE_URL,
            params={"q": location, "format": "json", "limit": 1},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except requests.RequestException as exc:
        return _error_weather(f"Geocoding failed: {exc}")

    if not geo_data:
        return _error_weather(
            f"Location '{location}' not found. "
            "Try adding the country, e.g. 'Gitega, Burundi'."
        )

    place    = geo_data[0]
    lat      = float(place["lat"])
    lon      = float(place["lon"])
    display  = place.get("display_name", location)
    # Extract clean city and country
    parts    = [p.strip() for p in display.split(",")]
    city     = parts[0]
    country  = parts[-1] if len(parts) > 1 else ""

    # Step 2 — Fetch weather
    try:
        wx_resp = requests.get(
            _WEATHER_URL,
            params={
                "latitude":  lat,
                "longitude": lon,
                "current":   "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
                "daily":     "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone":  "Africa/Bujumbura",
                "forecast_days": 3,
            },
            timeout=_TIMEOUT,
        )
        wx_resp.raise_for_status()
        wx = wx_resp.json()
    except requests.RequestException as exc:
        return _error_weather(f"Weather fetch failed: {exc}")

    current      = wx["current"]
    daily        = wx["daily"]
    temp         = current["temperature_2m"]
    humidity     = int(current["relative_humidity_2m"])
    precipitation= current["precipitation"]
    wind_speed   = current["wind_speed_10m"]
    code         = current["weather_code"]
    rain_3days   = daily["precipitation_sum"]
    temp_max     = daily["temperature_2m_max"]
    temp_min     = daily["temperature_2m_min"]

    farming_risk, farming_advice = _assess_farming(
        humidity, precipitation, rain_3days, temp, code
    )

    return WeatherData(
        location=city,
        country=country,
        temperature=temp,
        humidity=humidity,
        precipitation=precipitation,
        wind_speed=wind_speed,
        weather_code=code,
        condition=_condition(code),
        rain_3days=rain_3days,
        temp_max=temp_max,
        temp_min=temp_min,
        farming_risk=farming_risk,
        farming_advice=farming_advice,
    )


_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def get_weather_by_coords(lat: float, lon: float) -> WeatherData:
    """
    Fetch weather directly from GPS coordinates.
    Reverse-geocodes lat/lon to a place name, then fetches weather.
    """
    # Reverse geocode to get a human-readable place name
    city    = "Your Location"
    country = ""
    try:
        rev_resp = requests.get(
            _REVERSE_URL,
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        rev_resp.raise_for_status()
        rev_data = rev_resp.json()
        addr     = rev_data.get("address", {})
        city     = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("county")
            or "Your Location"
        )
        country  = addr.get("country", "")
    except requests.RequestException:
        pass  # fall back to generic name, still fetch weather

    # Fetch weather with the provided coordinates directly
    try:
        wx_resp = requests.get(
            _WEATHER_URL,
            params={
                "latitude":      lat,
                "longitude":     lon,
                "current":       "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
                "daily":         "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone":      "auto",
                "forecast_days": 3,
            },
            timeout=_TIMEOUT,
        )
        wx_resp.raise_for_status()
        wx = wx_resp.json()
    except requests.RequestException as exc:
        return _error_weather(f"Weather fetch failed: {exc}")

    current       = wx["current"]
    daily         = wx["daily"]
    temp          = current["temperature_2m"]
    humidity      = int(current["relative_humidity_2m"])
    precipitation = current["precipitation"]
    wind_speed    = current["wind_speed_10m"]
    code          = current["weather_code"]
    rain_3days    = daily["precipitation_sum"]
    temp_max      = daily["temperature_2m_max"]
    temp_min      = daily["temperature_2m_min"]

    farming_risk, farming_advice = _assess_farming(
        humidity, precipitation, rain_3days, temp, code
    )

    return WeatherData(
        location=city,
        country=country,
        temperature=temp,
        humidity=humidity,
        precipitation=precipitation,
        wind_speed=wind_speed,
        weather_code=code,
        condition=_condition(code),
        rain_3days=rain_3days,
        temp_max=temp_max,
        temp_min=temp_min,
        farming_risk=farming_risk,
        farming_advice=farming_advice,
    )


def _error_weather(message: str) -> WeatherData:
    return WeatherData(
        location="", country="", temperature=0, humidity=0,
        precipitation=0, wind_speed=0, weather_code=0,
        condition="", rain_3days=[], temp_max=[], temp_min=[],
        farming_risk="low", farming_advice=[], error=message,
    )
