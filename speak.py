from kokoro import KPipeline
import soundfile as sf
import numpy as np
from config import TTS_VOICE

_pipeline = KPipeline(lang_code='a')

def _trim_leading_silence(audio, threshold=0.01, sample_rate=24000, pad_ms=250):
    above_threshold = np.where(np.abs(audio) > threshold)[0]
    if len(above_threshold) == 0:
        return audio  # entire clip is silent -- nothing to trim
    start = max(0, above_threshold[0] - int(sample_rate * pad_ms / 1000))
    return audio[start:]

def synthesize(text: str, out_path: str) -> str:
    audio_chunks = [audio for _, _, audio in _pipeline(text, voice=TTS_VOICE)]
    full_audio = np.concatenate(audio_chunks)
    full_audio = _trim_leading_silence(full_audio)
    sf.write(out_path, full_audio, 24000)
    return out_path