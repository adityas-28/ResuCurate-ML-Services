# Backend Deployment Guide

## Overview
Your FastAPI backend needs to be deployed separately from your Vercel frontend. The frontend will make API calls to your deployed backend URL.

**Note**: If you're using Supabase as BaaS, see [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for complete Supabase integration guide.

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)
1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub repository
4. Railway will auto-detect Python and install dependencies
5. Add environment variables:
   - `GOOGLE_API_KEY`: Your Google API key from `.env`
   - `ALLOWED_ORIGINS`: Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)
6. Railway will provide a URL like `https://your-app.railway.app`
7. Update your frontend to use this URL for API calls

### Option 2: Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. Add environment variables in the dashboard:
   - `GOOGLE_API_KEY`: Your Google API key
   - `ALLOWED_ORIGINS`: Your Vercel frontend URL
6. Render will provide a URL like `https://your-app.onrender.com`
7. Update your frontend to use this URL

### Option 3: Fly.io
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Run `fly launch` in your project directory
3. Follow the prompts
4. Set secrets: `fly secrets set GOOGLE_API_KEY=your_key ALLOWED_ORIGINS=your_vercel_url`
5. Deploy: `fly deploy`

### Option 4: PythonAnywhere
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload your code via Git or file upload
3. Create a web app and point it to your `main.py`
4. Set environment variables in the web app configuration
5. Use the provided URL

## Environment Variables

Set these in your deployment platform:

```bash
GOOGLE_API_KEY=your_google_api_key_here
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
```

**If using Supabase** (optional):
```bash
USE_SUPABASE=true
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**Important**: Replace `https://your-vercel-app.vercel.app` with your actual Vercel deployment URL.

## Updating Frontend

After deploying, update your frontend code to use the backend URL:

```javascript
// Example: In your frontend API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-backend.railway.app';

// Or for React/Vite
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-backend.railway.app';
```

## Testing Deployment

1. Check health endpoint: `https://your-backend-url/health`
2. Should return: `{"status": "healthy"}`
3. Test ATS endpoint: `POST https://your-backend-url/api/ats-score`

## CORS Configuration

The backend is configured to accept requests from:
- Development: All origins (`*`)
- Production: Only origins specified in `ALLOWED_ORIGINS` environment variable

Make sure to set `ALLOWED_ORIGINS` to your Vercel URL in production!

## Troubleshooting

### 502 Bad Gateway
- Check if the server is running
- Verify environment variables are set
- Check logs in your deployment platform

### CORS Errors
- Ensure `ALLOWED_ORIGINS` includes your Vercel URL
- Check that the URL matches exactly (including `https://`)

### Module Not Found
- Ensure all dependencies are in `requirements.txt`
- Check build logs for missing packages

## Cost Considerations

- **Railway**: Free tier available, then pay-as-you-go
- **Render**: Free tier with limitations, paid plans available
- **Fly.io**: Free tier available, then pay-as-you-go
- **PythonAnywhere**: Free tier available, paid plans available
