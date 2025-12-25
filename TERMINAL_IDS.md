# 🎯 Terminal IDs Reference

## Keep This Handy!

### Terminal 1️⃣ - BACKEND
**Terminal ID**: `1b4603b8-bbcc-4fb7-b188-468f76f85de6`
```
Purpose: Run backend FastAPI server
Command: python run_backend.py
Location: /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/
URL: http://localhost:8000
Status: ✅ RUNNING
```

### Terminal 2️⃣ - NGROK
**Terminal ID**: `25e23cda-161d-4d12-a653-2802baac317c`
```
Purpose: Expose backend to internet
Command: ngrok http 8000 --log=stdout
Location: /Users/aayushtiwari/Desktop/AGENITC_BOOK/
PUBLIC URL: https://marmoreal-luisa-honeyful.ngrok-free.dev
Status: ✅ RUNNING
```

### Terminal 3️⃣ - FRONTEND (Use Only When Rebuilding)
```
Purpose: Build frontend from React source
Command: npm run build
Location: /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/frontend/
Then: mv dist ../backend/app/static/
```

---

## 📋 Checklist

- [x] Backend Terminal running
- [x] Ngrok Terminal running  
- [x] Frontend built and in backend/app/static/
- [x] http://localhost:8000 accessible locally
- [x] https://marmoreal-luisa-honeyful.ngrok-free.dev accessible worldwide

---

## ⚡ Quick Commands

### Start Everything (IN ORDER)
```bash
# Terminal 1 - Backend
python /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/run_backend.py

# Terminal 2 - Ngrok (after backend is running)
ngrok http 8000 --log=stdout
```

### Rebuild Frontend
```bash
cd /Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31/frontend
npm run build
rm -rf ../backend/app/static && mv dist ../backend/app/static
# Then restart Backend Terminal
```

### Check Port Usage
```bash
lsof -i :8000
```

### Kill Old Processes
```bash
kill -9 44093  # Replace with PID from lsof
```

---

**Remember**: Each terminal has ONE job. Do NOT mix purposes! 🎯
