from typing import TypedDict
from config import BRAIN_MODEL, MAX_ATTEMPTS, OLLAMA_HOST
import ollama

_client = ollama.Client(host=OLLAMA_HOST)

class BriefingState(TypedDict):
    weather: dict
    headlines: list[str]
    time_context: dict
    draft: str
    word_count: int
    attempts: int

PERSONA = (
    'You are Herald, a calm, slightly dry morning-briefing assistant. '
    'Greet the user, state the time, then weave the weather and the '
    'top headlines into a short, natural spoken briefing. No headers, '
    'no bullet points -- this will be read aloud.'
)

def compose_draft(state: BriefingState) -> BriefingState:
    prompt = (
        f"{PERSONA}\nTime: {state['time_context']['time_str']}, "
        f"{state['time_context']['weekday']}\nWeather: "
        f"{state['weather']['description']}, {state['weather']['temp_c']}C "
        f"(feels like {state['weather']['feels_like_c']}C)\n"
        f"Headlines: {'; '.join(state['headlines'])}"
    )
    reply = _client.chat(model=BRAIN_MODEL, messages=[{'role': 'user', 'content': prompt}])
    draft = reply.message.content.strip()
    return {
        **state,
        'draft': draft,
        'word_count': len(draft.split()),
        'attempts': state.get('attempts', 0) + 1,
    }
    
from langgraph.graph import StateGraph, END

def route_on_length(state: BriefingState) -> str:
    if state['word_count'] <= 220 or state['attempts'] >= MAX_ATTEMPTS:
        return 'done'
    return 'retry'

def tighten(state: BriefingState) -> BriefingState:
    prompt = (
        f"Rewrite this to under 200 words, same facts, same tone, "
        f"nothing cut that changes the meaning:\n\n{state['draft']}"
    )
    reply = _client.chat(model=BRAIN_MODEL, messages=[{'role': 'user', 'content': prompt}])
    draft = reply.message.content.strip()
    return {**state, 'draft': draft, 'word_count': len(draft.split()), 'attempts': state['attempts'] + 1}

graph = StateGraph(BriefingState)
graph.add_node('compose', compose_draft)
graph.add_node('tighten', tighten)
graph.set_entry_point('compose')
graph.add_conditional_edges('compose', route_on_length, {'done': END, 'retry': 'tighten'})
graph.add_conditional_edges('tighten', route_on_length, {'done': END, 'retry': 'tighten'})
briefing_graph = graph.compile()