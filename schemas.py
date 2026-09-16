from pydantic import BaseModel
from datetime import datetime

class BriefingResponse(BaseModel):
    script: str
    audio_path: str
    word_count: int
    generated_at: datetime

class BriefingRequest(BaseModel):
    city: str | None = None   # override config.CITY for this call only