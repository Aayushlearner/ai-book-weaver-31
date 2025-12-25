# Terminal Management Guide

## Running Backend and Frontend Separately

Your project has been configured with dedicated terminals for the backend and frontend. Follow these instructions to run them correctly.

### ✅ Current Status
- **Backend Terminal**: Running on `http://0.0.0.0:8000` (Terminal ID: `045e4d0e-37ce-4857-b1b4-4ff75f56a87b`)
- **Frontend Terminal**: Running on `http://localhost:5173` (Terminal ID: `de659c85-1826-47a3-bb1e-285a81dbf124`)

---

## How to Run (Method 1: Using VS Code Tasks)

1. **Open Command Palette**: Press `Cmd + Shift + P`
2. **Run All Tasks**: Type `Run All Tasks`
   - Select `All - Start Backend & Frontend` to run both servers
3. **Or Run Separately**:
   - Type `Run Task` → Select `Backend - Start Server`
   - Type `Run Task` → Select `Frontend - Start Dev Server`

### Task Details:
- **Backend - Start Server**: Runs `python run_backend.py`
- **Frontend - Start Dev Server**: Runs `npm run dev` in the frontend directory
- **All - Start Backend & Frontend**: Runs both simultaneously in dedicated panels

---

## How to Run (Method 2: Using Terminal Commands)

### Backend Terminal (Python Server)
```bash
cd /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31
python run_backend.py
```

### Frontend Terminal (React/Vite Dev Server)
```bash
cd /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/frontend
npm run dev
```

---

## 🎯 Important Rules

✅ **ALWAYS use separate terminals:**
- Backend changes → Use **Backend Terminal**
- Frontend changes → Use **Frontend Terminal**
- Don't mix commands in the same terminal

✅ **Keep terminals dedicated:**
- Once started, don't use backend terminal for frontend commands
- Once started, don't use frontend terminal for backend commands

✅ **Terminal Panel Labels:**
- Look for dedicated panels at the bottom of VS Code
- Backend panel shows "Backend - Start Server"
- Frontend panel shows "Frontend - Start Dev Server"

---

## Server URLs

| Server | URL | Port |
|--------|-----|------|
| Backend (FastAPI) | http://0.0.0.0:8000 | 8000 |
| Frontend (Vite) | http://localhost:5173 | 5173 |
| Backend (Local) | http://localhost:8000 | 8000 |

---

## Stopping the Servers

- Press `Ctrl+C` in the respective terminal for each server
- Or use VS Code's task management to terminate tasks

---

## Configuration Files

- **Backend**: `run_backend.py`
- **Frontend**: `frontend/package.json`
- **VS Code Tasks**: `.vscode/tasks.json` (configured for dedicated terminals)

---

## Troubleshooting

### Backend won't start
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`

### Frontend won't start
- Check npm is installed: `npm --version`
- Install dependencies: `npm install` (in frontend directory)
- Check port 5173 is not in use: `lsof -i :5173`

### Bun vs npm
- Project uses `npm` (not bun)
- Always run: `npm run dev` instead of `bun run dev`
