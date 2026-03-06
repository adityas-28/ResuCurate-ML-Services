# Backend Deployment Guide

## Overview
This FastAPI backend should be deployed separately from your frontend. Your frontend will call the deployed backend URL for API requests.

## Quick Deploy Options

### Option 1: Railway
- Create a new project and deploy from GitHub
- Add environment variables:
  - `GOOGLE_API_KEY`
  - `ALLOWED_ORIGINS` (your frontend URL)
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Render
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add environment variables:
  - `GOOGLE_API_KEY`
  - `ALLOWED_ORIGINS`

### Option 3: Fly.io
- Set secrets: `fly secrets set GOOGLE_API_KEY=... ALLOWED_ORIGINS=...`
- Deploy: `fly deploy`

### Option 4: PythonAnywhere
- Create a web app pointing to `main.py`/ASGI config
- Add environment variables in the dashboard

## Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key_here
ALLOWED_ORIGINS=https://your-frontend-url.example
```

## Testing Deployment
- Health: `GET /health`
- ATS scan: `POST /api/ats-score`

## CORS Notes
For production, set `ALLOWED_ORIGINS` to your exact frontend origin (including `https://`).

