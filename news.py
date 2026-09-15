import feedparser
from config import RSS_FEEDS, MAX_HEADLINES

def get_headlines() -> list[str]:
    headlines = []
    for url in RSS_FEEDS:
        parsed = feedparser.parse(url)
        headlines += [entry.title for entry in parsed.entries[:MAX_HEADLINES]]
    return headlines[:MAX_HEADLINES]