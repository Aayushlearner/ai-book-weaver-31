# 🚀 Ngrok Deployment Guide

## Current Status ✅

**Live Public URL**: `https://marmoreal-luisa-honeyful.ngrok-free.dev`

Your backend + frontend is now live and accessible from anywhere in the world!

---

## 🎯 3-Terminal Setup

### Terminal 1: Backend Server (ALWAYS USE THIS)
```bash
# Backend Terminal ID: 1b4603b8-bbcc-4fb7-b188-468f76f85de6
python /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/run_backend.py

# Local URL: http://localhost:8000
# What it does: Runs FastAPI server with frontend static files bundled
```

### Terminal 2: Ngrok Tunnel (ALWAYS USE THIS FOR PUBLIC ACCESS)
```bash
# Ngrok Terminal ID: 25e23cda-161d-4d12-a653-2802baac317c
ngrok http 8000 --log=stdout

# Public URL: https://marmoreal-luisa-honeyful.ngrok-free.dev
# What it does: Exposes your local backend to the internet
```

### Terminal 3: Frontend Dev (ONLY WHEN REBUILDING)
```bash
# Use this ONLY when you need to rebuild frontend
cd /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/frontend
npm run build

# Then copy dist to backend:
rm -rf ../backend/app/static && mv dist ../backend/app/static
```

---

## 📍 Architecture

```
┌─────────────────────────────────────┐
│  Frontend (React + Vite)            │
│  Built & Bundled in backend/app/static/
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│  http://localhost:8000              │
│  - Serves static frontend files     │
│  - API endpoints (/plan, /write)    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Ngrok Tunnel                       │
│  https://marmoreal-luisa-honeyful... │
│  - Public internet access           │
│  - HTTPS enabled                    │
└─────────────────────────────────────┘
```

---

## 🔄 Workflow

### 1. **Local Development**
```
- Make changes to backend (agents.py, main.py, etc)
- Backend Terminal will auto-reload if you have reload=True
- Open http://localhost:8000 to test
```

### 2. **Frontend Changes**
```
- Make changes to React components (src/components/, src/pages/)
- Run: npm run build (Terminal 3)
- Copy dist to backend
- Refresh http://localhost:8000 to see changes
```

### 3. **Share With Others**
```
- Keep Ngrok Terminal running
- Share this URL: https://marmoreal-luisa-honeyful.ngrok-free.dev
- Anyone worldwide can access your app!
```

---

## ⚠️ Important Rules

1. **NEVER** mix terminal purposes:
   - Backend Terminal = Backend code only
   - Ngrok Terminal = Tunnel exposure only
   - Frontend Terminal = Rebuild only

2. **Keep Terminals Dedicated:**
   - Once you start a terminal for a purpose, use ONLY that terminal for that purpose
   - This prevents confusion and port conflicts

3. **Ngrok URL Changes:**
   - Every time you restart Ngrok, you get a NEW public URL
   - If using ngrok.com account, you can get a static domain (pro feature)
   - Current URL works until you restart ngrok

---

## 🛠️ Troubleshooting

### Backend won't start on port 8000
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Try again
python run_backend.py
```

### Ngrok tunnel not working
```bash
# Check if ngrok is authenticated
ngrok config add-authtoken <your-auth-token>

# Restart ngrok
ngrok http 8000 --log=stdout
```

### Frontend changes not showing
```bash
# Rebuild frontend
npm run build

# Move to backend
rm -rf backend/app/static && mv frontend/dist backend/app/static

# Restart backend server
# Ctrl+C in Backend Terminal, then restart it
```

### Port 8000 already in use
```bash
# Find and kill existing process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Restart backend
python run_backend.py
```

---

## 📝 Files Modified

- ✅ `/backend/app/main.py` - Updated to serve static files from `backend/app/static/`
- ✅ `/backend/app/static/` - Holds compiled frontend (index.html, assets, etc)
- ✅ `NGROK_DEPLOYMENT_LIVE.md` - This file!

---

## 🎉 You're All Set!

Your application is:
- ✅ Built and bundled
- ✅ Running locally on http://localhost:8000
- ✅ Exposed publicly via ngrok
- ✅ Accessible worldwide!

Keep those 3 terminals running and you're good to go! 🚀
