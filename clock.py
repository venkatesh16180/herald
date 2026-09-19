from datetime import datetime, timedelta, timezone

def get_time_context(timezone_offset: int = 0) -> dict:
    local_now = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset)
    return {'time_str': local_now.strftime('%I:%M %p'), 'weekday': local_now.strftime('%A')}