# Video Transcriber

The application accepts an MP4 video, extracts its audio using FFmpeg, transcribes the speech, translates it into English, and allows the transcript to be downloaded.

---

## Features

- Upload MP4 videos
- Automatic audio extraction using FFmpeg
- Speech-to-text using Faster-Whisper Large-v3
- Automatically translates all speech into English
- Supports Hindi, English, and mixed (Hinglish) speech
- Download transcript as TXT or SRT
- Simple browser-based interface

---

## Project Structure

```
video-transcriber/
│
├── backend/
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   └── index.html
│
├── .gitignore
└── README.md
```

---

## Requirements

- Python 3.11 or newer
- FFmpeg installed and added to PATH

Verify FFmpeg installation:

```bash
ffmpeg -version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/AnshKaul8/video_transcriber.git
```

Go to the project:

```bash
cd video_transcriber/backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run Backend

Inside the **backend** folder run:

```bash
python -m uvicorn main:app --reload --port 8000
```

The backend will be available at:

```
http://localhost:8000
```

The first launch will download the **Large-v3 Whisper model**, which may take a few minutes depending on your internet connection.

---

## Run Frontend

Open

```
frontend/index.html
```

in your browser.

Upload an MP4 video and click **Generate Transcript**.

---

## Output

Generated transcripts are saved inside:

```
backend/transcripts/
```

Available formats:

- TXT
- SRT

Temporary uploaded videos are automatically removed after processing.

---

## Tech Stack

- Python
- FastAPI
- Faster-Whisper
- FFmpeg
- HTML
- CSS
- JavaScript

---

## Notes

- Only MP4 videos are supported.
- Longer videos take more processing time.
- The project currently runs locally.

---

## License

This project is intended for educational and personal use.
