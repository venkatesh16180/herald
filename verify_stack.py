import os, requests, ollama

# 1. Ollama responds at all
r = ollama.chat(model='qwen3:4b', messages=[{'role': 'user', 'content': 'Say OK.'}])
print('Ollama chat:', r.message.content[:50])

# 2. OpenWeatherMap key is valid
key = os.environ['OWM_API_KEY']
resp = requests.get('https://api.openweathermap.org/data/2.5/weather',
                     params={'q': 'Hyderabad,IN', 'appid': key, 'units': 'metric'})
resp.raise_for_status()
print('Weather OK:', resp.json()['weather'][0]['description'])

# 3. Kokoro in isolation
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='a')  # 'a' = American English
for _, _, audio in pipeline('Herald stack check complete.', voice='af_heart'):
    sf.write('data/verify_tts.wav', audio, 24000)
print('Kokoro OK -- check data/verify_tts.wav')