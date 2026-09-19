import requests
from config import OWM_API_KEY, CITY

def get_weather(city: str = None) -> dict:
    resp = requests.get('https://api.openweathermap.org/data/2.5/weather',
        params={'q': city or CITY, 'appid': OWM_API_KEY, 'units': 'metric'}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        'description': data['weather'][0]['description'],
        'temp_c': round(data['main']['temp']),
        'feels_like_c': round(data['main']['feels_like']),
        'resolved_city': data['name'],
        'timezone_offset': data['timezone'],
    }