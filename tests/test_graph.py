# tests/test_graph.py
from unittest.mock import patch, MagicMock
from graph import briefing_graph

def test_briefing_graph_terminates_within_word_budget():
    fake_reply = MagicMock()
    fake_reply.message.content = 'Good morning. ' * 10  # short, well under 220 words
    with patch('graph._client.chat', return_value=fake_reply):
        state = {
            'weather': {'description': 'clear', 'temp_c': 28, 'feels_like_c': 30},
            'headlines': ['Test headline'],
            'time_context': {'time_str': '07:00 AM', 'weekday': 'Monday'},
            'draft': '', 'word_count': 0, 'attempts': 0,
        }
        result = briefing_graph.invoke(state)
    assert result['word_count'] <= 220
    assert result['attempts'] >= 1

def test_briefing_graph_bounds_retry_loop():
    fake_reply = MagicMock()
    fake_reply.message.content = 'word ' * 300  # permanently over budget
    with patch('graph._client.chat', return_value=fake_reply):
        state = {
            'weather': {'description': 'clear', 'temp_c': 28, 'feels_like_c': 30},
            'headlines': ['Test headline'],
            'time_context': {'time_str': '07:00 AM', 'weekday': 'Monday'},
            'draft': '', 'word_count': 0, 'attempts': 0,
        }
        result = briefing_graph.invoke(state)
    assert result['attempts'] == 2  # MAX_ATTEMPTS, not stuck looping