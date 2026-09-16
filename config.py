import os
from dotenv import load_dotenv
load_dotenv()

OWM_API_KEY = os.environ['OWM_API_KEY']
CITY = 'Hyderabad,IN'
RSS_FEEDS = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://news.ycombinator.com/rss',
]
MAX_HEADLINES = 5
BRAIN_MODEL = 'qwen3:4b'
MAX_ATTEMPTS = 2
TTS_VOICE = 'af_heart'