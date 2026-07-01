# Video Transcriber — Setup Guide

A simple full-stack app: upload an MP4 video, get a downloadable multilingual transcript.

## Folder Structure
```
video-transcriber/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── uploads/         (temp video/audio, auto-cleaned)
│   └── transcripts/     (saved transcripts — this is your private record)
└── frontend/
    └── index.html
```

## 1. Prerequisites

- Python 3.9+ installed
- ffmpeg installed and available in PATH
  - Windows: download from https://ffmpeg.org/download.html, add the `bin` folder to your system PATH
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

Check it's installed:
```
ffmpeg -version
```

## 2. Backend Setup (in VS Code terminal)

```bash
cd video-transcriber/backend
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## 3. Run the Backend

```bash
uvicorn main:app --reload --port 8000
```

First run will download the Whisper model automatically (a few hundred MB, one-time only).
Once you see "Model loaded successfully", the backend is ready.

Backend will be running at: http://localhost:8000

## 4. Run the Frontend

Just open `frontend/index.html` directly in your browser
(double-click it, or right-click → "Open with Live Server" if you have that VS Code extension).

## 5. Use It

1. Open the page in your browser
2. Click "Select your video file" and choose an .mp4
3. Click "Generate Transcript"
4. Wait for processing (depends on video length + your CPU/GPU)
5. View transcript on screen, or download as .txt / .srt

## Where transcripts are saved (your private copy)

- All transcripts are saved permanently in `backend/transcripts/` as `{job_id}.txt` and `{job_id}.srt`
- A running log of every video processed is kept in `backend/transcript_log.jsonl`
  (includes filename, detected language, timestamp, and file paths)
- This log is for your own records — it is not exposed to users through the website

## Notes on performance

- Default model is "medium" (good multilingual accuracy, moderate speed on CPU)
- For faster processing: change `MODEL_SIZE = "small"` or `"base"` in main.py (less accurate)
- For better accuracy: change to `MODEL_SIZE = "large-v3"` (slower on CPU)
- If you have an NVIDIA GPU: set `DEVICE = "cuda"` and `COMPUTE_TYPE = "float16"` in main.py — much faster

## Deployment (when ready to go live)

- Backend: deploy to Railway, Render, or a GPU instance on RunPod (recommended if videos are long)
- Frontend: deploy `index.html` to Vercel/Netlify, or serve it via FastAPI itself
- Update `API_BASE` in index.html to your deployed backend URL instead of localhost
- Add file size limits and rate limiting before going public, to avoid abuse
