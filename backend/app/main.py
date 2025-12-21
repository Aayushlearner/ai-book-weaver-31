from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request
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
from .ollama_provider import OllamaProvider
from .agents import (
    IndexingAgent,
    TOCGeneratorAgent,
    TOCMergerAgent,
    CritiqueAgent,
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

        # Use multi-agent TOC generation
        perspectives = ["foundational", "applied", "strategic", "future-oriented"]
        toc_plans = []
        for perspective in perspectives:
            agent = TOCGeneratorAgent(provider, perspective)
            plan = agent.generate_toc(req.topic, num_chapters=req.num_chapters, tone=req.tone, toc_context=combined_context)
            toc_plans.append(plan)

        merger = TOCMergerAgent(provider)
        result = merger.merge_tocs(req.topic, req.num_chapters, req.tone, toc_plans, combined_context)
        critique = CritiqueAgent(provider)
        final_result = critique.critique_toc(result, req.topic, req.num_chapters, req.tone, combined_context)
        logger.info(f"Plan result: title={final_result.title}, chapters={len(final_result.chapters)}")
        return final_result
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
    # Serve static files (JS, CSS, images, etc.)
    # app.mount("/static", StaticFiles(directory="dist/static"), name="static")

    # Serve other assets
    app.mount("/assets", StaticFiles(directory="dist/assets", check_dir=False), name="assets")

    @app.get("/manifest.json")
    async def get_manifest():
        return FileResponse("dist/manifest.json")

    @app.get("/favicon.ico")
    async def get_favicon():
        return FileResponse("dist/favicon.ico")

    # Catch-all route for React Router (must be last)
    @app.get("/{full_path:path}")
    async def serve_react_app(request: Request, full_path: str):
        # If it's an API call, let it fall through to 404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # For all other routes, serve the React app
        return FileResponse("dist/index.html")
else:
    print("⚠️  React build folder not found. Please run 'npm run build' first.")

    @app.get("/")
    async def no_react_build():
        return {"message": "React app not built. Run 'npm run build' first, then restart the server."}