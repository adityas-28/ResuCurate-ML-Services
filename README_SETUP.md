# How to Run the Backend Server

## Quick Start (Windows)
- Double-click `start_server.bat`, or run:

```bash
start_server.bat
```

## Manual Start

```bash
cd ResuCurate-mlServices
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Environment Variables
Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY=your_api_key_here
ALLOWED_ORIGINS=http://localhost:3000
```

## Server Endpoints
- `GET /` - API status
- `GET /health` - Health check
- `POST /api/ats-score` - Upload PDF and get ATS score

