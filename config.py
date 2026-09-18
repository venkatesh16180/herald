import os
from dotenv import load_dotenv
load_dotenv()

def _str(key, default=None):
    return os.environ.get(key, default)

def _int(key, default):
    return int(os.environ.get(key, default))

OWM_API_KEY   = _str('HERALD_OWM_API_KEY')
CITY          = _str('HERALD_CITY', 'Hyderabad,IN')
RSS_FEEDS     = _str('HERALD_RSS_FEEDS', '').split(',')
MAX_HEADLINES = _int('HERALD_MAX_HEADLINES', 5)
BRAIN_MODEL   = _str('HERALD_BRAIN_MODEL', 'qwen3:4b')
MAX_ATTEMPTS  = _int('HERALD_MAX_ATTEMPTS', 2)
TTS_VOICE     = _str('HERALD_TTS_VOICE', 'af_heart')
DB_PATH       = _str('HERALD_DB_PATH', 'data/history.db')
LOG_LEVEL     = _str('HERALD_LOG_LEVEL', 'INFO')
LOG_PATH      = _str('HERALD_LOG_PATH', 'data/herald.log')
OLLAMA_HOST = _str('HERALD_OLLAMA_HOST', 'http://localhost:11434')