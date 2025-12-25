#!/usr/bin/env python
"""Run backend server"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/aayushtiwari/Desktop/AGENITC_BOOK/ai-book-weaver-31')

import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload for now
    )
