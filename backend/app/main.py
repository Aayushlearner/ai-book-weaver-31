from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

from .groq_provider import GroqProvider
from .agents import (
    IndexingAgent,
    TOCGeneratorAgent,
    TOCMergerAgent,
    WritingAgent,
    ChapterPlan,
    BookPlan,
    ChapterContent,
    BookContent,
    generate_toc_context,
)

import json
# from .image_generator import ImageGenerator # Removed

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Book Writing Backend")

# Wide-open CORS for development (no credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

class PlanRequest(BaseModel):
    topic: str
    num_chapters: int = 8
    tone: Optional[str] = "casual"
    additional_content: Optional[str] = None

@app.post("/plan", response_model=BookPlan)
async def plan(req: PlanRequest):
    logger.info(f"Plan request received: topic={req.topic}, num_chapters={req.num_chapters}, tone={req.tone}, additional_content={bool(req.additional_content)}")
    try:
        provider = GroqProvider()
        logger.info(f"GroqProvider initialized, available: {provider.is_available()}")

        # Generate TOC context from real books
        logger.info("Generating TOC context from real books...")
        toc_context = generate_toc_context(req.topic)
        logger.info(f"TOC context generated: {len(toc_context)} characters")

        # Combine TOC context with user additional content
        combined_context = toc_context
        if req.additional_content:
            combined_context += f"\n\nUSER PROVIDED ADDITIONAL CONTENT:\n{req.additional_content}\n\nPlease incorporate these specific ideas and content into the book structure and chapter planning."

        planner = IndexingAgent(provider)
        result = planner.plan(req.topic, num_chapters=req.num_chapters, tone=req.tone, toc_context=combined_context)
        logger.info(f"Plan result: title={result.title}, chapters={len(result.chapters)}")
        return result
    except Exception as e:
        logger.error(f"An unhandled exception occurred in /plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

class WriteRequest(BaseModel):
    book_title: str
    topic: str
    chapters: List[ChapterPlan]
    tone: Optional[str] = "casual"

@app.post("/write", response_model=BookContent)
async def write(req: WriteRequest):
    provider = GroqProvider()
    writer = WritingAgent(provider)
    return writer.write(req.book_title, req.topic, req.chapters, tone=req.tone)

class GenerateRequest(BaseModel):
    topic: str
    num_chapters: int = 8
    tone: Optional[str] = "casual"
    format: Optional[str] = "json"  # json|docx|pdf

@app.post("/generate")
async def generate(req: GenerateRequest):
    provider = GroqProvider()
    planner = IndexingAgent(provider)
    plan = planner.plan(req.topic, num_chapters=req.num_chapters, tone=req.tone)
    writer = WritingAgent(provider)
    book = writer.write(plan.title, req.topic, plan.chapters, tone=req.tone)
    return {"title": book.title, "chapters": [c.__dict__ for c in book.chapters]}

react_build_path = Path("dist")
if react_build_path.exists():

    # 1️⃣ Serve /assets folder (images, fonts, etc.)
    app.mount(
        "/assets",
        StaticFiles(directory=react_build_path / "assets", html=False),
        name="assets"
    )

    # 2️⃣ Serve static JS/CSS if needed
    if (react_build_path / "static").exists():
        app.mount(
            "/static",
            StaticFiles(directory=react_build_path / "static", html=False),
            name="static"
        )

    # 3️⃣ Serve specific files
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(react_build_path / "manifest.json")

    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(react_build_path / "favicon.ico")

    # 4️⃣ Catch-all route for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API endpoints to pass through
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Serve React SPA
        return FileResponse(react_build_path / "index.html")

else:
    print("⚠️ dist folder not found. Run: npm run build")

    @app.get("/")
    async def no_build():
        return {"error": "React build not found. Run npm run build first."}