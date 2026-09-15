from datetime import datetime

def get_time_context() -> dict:
    now = datetime.now()
    return {'time_str': now.strftime('%I:%M %p'), 'weekday': now.strftime('%A')}