# How to Run the Backend Server

## Quick Start

### Option 1: Using the Batch Script (Windows)
Double-click `start_server.bat` or run it from the command line:
```bash
start_server.bat
```

### Option 2: Manual Start

1. **Navigate to the backend directory:**
   ```bash
   cd ResuCurate-mlServices
   ```

2. **Activate virtual environment (if you have one):**
   ```bash
   .venv\Scripts\activate
   ```
   
   If you don't have a virtual environment, create one:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install dependencies (if not already installed):**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Verify the server is running:**
   - Open your browser and go to: `http://localhost:8000`
   - You should see: `{"message":"ResuCurate ML Services API","status":"running"}`
   - Or check health: `http://localhost:8000/health`

## Environment Variables

Make sure you have a `.env` file in the `ResuCurate-mlServices` directory with your Google Generative AI API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Troubleshooting

- **Port 8000 already in use:** Change the port in `main.py` or kill the process using port 8000
- **Module not found errors:** Make sure all dependencies are installed: `pip install -r requirements.txt`
- **API key errors:** Check your `.env` file has the correct `GOOGLE_API_KEY`

## Server Endpoints

- `GET /` - API status
- `GET /health` - Health check
- `POST /api/ats-score` - Upload PDF and get ATS score
