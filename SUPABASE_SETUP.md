# Supabase Integration Guide

## Overview

This guide shows you how to integrate Supabase as your Backend-as-a-Service (BaaS) for ResuCurate. Supabase will handle:
- **Storage**: PDF file storage
- **Database**: Scan results and user history
- **Authentication**: User management (optional)
- **Edge Functions**: Serverless functions (optional)

## Architecture

```
Frontend (Vercel) 
    ↓
Supabase Edge Function (optional proxy)
    ↓
FastAPI Backend (ML Services) → Supabase Storage & Database
```

## Setup Steps

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in:
   - **Name**: ResuCurate
   - **Database Password**: (save this!)
   - **Region**: Choose closest to your users
4. Wait for project to be created (~2 minutes)

### 2. Get Your Supabase Credentials

In your Supabase dashboard:
1. Go to **Settings** → **API**
2. Copy:
   - **Project URL** (SUPABASE_URL)
   - **Service Role Key** (SUPABASE_SERVICE_ROLE_KEY) - Keep this secret!
   - **Anon Key** (SUPABASE_ANON_KEY) - For frontend

### 3. Create Storage Bucket

1. Go to **Storage** in Supabase dashboard
2. Click **New bucket**
3. Name: `resumes`
4. **Public bucket**: OFF (private)
5. **File size limit**: 10 MB
6. **Allowed MIME types**: `application/pdf`
7. Click **Create bucket**

### 4. Set Up Database Schema

Run the migration SQL:

1. Go to **SQL Editor** in Supabase dashboard
2. Click **New query**
3. Copy and paste the contents of `supabase/migrations/001_create_scan_results.sql`
4. Click **Run**

This creates:
- `scan_results` table for storing scan history
- Row Level Security (RLS) policies
- Indexes for performance

### 5. Configure Environment Variables

Add to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here

# Enable Supabase integration
USE_SUPABASE=true

# Your existing variables
GOOGLE_API_KEY=your-google-api-key
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
```

### 6. Update Frontend (Optional - for Auth)

If you want to use Supabase Auth in your frontend:

```bash
npm install @supabase/supabase-js
```

```javascript
// lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

## Deployment Options

### Option A: FastAPI + Supabase (Recommended)

Keep your FastAPI backend but use Supabase for storage/database:

1. **Deploy FastAPI** to Railway/Render (as before)
2. **Set environment variables**:
   - `USE_SUPABASE=true`
   - `SUPABASE_URL=...`
   - `SUPABASE_SERVICE_ROLE_KEY=...`
3. Your FastAPI backend will automatically:
   - Save PDFs to Supabase Storage
   - Save scan results to Supabase Database

### Option B: Supabase Edge Functions Only

Use Supabase Edge Functions as a proxy to your FastAPI backend:

1. **Deploy FastAPI** to Railway/Render
2. **Deploy Edge Function**:
   ```bash
   # Install Supabase CLI
   npm install -g supabase
   
   # Login
   supabase login
   
   # Link project
   supabase link --project-ref your-project-id
   
   # Deploy function
   supabase functions deploy ats-scan
   ```
3. Set environment variable in Supabase:
   - `FASTAPI_BACKEND_URL`: Your FastAPI backend URL

### Option C: Full Supabase (Advanced)

Convert everything to Supabase Edge Functions (requires rewriting Python to TypeScript/Deno).

## API Endpoints

### With Supabase Enabled

- `POST /api/ats-score` - Upload resume and get ATS score (saves to Supabase)
- `GET /api/scan-history` - Get user's scan history (requires auth token)

### Request Headers

For authenticated requests:
```
Authorization: Bearer <supabase-jwt-token>
```

## Frontend Integration

### Upload Resume with Auth

```javascript
// Get Supabase client
import { supabase } from './lib/supabase'

// Get user session
const { data: { session } } = await supabase.auth.getSession()

// Upload file
const formData = new FormData()
formData.append('file', pdfFile)

const response = await fetch('https://your-backend-url/api/ats-score', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  },
  body: formData
})

const result = await response.json()
// result.scanId - ID of saved scan
// result.fileUrl - URL to stored PDF
```

### Get Scan History

```javascript
const response = await fetch('https://your-backend-url/api/scan-history', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
})

const { history } = await response.json()
```

## Database Schema

### scan_results Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to auth.users |
| file_path | TEXT | Path in Supabase Storage |
| filename | TEXT | Original filename |
| overall_score | INTEGER | ATS score (0-100) |
| field | TEXT | Detected field |
| keyword_relevance | INTEGER | Keyword score |
| formatting_score | INTEGER | Formatting score |
| experience_score | INTEGER | Experience score |
| strengths | JSONB | Array of strengths |
| improvements | JSONB | Array of improvements |
| links | JSONB | Extracted links object |
| scanned_at | TIMESTAMPTZ | When scan was performed |
| created_at | TIMESTAMPTZ | Record creation time |

## Row Level Security (RLS)

The database uses RLS policies:
- Users can only see their own scan results
- Users can insert their own scan results
- Users can delete their own scan results
- Service role has full access (for backend operations)

## Storage Structure

```
resumes/
  ├── {user_id}/
  │   ├── {uuid}.pdf
  │   └── {uuid}.pdf
  └── anonymous/
      └── {uuid}.pdf
```

## Testing

1. **Test Storage Upload**:
   ```python
   from app.services.supabase_storage import upload_resume
   
   with open("resume.pdf", "rb") as f:
       result = upload_resume(f.read(), "resume.pdf")
   print(result["public_url"])
   ```

2. **Test Database**:
   ```python
   from app.services.supabase_db import save_scan_result
   
   result = save_scan_result(
       user_id=None,
       file_path="test/file.pdf",
       scan_result={"overallScore": 85},
       filename="test.pdf"
   )
   ```

## Troubleshooting

### "Supabase credentials not found"
- Check `.env` file has `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Restart your server after adding env vars

### "Bucket not found"
- Create the `resumes` bucket in Supabase dashboard
- Check bucket name matches `BUCKET_NAME` in `supabase_storage.py`

### "Table does not exist"
- Run the migration SQL in Supabase SQL Editor
- Check table name is `scan_results`

### CORS Errors
- Add your frontend URL to Supabase CORS settings
- Check `ALLOWED_ORIGINS` in backend env vars

## Cost Considerations

Supabase Free Tier includes:
- 500 MB database storage
- 1 GB file storage
- 2 GB bandwidth
- 50,000 monthly active users

For production, consider:
- **Pro Plan**: $25/month (8 GB database, 100 GB storage)
- **Team Plan**: $599/month (for larger scale)

## Next Steps

1. ✅ Set up Supabase project
2. ✅ Create storage bucket
3. ✅ Run database migration
4. ✅ Add environment variables
5. ✅ Test upload and save
6. ✅ Integrate with frontend
7. ✅ Deploy backend with Supabase enabled
