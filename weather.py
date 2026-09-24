"""Weather via Open-Meteo + Nominatim. No API key needed."""
import requests
from dataclasses import dataclass

_GEO = "https://nominatim.openstreetmap.org/search"
_REV = "https://nominatim.openstreetmap.org/reverse"
_WX  = "https://api.open-meteo.com/v1/forecast"
_HDR = {"User-Agent": "SmartAgriAI/2.0 (Burundi)"}
_WMO = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Foggy",
        51:"Light drizzle",61:"Slight rain",63:"Moderate rain",65:"Heavy rain",
        80:"Rain showers",95:"Thunderstorm"}

@dataclass
class WeatherData:
    location:str; country:str; temperature:float; humidity:int
    precipitation:float; wind_speed:float; weather_code:int; condition:str
    rain_3days:list; temp_max:list; temp_min:list
    farming_risk:str; farming_advice:list; error:str=None

def _condition(c): return _WMO.get(c,"Unknown")

def _assess(humidity, precip, rain3, temp, code):
    advice=[]; score=0
    if humidity>=80: score+=2; advice.append(f"Humidity {humidity}% — high fungal disease risk. Inspect crops for leaf spots and rust.")
    elif humidity>=65: score+=1; advice.append(f"Moderate humidity ({humidity}%). Monitor crops for early disease signs.")
    total_rain=sum(rain3)
    if total_rain>=30: score+=2; advice.append(f"{total_rain:.0f}mm rain forecast. Ensure field drainage to prevent waterlogging.")
    elif total_rain>=10: score+=1; advice.append(f"Light rain expected ({total_rain:.0f}mm). Good time to apply fertilizer.")
    elif total_rain==0: advice.append("No rain forecast. Consider irrigating if crops show drought stress.")
    if precip>5: advice.append("Active rain — avoid pesticide application now.")
    if temp>=32: score+=1; advice.append(f"High temperature ({temp}°C). Water early morning or evening.")
    elif temp<=14: score+=1; advice.append(f"Cool temperature ({temp}°C). Protect seedlings from cold stress.")
    if code>=95: score+=2; advice.append("Thunderstorm warning — do not work in open fields.")
    if not advice: advice.append("Weather conditions are favourable for field work.")
    risk = "high" if score>=4 else "medium" if score>=2 else "low"
    return risk, advice[:5]

def _fetch_wx(lat, lon, city="Your Location", country=""):
    try:
        r = requests.get(_WX, params={
            "latitude":lat,"longitude":lon,
            "current":"temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "daily":"precipitation_sum,temperature_2m_max,temperature_2m_min",
            "timezone":"auto","forecast_days":3}, timeout=8)
        r.raise_for_status(); wx=r.json(); c=wx["current"]; d=wx["daily"]
        risk,advice=_assess(int(c["relative_humidity_2m"]),c["precipitation"],
                            d["precipitation_sum"],c["temperature_2m"],c["weather_code"])
        return WeatherData(location=city,country=country,temperature=c["temperature_2m"],
            humidity=int(c["relative_humidity_2m"]),precipitation=c["precipitation"],
            wind_speed=c["wind_speed_10m"],weather_code=c["weather_code"],
            condition=_condition(c["weather_code"]),rain_3days=d["precipitation_sum"],
            temp_max=d["temperature_2m_max"],temp_min=d["temperature_2m_min"],
            farming_risk=risk,farming_advice=advice)
    except Exception as e: return _err_wx(str(e))

def get_weather(location):
    try:
        r=requests.get(_GEO,params={"q":location,"format":"json","limit":1},headers=_HDR,timeout=8)
        r.raise_for_status(); data=r.json()
        if not data: return _err_wx(f"Location '{location}' not found.")
        p=data[0]; parts=[x.strip() for x in p.get("display_name","").split(",")]
        return _fetch_wx(float(p["lat"]),float(p["lon"]),parts[0],parts[-1] if len(parts)>1 else "")
    except Exception as e: return _err_wx(str(e))

def get_weather_by_coords(lat, lon):
    city="Your Location"; country=""
    try:
        r=requests.get(_REV,params={"lat":lat,"lon":lon,"format":"json"},headers=_HDR,timeout=8)
        r.raise_for_status(); a=r.json().get("address",{})
        city=a.get("city") or a.get("town") or a.get("village") or "Your Location"
        country=a.get("country","")
    except: pass
    return _fetch_wx(lat, lon, city, country)

def _err_wx(msg):
    return WeatherData(location="",country="",temperature=0,humidity=0,precipitation=0,
        wind_speed=0,weather_code=0,condition="",rain_3days=[],temp_max=[],temp_min=[],
        farming_risk="low",farming_advice=[],error=msg)
