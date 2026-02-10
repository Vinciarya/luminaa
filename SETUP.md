# YouTube Summarizer - Setup Guide

## 🎯 Cost-Optimized Architecture

This application uses a **FastAPI backend** with aggressive caching to achieve **$0-10/month** for 1000+ videos.

### Cost Breakdown

- **Transcript Extraction**: $0 (FREE via `youtube-transcript-api`)
- **AI Summarization**: $0 (Gemini Flash FREE tier: 15 RPM × 3 keys = 45 RPM)
- **Caching**: $0 (Upstash Redis FREE tier: 10K commands/day)
- **Hosting**: $0 (Render/Railway FREE tier)

**Total**: $0/month for most use cases! 🎉

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **Redis** (local or Upstash free tier)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Linux/Mac

# Edit .env and add your API keys
# - Get FREE Gemini keys from: https://aistudio.google.com/apikey
# - Get FREE Redis URL from: https://upstash.com/
notepad .env  # Windows
# OR
nano .env     # Linux/Mac

# Run the backend
python main.py
```

Backend will start at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
# Navigate to project root
cd ..

# Install dependencies
npm install

# Backend API is already configured in .env.local
# (defaults to http://localhost:8000)

# Run the frontend
npm run dev
```

Frontend will start at: **http://localhost:5173**

---

## 🔑 Getting FREE API Keys

### Gemini API Keys (3 free accounts = 45 RPM)

1. Go to https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Repeat with 2 more Google accounts
6. Add all 3 keys to `backend/.env`:

```env
GEMINI_API_KEY_1=AIza...your_first_key
GEMINI_API_KEY_2=AIza...your_second_key
GEMINI_API_KEY_3=AIza...your_third_key
```

**Result**: 45 requests/minute, 4500 requests/day - completely FREE!

### Upstash Redis (FREE tier)

1. Go to https://upstash.com/
2. Sign up (free)
3. Create new Redis database
4. Copy the connection URL
5. Add to `backend/.env`:

```env
REDIS_URL=redis://default:password@host:port
```

**FREE tier**: 10,000 commands/day, 256MB storage

---

## 📊 Testing the Setup

### 1. Test Backend

```bash
# In backend directory
cd backend

# Test transcript extraction (FREE - no API key needed!)
python services/transcript_service.py

# Start backend
python main.py

# In another terminal, test API
curl http://localhost:8000/health
```

### 2. Test Video Analysis

```bash
# Analyze a video
curl -X POST http://localhost:8000/api/videos/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Check cache stats
curl http://localhost:8000/api/stats
```

### 3. Test Frontend

1. Open http://localhost:5173
2. Paste a YouTube URL
3. Click submit
4. Wait for analysis (5-15 seconds first time)
5. Try the same video again (should be instant from cache!)

---

## 🎓 How It Works

### Request Flow

```
User → Frontend → Backend API → Cache Check
                                    ↓
                            Cache HIT (85%+)
                                    ↓
                            Return cached data ($0 cost)

                            Cache MISS (15%)
                                    ↓
                    Extract transcript (FREE)
                                    ↓
                    Summarize with Gemini (FREE tier)
                                    ↓
                    Cache for 90 days
                                    ↓
                    Return new data
```

### Cost Optimization

**Week 1**: 10% cache hit rate

- 100 videos processed
- 90 Gemini API calls
- **Cost: $0** (free tier)

**Week 4**: 85% cache hit rate

- 400 videos total
- 60 new Gemini API calls
- **Cost: $0** (free tier)

**Month 6**: 95% cache hit rate

- 2000 videos total
- 100 new Gemini API calls
- **Cost: $0** (free tier)

---

## 🐛 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

### Redis connection failed

**Error**: `Redis connection failed`

**Solution**:

```bash
# Option 1: Use Upstash (recommended)
# Get free Redis URL from: https://upstash.com/
# Add to backend/.env

# Option 2: Install Redis locally
# Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Start Redis
redis-server
```

### Frontend can't connect to backend

**Error**: `Failed to fetch` or `Network error`

**Solution**:

```bash
# 1. Make sure backend is running
cd backend
python main.py

# 2. Check backend URL in frontend/.env.local
# Should be: VITE_API_URL=http://localhost:8000

# 3. Check CORS settings in backend/main.py
# Frontend URL should be allowed
```

### Rate limit errors

**Error**: `429 Too Many Requests`

**Solution**:

```bash
# Check API usage
curl http://localhost:8000/api/stats

# Add more API keys (up to 3 free)
# Edit backend/.env and add GEMINI_API_KEY_2, GEMINI_API_KEY_3
```

---

## 🚢 Deployment

### Deploy Backend (Render - FREE)

1. Push code to GitHub
2. Go to https://render.com/
3. Create new "Web Service"
4. Connect GitHub repo
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `python main.py`
7. Add environment variables (Gemini keys, Redis URL)
8. Deploy!

**Cost**: $0/month (free tier)

### Deploy Frontend (Vercel - FREE)

1. Go to https://vercel.com/
2. Import GitHub repo
3. Set environment variable: `VITE_API_URL=https://your-backend.onrender.com`
4. Deploy!

**Cost**: $0/month (free tier)

---

## 📈 Monitoring

### Check Usage Statistics

```bash
curl http://localhost:8000/api/stats
```

Response:

```json
{
  "cache": {
    "total_videos": 150,
    "popular_videos": 25,
    "total_views": 500,
    "cache_enabled": true
  },
  "api_keys": {
    "key_1": {
      "requests_last_minute": 5,
      "requests_today": 120,
      "rpm_remaining": 10,
      "rpd_remaining": 1380
    }
  }
}
```

---

## 💡 Tips for Maximum Cost Savings

1. **Let cache warm up**: First week will have low cache hit rate, but it improves to 85%+ by week 4
2. **Use multiple API keys**: Get 3 free Gemini accounts for 45 RPM capacity
3. **Monitor popular videos**: Videos with >10 requests are cached forever (permanent $0 cost)
4. **Use Upstash Redis**: Free tier is perfect for this use case
5. **Deploy on free tiers**: Render + Vercel = $0/month hosting

---

## 📝 Next Steps

1. ✅ Set up backend with Gemini keys
2. ✅ Configure Redis (Upstash recommended)
3. ✅ Test video analysis
4. ✅ Check cache is working
5. ✅ Monitor usage statistics
6. 🚀 Deploy to production (optional)

---

## 🤝 Support

- Backend API Docs: http://localhost:8000/docs
- Backend Health: http://localhost:8000/health
- Frontend: http://localhost:5173

For issues, check the troubleshooting section above!
