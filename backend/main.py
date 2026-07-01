"""

Video Transcriber Backend
--------------------------
- Accepts .mp4 upload
- Extracts audio using ffmpeg
- Transcribes + TRANSLATES everything to English using faster-whisper large-v3
- Handles Hindi, English, mixed/Hinglish — output always in English
- No time limit — processes full video regardless of length
- Saves transcript on server (transcripts/ folder + a local log file)
 
Run with: python -m uvicorn main:app --reload --port 8000
"""
 
import os
import uuid
import subprocess
import json
from datetime import datetime
 
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from faster_whisper import WhisperModel
 
# ---------- CONFIG ----------
UPLOAD_DIR = "uploads"
TRANSCRIPT_DIR = "transcripts"
LOG_FILE = "transcript_log.jsonl"
 
# large-v3 = best accuracy, especially for Hindi and mixed language
# If too slow on your CPU, switch back to "medium"
MODEL_SIZE = "large-v3"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"   # int8 for CPU — fast and low memory
 
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
 
# ---------- APP INIT ----------
app = FastAPI(title="Video Transcriber")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
print("Loading Whisper model... (this happens once at startup)")
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
print("Model loaded successfully.")
 
 
# ---------- HELPERS ----------
def extract_audio(video_path: str, audio_path: str):
    """
    Extract full audio from video as mono 16kHz wav.
    No duration limit — processes the entire file.
    """
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",           # no video
        "-ac", "1",      # mono
        "-ar", "16000",  # 16kHz sample rate (Whisper requirement)
        "-f", "wav",
        audio_path
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
 
 
def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
 
 
def transcribe_audio(audio_path: str):
    """
    Transcribes audio and TRANSLATES everything to English.
 
    Key settings:
    - task="translate"     → always outputs English, regardless of input language
    - beam_size=5          → good accuracy tradeoff
    - vad_filter=True      → removes silence chunks, faster processing
    - vad_parameters       → tuned to avoid cutting off speech (longer min silence)
    - no chunk_length cap  → full video processed, no time limit
    - condition_on_previous_text=True → better context across segments
    - temperature fallback → if beam search fails, tries greedy decode
    """
    segments, info = model.transcribe(
        audio_path,
        task="translate",                    # FIX 1 & 4: always translate to English
        beam_size=5,
        best_of=5,
        patience=1.0,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 500,  # FIX 3: won't cut off at short pauses
            "speech_pad_ms": 400,            # padding around speech — catches full words
            "threshold": 0.3,               # lower = more sensitive, catches quiet speech
        },
        condition_on_previous_text=True,    # FIX 2: better Hindi/mixed language quality
        temperature=[0.0, 0.2, 0.4, 0.6],  # fallback temperatures if transcription uncertain
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
    )
 
    # IMPORTANT: segments is a generator — must iterate fully for complete video
    # This is FIX 3: not cutting off early
    segment_list = []
    for seg in segments:
        text = seg.text.strip()
        if text:  # skip empty segments
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": text
            })
 
    return segment_list, info.language, info.language_probability
 
 
def save_transcript_files(job_id: str, segments: list, language: str):
    """Save transcript as both .txt and .srt files."""
    txt_path = os.path.join(TRANSCRIPT_DIR, f"{job_id}.txt")
    srt_path = os.path.join(TRANSCRIPT_DIR, f"{job_id}.srt")
 
    with open(txt_path, "w", encoding="utf-8") as f:
        full_text = " ".join(seg["text"] for seg in segments)
        f.write(full_text)
 
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")
 
    return txt_path, srt_path
 
 
def log_job(job_id: str, original_filename: str, language: str, duration_segments: int, txt_path: str, srt_path: str):
    """Internal log — admin only, not shown to users."""
    entry = {
        "job_id": job_id,
        "original_filename": original_filename,
        "detected_language": language,
        "total_segments": duration_segments,
        "output_language": "english (translated)",
        "timestamp": datetime.utcnow().isoformat(),
        "txt_path": txt_path,
        "srt_path": srt_path,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
 
 
# ---------- ROUTES ----------
@app.get("/")
def root():
    return {"status": "running", "message": "Video Transcriber API is live"}
 
 
@app.post("/transcribe")
async def transcribe_video(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are supported")
 
    job_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}.mp4")
    audio_path = os.path.join(UPLOAD_DIR, f"{job_id}.wav")
 
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)
 
    try:
        extract_audio(video_path, audio_path)
        segments, language, lang_prob = transcribe_audio(audio_path)
 
        if not segments:
            raise HTTPException(status_code=422, detail="No speech detected in video")
 
        txt_path, srt_path = save_transcript_files(job_id, segments, language)
        log_job(job_id, file.filename, language, len(segments), txt_path, srt_path)
 
        full_text = " ".join(seg["text"] for seg in segments)
 
        return JSONResponse({
            "job_id": job_id,
            "detected_language": language,
            "language_confidence": round(lang_prob, 2),
            "output_language": "English (translated)",
            "total_segments": len(segments),
            "transcript": full_text,
            "segments": segments,
            "download_txt": f"/download/{job_id}/txt",
            "download_srt": f"/download/{job_id}/srt",
        })
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
 
 
@app.get("/download/{job_id}/{filetype}")
def download_transcript(job_id: str, filetype: str):
    if filetype not in ("txt", "srt"):
        raise HTTPException(status_code=400, detail="filetype must be 'txt' or 'srt'")
 
    path = os.path.join(TRANSCRIPT_DIR, f"{job_id}.{filetype}")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Transcript not found")
 
    return FileResponse(
        path,
        media_type="text/plain",
        filename=f"transcript_{job_id}.{filetype}"
    )