from fastapi import FastAPI, HTTPException
import requests as _requests
from datetime import datetime
from schemas import BriefingRequest, BriefingResponse
from graph import briefing_graph
from speak import synthesize
from weather import get_weather
from news import get_headlines
from clock import get_time_context
from history import init_db, log_briefing
from logging_setup import get_logger

app = FastAPI(title='Herald')
log = get_logger(__name__)
init_db()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/briefing/generate', response_model=BriefingResponse)
def generate_briefing(req: BriefingRequest):
    log.info('Briefing requested')
    try:
        weather = get_weather(city=req.city)
    except _requests.HTTPError:
        raise HTTPException(status_code=400, detail=f"Could not find weather for city: {req.city}")
    state = {
        'weather': weather,
        'headlines': get_headlines(),
        'time_context': get_time_context(weather['timezone_offset']),
        'draft': '', 'word_count': 0, 'attempts': 0,
    }
    result = briefing_graph.invoke(state)
    now = datetime.now()
    audio_path = synthesize(result['draft'], f"data/briefing_{now:%Y%m%d_%H%M}.wav")
    log_briefing(result['draft'], audio_path, result['word_count'], now)
    log.info(f"Briefing generated, {result['word_count']} words")
    return BriefingResponse(script=result['draft'], audio_path=audio_path,
                             word_count=result['word_count'], generated_at=now)