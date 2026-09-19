# tests/test_weather.py
from unittest.mock import patch, MagicMock
from weather import get_weather

def test_get_weather_parses_response():
    fake_resp = MagicMock()
    fake_resp.json.return_value = {
        'weather': [{'description': 'clear sky'}],
        'main': {'temp': 28.4, 'feels_like': 30.1},
        'name': 'Hyderabad',
        'timezone': 19800,
    }
    with patch('weather.requests.get', return_value=fake_resp):
        result = get_weather()
    assert result == {
        'description': 'clear sky', 'temp_c': 28, 'feels_like_c': 30,
        'resolved_city': 'Hyderabad', 'timezone_offset': 19800,
    }