# agents.py
from typing import List, Optional
from pydantic import BaseModel
from .groq_provider import GroqProvider
import json
import re
import logging
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from duckduckgo_search import DDGS
import time
import os
import uuid

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------
# Data classes
# ---------------------------
class ChapterPlan(BaseModel):
    title: str
    summary: str
    subtopics: List[str] = []


class BookPlan(BaseModel):
    title: str
    chapters: List[ChapterPlan]


class ChapterContent(BaseModel):
    title: str
    content: str


class BookContent(BaseModel):
    title: str
    chapters: List[ChapterContent]


# ---------------------------
# Prompt templates (all tones)
# ---------------------------
PLANNER_SYSTEM = (
    "You are an expert educational content planner specializing in creating engaging, modern, and pedagogically structured book outlines. "
    "You design compelling learning journeys that progress logically from foundational concepts to advanced applications. "
    "You create eye-catching, action-oriented chapter titles that capture readers' attention while ensuring each chapter builds upon previous knowledge. "
    "You focus on practical applications, modern perspectives, and real-world value while maintaining academic rigor. "
    "You strictly return valid JSON only."
)

PLANNER_SYSTEM_FORMAL = (
    "You are a distinguished academic content planner specializing in creating comprehensive, scholarly, and methodically structured book outlines. "
    "You design rigorous intellectual journeys that progress systematically from theoretical foundations to advanced scholarly applications. "
    "You create precise, authoritative chapter titles that reflect academic depth while ensuring logical progression of complex concepts. "
    "You emphasize theoretical frameworks, empirical evidence, and scholarly discourse while maintaining professional academic standards. "
    "You strictly return valid JSON only."
)

PLANNER_SYSTEM_ACADEMIC = (
    "You are a renowned scholarly content planner specializing in creating erudite, research-oriented, and intellectually rigorous book outlines. "
    "You design sophisticated academic journeys that progress from foundational theories to cutting-edge scholarly applications. "
    "You create sophisticated, research-informed chapter titles that demonstrate academic excellence while ensuring systematic development of complex ideas. "
    "You prioritize theoretical depth, methodological rigor, and scholarly discourse while maintaining the highest academic standards. "
    "IMPORTANT: When provided with real-world Table of Contents or index data, you MUST analyze them and adapt the structure, numbering and style to reflect authentic academic TOCs. "
    "CRITICAL: Return ONLY simple chapter objects with 'title' and 'summary' fields. Do NOT include sections, subsections, or complex nested structures. "
    "Each chapter should be a standalone unit with a clear, academic title and comprehensive summary."
)

PLANNER_SYSTEM_STORYTELLING = (
    "You are a masterful narrative content planner specializing in creating compelling, story-driven, and emotionally engaging book outlines. "
    "You design captivating journeys that unfold like great narratives, progressing from intriguing beginnings to transformative conclusions. "
    "You create vivid, story-like chapter titles that draw readers in while ensuring each chapter advances the overall narrative arc. "
    "You focus on human elements, real-world stories, and transformative experiences while maintaining narrative coherence. "
    "You strictly return valid JSON only."
)

# User templates: casual/formal/academic/storytelling.
PLANNER_USER_TMPL = (
    "Generate a professional, engaging, and pedagogically structured Table of Contents for a book based on the user's given topic.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "- Create a compelling, specific book title that positions the topic professionally and attractively\n"
    "- Produce exactly {num_chapters} chapters with engaging, action-oriented titles\n"
    "- Each chapter MUST be numbered: 'Chapter 1: [Title]', 'Chapter 2: [Title]', etc.\n"
    "- Write detailed 2-3 sentence summaries that explain the chapter's value and practical focus\n"
    "- For each chapter, provide 3-5 relevant subtopics that outline the key sections within that chapter\n"
    "- Ensure subtopics are unique and specific to each chapter, differing significantly between chapters to provide diverse and comprehensive coverage\n"
    "- Ensure logical progression: fundamentals → practical skills → advanced applications → business impact → future trends\n"
    "- Include modern perspectives: AI integration, cloud computing, sustainability, ethics, MLOps, edge computing\n"
    "- Make titles specific and engaging, not generic or academic\n"
    "- Focus on practical applications and real-world value\n"
    "- Each chapter should build upon previous knowledge while offering unique insights\n\n"
    "ENGAGING CHAPTER STRUCTURE:\n"
    "1. Foundation: Core concepts with modern context and practical relevance\n"
    "2. Practical Skills: Hands-on techniques, tools, and methodologies\n"
    "3. Advanced Applications: Sophisticated use cases and optimization strategies\n"
    "4. Industry Impact: Real-world applications across different sectors\n"
    "5. Business Strategy: ROI, implementation, and organizational transformation\n"
    "6. Future Vision: Emerging trends, predictions, and next-generation technologies\n"
    "7. Getting Started: Actionable implementation roadmap and best practices\n\n"
    "EXCELLENT EXAMPLES:\n"
    'Good: "Chapter 1: Demystifying Machine Learning: From Buzzword to Business Reality"\n'
    'Bad: "Introduction to Machine Learning"\n\n'
    'Good: "Chapter 3: Building Production-Ready ML Systems: From Prototype to Scale"\n'
    'Bad: "Implementing Machine Learning Solutions"\n\n'
    'Good: "Chapter 5: The AI-Powered Enterprise: Transforming Business Through Intelligent Automation"\n'
    'Bad: "Machine Learning in Business"\n\n'
    "OUTPUT FORMAT:\n"
    "{{\n"
    '  "title": "Engaging Book Title That Captures the Topic\'s Modern Relevance",\n'
    '  "chapters": [\n'
    '    {{"title": "Chapter 1: Specific, Engaging Chapter Title", "summary": "Detailed 2-3 sentence explanation of what readers will learn, why it matters, and practical applications they can expect", "subtopics": ["Introduction to Core Concepts", "Modern Context and Relevance", "Practical Foundations"]}},\n'
    '    {{"title": "Chapter 2: Another Action-Oriented, Specific Title", "summary": "Clear description of the chapter\'s focus, practical value, and how it builds on previous knowledge", "subtopics": ["Key Techniques and Tools", "Hands-on Implementation", "Common Pitfalls and Solutions"]}}'
    '  ]\n'
    "}}\n\n"
    "Topic: {topic}\n"
    "Return ONLY valid JSON."
)

PLANNER_USER_TMPL_FORMAL = (
    "Generate a comprehensive, methodical, and academically rigorous Table of Contents for a scholarly book based on the user's given topic.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "- Create a distinguished, authoritative book title that establishes scholarly credibility\n"
    "- Produce exactly {num_chapters} chapters with precise, professional titles\n"
    "- Each chapter MUST be numbered: 'Chapter 1: [Title]', 'Chapter 2: [Title]', etc.\n"
    "- Write detailed 2-3 sentence summaries that articulate the chapter's scholarly contribution and methodological approach\n"
    "- For each chapter, provide 3-5 relevant subtopics that outline the key sections within that chapter\n"
    "- CRITICAL: Subtopics MUST be completely unique and specific to each chapter. No overlapping, similar, or repeated subtopics across any chapters. Each chapter's subtopics should be tailored exclusively to its own content and theme, ensuring maximum diversity and avoiding any duplication.\n"
    "- Ensure systematic progression: theoretical foundations → methodological frameworks → empirical applications → critical analysis → scholarly implications\n"
    "- Include rigorous perspectives: theoretical frameworks, methodological rigor, empirical evidence, critical discourse\n"
    "- Make titles precise and authoritative, reflecting academic depth\n"
    "- Focus on scholarly analysis and theoretical contributions\n"
    "- Each chapter should advance the scholarly discourse while building on established knowledge\n\n"
    "SCHOLARLY CHAPTER STRUCTURE:\n"
    "1. Theoretical Foundations: Core concepts with historical context and theoretical frameworks\n"
    "2. Methodological Approaches: Rigorous methods, analytical frameworks, and research methodologies\n"
    "3. Empirical Applications: Evidence-based applications and case studies\n"
    "4. Critical Analysis: Theoretical critiques, limitations, and scholarly debates\n"
    "5. Scholarly Implications: Contributions to the field and future research directions\n"
    "6. Professional Practice: Standards, ethics, and professional applications\n"
    "7. Advanced Scholarship: Cutting-edge research and theoretical developments\n\n"
    "EXCELLENT EXAMPLES:\n"
    'Good: "Chapter 1: Theoretical Foundations of Machine Learning: A Comprehensive Framework"\n'
    'Bad: "Introduction to Machine Learning"\n\n'
    'Good: "Chapter 3: Methodological Approaches to Machine Learning Implementation: A Systematic Analysis"\n'
    'Bad: "Implementing Machine Learning Solutions"\n\n'
    'Good: "Chapter 5: Critical Analysis of Machine Learning Applications: Theoretical and Practical Implications"\n'
    'Bad: "Machine Learning in Business"\n\n'
    "OUTPUT FORMAT:\n"
    "{{\n"
    '  "title": "Distinguished Scholarly Title That Establishes Academic Authority",\n'
    '  "chapters": [\n'
    '    {{"title": "Chapter 1: Precise Scholarly Chapter Title", "summary": "Detailed articulation of the chapter\'s theoretical contribution, methodological approach, and scholarly significance", "subtopics": ["Historical Context and Evolution", "Core Theoretical Frameworks", "Fundamental Principles"]}},\n'
    '    {{"title": "Chapter 2: Another Methodically Structured Title", "summary": "Clear description of the chapter\'s analytical framework, empirical focus, and scholarly advancement", "subtopics": ["Methodological Frameworks", "Analytical Approaches", "Research Methodologies"]}}'
    '  ]\n'
    "}}\n\n"
    "Topic: {topic}\n"
    "Create a rigorous, scholarly, and methodically structured book outline. Return ONLY valid JSON."
)

PLANNER_USER_TMPL_ACADEMIC = (
    "Generate an erudite, research-oriented, and academically formatted Table of Contents for a scholarly book based on the user's given topic.\n\n"
    "REQUIREMENTS:\n"
    "- Output must resemble a professional textbook-style TOC with PARTS, CHAPTERS, and SECTIONS.\n"
    "- Use hierarchical numbering (1, 1.1, 1.1.1) for chapters and subtopics.\n"
    "- Organize chapters under PART headings such as 'PART I: FOUNDATIONS' or 'PART II: APPLICATIONS'.\n"
    "- CRITICAL: Sections (subtopics) MUST be completely unique and specific to each chapter. No overlapping, similar, or repeated sections across any chapters. Each chapter's sections should be tailored exclusively to its own content and theme, ensuring maximum diversity and avoiding any duplication.\n"
    "- Return ONLY valid JSON. Use the example schema below and adapt to {topic}.\n\n"
    'EXAMPLE SCHEMA:\n'
    '{{\n'
    '  "title": "Academic Book Title",\n'
    '  "parts": [\n'
    '    {{"part_title": "PART I: FOUNDATIONS", "chapters": [\n'
    '      {{"chapter_number": "1", "chapter_title": "Introduction to {topic}", "sections": [\n'
    '        {{"section_number": "1.1", "section_title": "Core Concepts"}},\n'
    '        {{"section_number": "1.2", "section_title": "Theoretical Background"}}\n'
    '      ]}}\n'
    '    ]}}\n'
    '  ]\n'
    '}}\n'
    "Topic: {topic}\n"
)

PLANNER_USER_TMPL_STORYTELLING = (
    "Generate a compelling, narrative-driven Table of Contents for a story-based book on {topic}.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "- Create an engaging, story-like book title that draws readers in\n"
    "- Produce exactly {num_chapters} chapters with narrative, story-driven titles\n"
    "- Each chapter MUST be numbered: 'Chapter 1: [Title]', 'Chapter 2: [Title]', etc.\n"
    "- Write engaging 2-3 sentence summaries that build narrative tension and emotional connection\n"
    "- For each chapter, provide 3-5 relevant subtopics that outline the key story beats or sections within that chapter\n"
    "- CRITICAL: Subtopics MUST be completely unique and specific to each chapter. No overlapping, similar, or repeated subtopics across any chapters. Each chapter's subtopics should be tailored exclusively to its own content and theme, ensuring maximum diversity and avoiding any duplication.\n"
    "- Ensure narrative progression: setup → rising action → climax → falling action → resolution\n"
    "- Focus on human elements, real stories, and transformative journeys\n\n"
    "NARRATIVE CHAPTER STRUCTURE:\n"
    "1. The Beginning: Setting the scene and introducing characters\n"
    "2. The Journey: Challenges, discoveries, and personal growth\n"
    "3. The Turning Point: Key moments of change and realization\n"
    "4. The Resolution: Outcomes, lessons learned, and new beginnings\n"
    "5. The Legacy: Lasting impact and future implications\n\n"
    "OUTPUT FORMAT:\n"
    "{{\n"
    '  "title": "Engaging Narrative Title That Captures the Story\'s Essence",\n'
    '  "chapters": [\n'
    '    {{"title": "Chapter 1: Story-Driven Chapter Title", "summary": "Engaging summary that builds narrative tension and emotional connection", "subtopics": ["Setting the Scene", "Introducing Characters", "Initial Challenges"]}},\n'
    '    {{"title": "Chapter 2: Another Narrative Chapter Title", "summary": "Clear description of the chapter\'s story arc and emotional journey", "subtopics": ["Rising Action", "Key Discoveries", "Personal Growth"]}}'
    '  ]\n'
    "}}\n\n"
    "Topic: {topic}\n"
    "Return ONLY valid JSON."
)


# ---------------------------
# TOCGeneratorAgent (generates TOC with specific perspective)
# ---------------------------
class TOCGeneratorAgent:
    def __init__(self, provider: GroqProvider, perspective: str) -> None:
        self.provider = provider
        self.perspective = perspective

    def generate_toc(
        self,
        topic: str,
        num_chapters: int = 8,
        tone: str = "casual",
        toc_context: str = "",
    ) -> BookPlan:
        """
        Generate a BookPlan with a specific perspective.
        Perspectives: foundational, applied, strategic, future-oriented
        """

        # Select prompts based on tone
        if tone == "formal":
            system_prompt = PLANNER_SYSTEM_FORMAL
            user_template = PLANNER_USER_TMPL_FORMAL
        elif tone == "academic":
            system_prompt = PLANNER_SYSTEM_ACADEMIC
            user_template = PLANNER_USER_TMPL_ACADEMIC
        elif tone == "storytelling":
            system_prompt = PLANNER_SYSTEM_STORYTELLING
            user_template = PLANNER_USER_TMPL_STORYTELLING
        else:  # casual
            system_prompt = PLANNER_SYSTEM
            user_template = PLANNER_USER_TMPL

        # Add perspective instruction
        perspective_instructions = {
            "foundational": "Focus on core concepts, basic principles, and fundamental knowledge. Emphasize building strong foundations for understanding the topic.",
            "applied": "Focus on practical applications, real-world implementations, and hands-on techniques. Emphasize actionable insights and industry use cases.",
            "strategic": "Focus on high-level strategy, business impact, organizational transformation, and long-term planning. Emphasize ROI and competitive advantage.",
            "future-oriented": "Focus on emerging trends, future developments, innovations, and predictions. Emphasize cutting-edge technologies and forward-thinking approaches."
        }

        perspective_note = perspective_instructions.get(self.perspective, "")

        # Truncate context
        max_context_chars = 8000
        if toc_context and len(toc_context) > max_context_chars:
            logger.info(f"Truncating toc_context from {len(toc_context)} to {max_context_chars} chars")
            toc_context = toc_context[:max_context_chars] + "\n...[truncated]"

        # Compose messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if toc_context:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"REFERENCE TOC EXAMPLES (analyze structure, numbering, and phrasing):\n\n{toc_context}",
                }
            )

        user_msg = user_template.format(topic=topic, num_chapters=num_chapters)
        if perspective_note:
            user_msg += f"\n\nPERSPECTIVE FOCUS: {perspective_note}"

        messages.append({"role": "user", "content": user_msg})

        # Call model
        logger.info(f"TOCGeneratorAgent ({self.perspective}): sending planning request for topic='{topic}' (tone={tone})")
        raw = self.provider.complete_messages(messages, temperature=0.35, timeout=120)
        logger.info(f"TOCGeneratorAgent ({self.perspective}) raw output (truncated): {raw[:800]}")

        data = self._extract_json(raw)
        if not data:
            logger.warning(f"TOCGeneratorAgent ({self.perspective}): JSON extraction failed; falling back to safe plan")
            return self._fallback_plan(topic, num_chapters, tone)

        # Parse structured response
        title = data.get("title") or f"The Complete Guide to {topic}"
        chapters: List[ChapterPlan] = []

        if "parts" in data and isinstance(data["parts"], list):
            for part_idx, part in enumerate(data["parts"]):
                for ch_idx, ch in enumerate(part.get("chapters", [])):
                    ch_title = ch.get("chapter_title") or ch.get("title") or "Untitled Chapter"
                    sections = ch.get("sections") or []
                    subtopics = []
                    if sections:
                        sec_titles = []
                        for i, s in enumerate(sections[:4], 1):
                            if isinstance(s, dict):
                                title_sec = s.get("section_title") or s.get("title")
                                if title_sec:
                                    sec_titles.append(f"{ch.get('chapter_number', str(len(chapters)+1))}.{i} {title_sec}")
                                    subtopics.append(title_sec)
                        summary = "Includes sections: " + ", ".join(sec_titles)
                    else:
                        summary = f"Explores theoretical and applied aspects of {topic}."
                    chapters.append(ChapterPlan(title=ch_title, summary=summary, subtopics=subtopics))
        elif "chapters" in data and isinstance(data["chapters"], list):
            for ch in data["chapters"][:num_chapters]:
                if isinstance(ch, dict):
                    ch_title = ch.get("title") or ch.get("chapter_title") or "Untitled Chapter"
                    summary = ch.get("summary") or ch.get("description") or f"Important topics related to {topic}."
                    subtopics = ch.get("subtopics", [])
                    if not isinstance(subtopics, list):
                        subtopics = []
                    chapters.append(ChapterPlan(title=f"Chapter {ch.get('chapter_number', str(len(chapters)+1))}: {ch_title}", summary=summary, subtopics=subtopics))
                else:
                    chapters.append(ChapterPlan(title=str(ch), summary=f"Important concepts related to {topic}."))

        # Ensure exact number of chapters
        while len(chapters) < num_chapters:
            idx = len(chapters) + 1
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, idx, num_chapters)
            chapters.append(fallback_chapter)
        chapters = chapters[:num_chapters]

        return BookPlan(title=title, chapters=chapters)

    def _generate_diverse_fallback_chapter(self, topic: str, chapter_num: int, total_chapters: int) -> ChapterPlan:
        # Same as in IndexingAgent
        chapter_themes = {
            1: ("Foundations and Fundamentals", "Core concepts, basic principles, and foundational knowledge essential for understanding the topic.", ["Introduction", "Basic Concepts", "Key Principles", "Foundational Knowledge"]),
            2: ("Core Principles and Theory", "Theoretical frameworks, key principles, and conceptual understanding of the subject matter.", ["Theoretical Frameworks", "Core Principles", "Conceptual Models", "Fundamental Theory"]),
            3: ("Practical Applications", "Real-world implementation, practical techniques, and hands-on approaches to applying the concepts.", ["Implementation Strategies", "Practical Techniques", "Hands-on Examples", "Real-world Applications"]),
            4: ("Advanced Techniques and Methods", "Sophisticated methods, advanced strategies, and specialized approaches to the topic.", ["Advanced Methods", "Specialized Techniques", "Optimization Strategies", "Expert Approaches"]),
            5: ("Case Studies and Examples", "Real-world examples, case studies, and practical demonstrations of concepts in action.", ["Case Study Analysis", "Real-world Examples", "Practical Demonstrations", "Success Stories"]),
            6: ("Challenges and Solutions", "Common challenges, problem-solving approaches, and strategies for overcoming obstacles.", ["Common Challenges", "Problem-solving Techniques", "Solution Strategies", "Overcoming Obstacles"]),
            7: ("Future Trends and Innovations", "Emerging trends, future developments, and innovative approaches shaping the field.", ["Emerging Trends", "Future Developments", "Innovative Approaches", "Industry Evolution"]),
            8: ("Implementation and Best Practices", "Practical implementation guides, best practices, and actionable recommendations.", ["Implementation Guides", "Best Practices", "Actionable Recommendations", "Practical Tips"]),
            9: ("Ethics and Governance", "Ethical considerations, governance frameworks, and responsible practices in the field.", ["Ethical Considerations", "Governance Frameworks", "Responsible Practices", "Compliance Issues"]),
            10: ("Research and Future Directions", "Current research, future directions, and emerging areas of study.", ["Current Research", "Future Directions", "Emerging Areas", "Research Opportunities"]),
            11: ("Industry Applications", "Industry-specific applications, sector implementations, and domain-specific use cases.", ["Industry Applications", "Sector Implementations", "Domain Use Cases", "Specialized Applications"]),
            12: ("Conclusion and Strategic Roadmap", "Summary of key concepts, strategic planning, and long-term roadmaps for success.", ["Key Concepts Summary", "Strategic Planning", "Long-term Roadmaps", "Final Thoughts"])
        }

        if chapter_num in chapter_themes:
            theme_title, theme_summary, subtopics = chapter_themes[chapter_num]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary} This chapter explores {theme_title.lower()} within the context of {topic}."
        else:
            advanced_themes = [
                ("Specialized Applications", "Advanced exploration of specialized applications within the topic.", ["Specialized Techniques", "Advanced Applications", "Expert Insights", "Domain Expertise"]),
                ("Cutting-Edge Developments", "Latest developments and cutting-edge approaches in the field.", ["Latest Developments", "Cutting-edge Approaches", "Innovation Highlights", "Future Technologies"]),
                ("Integration and Optimization", "Integration strategies and optimization techniques for better performance.", ["Integration Strategies", "Optimization Techniques", "Performance Enhancement", "System Integration"]),
                ("Advanced Analytics and Insights", "Advanced analytical methods and deep insights into the topic.", ["Advanced Analytics", "Deep Insights", "Data Analysis", "Strategic Intelligence"]),
                ("Strategic Implementation", "Strategic approaches to implementing concepts and achieving goals.", ["Strategic Planning", "Implementation Tactics", "Goal Achievement", "Strategic Execution"]),
                ("Innovation and Transformation", "Innovative ideas and transformative approaches to the field.", ["Innovative Ideas", "Transformative Approaches", "Change Management", "Innovation Strategies"])
            ]
            theme_title, theme_summary, subtopics = advanced_themes[(chapter_num - 1) % len(advanced_themes)]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary}"

        return ChapterPlan(title=title, summary=summary, subtopics=subtopics)

    def _extract_json(self, text: str) -> Optional[dict]:
        # Same as in IndexingAgent
        if not text or not isinstance(text, str):
            return None

        try:
            return json.loads(text)
        except Exception:
            pass

        m = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        return None

    def _fallback_plan(self, topic: str, num_chapters: int, tone: str = "casual") -> BookPlan:
        title = f"The Complete Guide to {topic}"
        fallback_chapters = []
        for i in range(1, num_chapters + 1):
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, i, num_chapters)
            fallback_chapters.append(fallback_chapter)
        return BookPlan(title=title, chapters=fallback_chapters)


# ---------------------------
# TOCMergerAgent (merges multiple TOCs into best one)
# ---------------------------
class TOCMergerAgent:
    def __init__(self, provider: GroqProvider) -> None:
        self.provider = provider

    def merge_tocs(
        self,
        topic: str,
        num_chapters: int,
        tone: str,
        toc_plans: List[BookPlan],
        toc_context: str = "",
    ) -> BookPlan:
        """
        Merge multiple BookPlans into the best single BookPlan.
        """

        # Serialize the TOC plans
        toc_texts = []
        for i, plan in enumerate(toc_plans):
            toc_text = f"TOC {i+1} (Perspective: {getattr(plan, '_perspective', 'unknown')}):\nTitle: {plan.title}\n"
            for j, ch in enumerate(plan.chapters, 1):
                toc_text += f"{j}. {ch.title} - {ch.summary}\n"
            toc_texts.append(toc_text)

        combined_tocs = "\n\n".join(toc_texts)

        # System prompt for merger
        system_prompt = (
            "You are an expert content strategist specializing in synthesizing multiple perspectives into cohesive, high-quality book outlines. "
            "You analyze diverse TOC proposals, identify the strongest elements from each, and create a unified, superior Table of Contents. "
            "You ensure logical flow, eliminate redundancies, and maximize value for readers. "
            "You strictly return valid JSON only."
        )

        # User prompt
        user_template = (
            "You have received multiple Table of Contents proposals for a book on '{topic}' with {num_chapters} chapters in '{tone}' tone.\n\n"
            "ANALYZE EACH TOC:\n{combined_tocs}\n\n"
            "MERGE REQUIREMENTS:\n"
            "- Create a single, cohesive book title that captures the best of all proposals\n"
            "- Select and combine the strongest chapters from all TOCs (exactly {num_chapters} chapters)\n"
            "- Ensure logical progression and eliminate duplicates\n"
            "- For each chapter, provide a compelling title, detailed summary, and 3-5 subtopics\n"
            "- Maintain the '{tone}' tone throughout\n"
            "- Focus on unique value and comprehensive coverage\n\n"
            "OUTPUT FORMAT:\n"
            "{{\n"
            '  "title": "Merged Book Title",\n'
            '  "chapters": [\n'
            '    {{"title": "Chapter 1: Title", "summary": "Detailed summary", "subtopics": ["Sub1", "Sub2", "Sub3"]}},\n'
            '    ...\n'
            '  ]\n'
            "}}\n\n"
            "Return ONLY valid JSON."
        )

        user_msg = user_template.format(topic=topic, num_chapters=num_chapters, tone=tone, combined_tocs=combined_tocs)

        # Truncate if too long
        max_chars = 12000
        if len(user_msg) > max_chars:
            user_msg = user_msg[:max_chars] + "\n\n[Content truncated due to length]"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        # Call model
        logger.info(f"TOCMergerAgent: merging {len(toc_plans)} TOCs for topic='{topic}'")
        raw = self.provider.complete_messages(messages, temperature=0.3, timeout=120)
        logger.info(f"TOCMergerAgent raw output (truncated): {raw[:800]}")

        data = self._extract_json(raw)
        if not data:
            logger.warning("TOCMergerAgent: JSON extraction failed; using first TOC as fallback")
            return toc_plans[0] if toc_plans else self._fallback_plan(topic, num_chapters, tone)

        # Parse
        title = data.get("title") or toc_plans[0].title
        chapters: List[ChapterPlan] = []

        if "chapters" in data and isinstance(data["chapters"], list):
            for ch in data["chapters"][:num_chapters]:
                if isinstance(ch, dict):
                    ch_title = ch.get("title") or "Untitled Chapter"
                    summary = ch.get("summary") or f"Chapter on {topic}."
                    subtopics = ch.get("subtopics", [])
                    if not isinstance(subtopics, list):
                        subtopics = []
                    chapters.append(ChapterPlan(title=ch_title, summary=summary, subtopics=subtopics))

        # Ensure exact number
        while len(chapters) < num_chapters:
            idx = len(chapters) + 1
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, idx, num_chapters)
            chapters.append(fallback_chapter)
        chapters = chapters[:num_chapters]

        return BookPlan(title=title, chapters=chapters)

    def _generate_diverse_fallback_chapter(self, topic: str, chapter_num: int, total_chapters: int) -> ChapterPlan:
        # Same as above
        chapter_themes = {
            1: ("Foundations and Fundamentals", "Core concepts, basic principles, and foundational knowledge essential for understanding the topic.", ["Introduction", "Basic Concepts", "Key Principles", "Foundational Knowledge"]),
            2: ("Core Principles and Theory", "Theoretical frameworks, key principles, and conceptual understanding of the subject matter.", ["Theoretical Frameworks", "Core Principles", "Conceptual Models", "Fundamental Theory"]),
            3: ("Practical Applications", "Real-world implementation, practical techniques, and hands-on approaches to applying the concepts.", ["Implementation Strategies", "Practical Techniques", "Hands-on Examples", "Real-world Applications"]),
            4: ("Advanced Techniques and Methods", "Sophisticated methods, advanced strategies, and specialized approaches to the topic.", ["Advanced Methods", "Specialized Techniques", "Optimization Strategies", "Expert Approaches"]),
            5: ("Case Studies and Examples", "Real-world examples, case studies, and practical demonstrations of concepts in action.", ["Case Study Analysis", "Real-world Examples", "Practical Demonstrations", "Success Stories"]),
            6: ("Challenges and Solutions", "Common challenges, problem-solving approaches, and strategies for overcoming obstacles.", ["Common Challenges", "Problem-solving Techniques", "Solution Strategies", "Overcoming Obstacles"]),
            7: ("Future Trends and Innovations", "Emerging trends, future developments, and innovative approaches shaping the field.", ["Emerging Trends", "Future Developments", "Innovative Approaches", "Industry Evolution"]),
            8: ("Implementation and Best Practices", "Practical implementation guides, best practices, and actionable recommendations.", ["Implementation Guides", "Best Practices", "Actionable Recommendations", "Practical Tips"]),
            9: ("Ethics and Governance", "Ethical considerations, governance frameworks, and responsible practices in the field.", ["Ethical Considerations", "Governance Frameworks", "Responsible Practices", "Compliance Issues"]),
            10: ("Research and Future Directions", "Current research, future directions, and emerging areas of study.", ["Current Research", "Future Directions", "Emerging Areas", "Research Opportunities"]),
            11: ("Industry Applications", "Industry-specific applications, sector implementations, and domain-specific use cases.", ["Industry Applications", "Sector Implementations", "Domain Use Cases", "Specialized Applications"]),
            12: ("Conclusion and Strategic Roadmap", "Summary of key concepts, strategic planning, and long-term roadmaps for success.", ["Key Concepts Summary", "Strategic Planning", "Long-term Roadmaps", "Final Thoughts"])
        }

        if chapter_num in chapter_themes:
            theme_title, theme_summary, subtopics = chapter_themes[chapter_num]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary} This chapter explores {theme_title.lower()} within the context of {topic}."
        else:
            advanced_themes = [
                ("Specialized Applications", "Advanced exploration of specialized applications within the topic.", ["Specialized Techniques", "Advanced Applications", "Expert Insights", "Domain Expertise"]),
                ("Cutting-Edge Developments", "Latest developments and cutting-edge approaches in the field.", ["Latest Developments", "Cutting-edge Approaches", "Innovation Highlights", "Future Technologies"]),
                ("Integration and Optimization", "Integration strategies and optimization techniques for better performance.", ["Integration Strategies", "Optimization Techniques", "Performance Enhancement", "System Integration"]),
                ("Advanced Analytics and Insights", "Advanced analytical methods and deep insights into the topic.", ["Advanced Analytics", "Deep Insights", "Data Analysis", "Strategic Intelligence"]),
                ("Strategic Implementation", "Strategic approaches to implementing concepts and achieving goals.", ["Strategic Planning", "Implementation Tactics", "Goal Achievement", "Strategic Execution"]),
                ("Innovation and Transformation", "Innovative ideas and transformative approaches to the field.", ["Innovative Ideas", "Transformative Approaches", "Change Management", "Innovation Strategies"])
            ]
            theme_title, theme_summary, subtopics = advanced_themes[(chapter_num - 1) % len(advanced_themes)]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary}"

        return ChapterPlan(title=title, summary=summary, subtopics=subtopics)

    def _extract_json(self, text: str) -> Optional[dict]:
        # Same
        if not text or not isinstance(text, str):
            return None

        try:
            return json.loads(text)
        except Exception:
            pass

        m = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        return None

    def _fallback_plan(self, topic: str, num_chapters: int, tone: str = "casual") -> BookPlan:
        title = f"The Complete Guide to {topic}"
        fallback_chapters = []
        for i in range(1, num_chapters + 1):
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, i, num_chapters)
            fallback_chapters.append(fallback_chapter)
        return BookPlan(title=title, chapters=fallback_chapters)


# ---------------------------
# IndexingAgent (uses tone + toc_context)
# ---------------------------
class IndexingAgent:
    def __init__(self, provider: GroqProvider) -> None:
        self.provider = provider

    def plan(
        self,
        topic: str,
        num_chapters: int = 8,
        tone: str = "casual",
        toc_context: str = "",
    ) -> BookPlan:
        """
        Create a BookPlan (title + list of ChapterPlan) using:
          - tone: "casual" | "formal" | "academic" | "storytelling"
          - toc_context: real scraped TOC text (can be empty)
        """

        # Select prompts based on tone
        if tone == "formal":
            system_prompt = PLANNER_SYSTEM_FORMAL
            user_template = PLANNER_USER_TMPL_FORMAL
        elif tone == "academic":
            system_prompt = PLANNER_SYSTEM_ACADEMIC
            user_template = PLANNER_USER_TMPL_ACADEMIC
        elif tone == "storytelling":
            system_prompt = PLANNER_SYSTEM_STORYTELLING
            user_template = PLANNER_USER_TMPL_STORYTELLING
        else:  # casual
            system_prompt = PLANNER_SYSTEM
            user_template = PLANNER_USER_TMPL

        # Truncate context to avoid token overflow but keep meaningful sample
        max_context_chars = 8000
        if toc_context and len(toc_context) > max_context_chars:
            logger.info(f"Truncating toc_context from {len(toc_context)} to {max_context_chars} chars")
            toc_context = toc_context[:max_context_chars] + "\n...[truncated]"

        # Compose messages: system -> assistant (TOC context) -> user (task)
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if toc_context:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"REFERENCE TOC EXAMPLES (analyze structure, numbering, and phrasing):\n\n{toc_context}",
                }
            )

        user_msg = user_template.format(topic=topic, num_chapters=num_chapters)
        messages.append({"role": "user", "content": user_msg})

        # Call model
        logger.info(f"IndexingAgent: sending planning request for topic='{topic}' (tone={tone})")
        raw = self.provider.complete_messages(messages, temperature=0.35, timeout=120)
        logger.info(f"IndexingAgent raw output (truncated): {raw[:800]}")

        data = self._extract_json(raw)
        if not data:
            logger.warning("IndexingAgent: JSON extraction failed; falling back to safe plan")
            return self._fallback_plan(topic, num_chapters, tone)

        # Parse structured response (support both simple schema and academic parts schema)
        # If academic parts schema provided, flatten parts -> chapters for BookPlan
        title = data.get("title") or f"The Complete Guide to {topic}"
        chapters: List[ChapterPlan] = []

        if "parts" in data and isinstance(data["parts"], list):
            for part_idx, part in enumerate(data["parts"]):
                for ch_idx, ch in enumerate(part.get("chapters", [])):
                    ch_title = ch.get("chapter_title") or ch.get("title") or "Untitled Chapter"
                    sections = ch.get("sections") or []
                    subtopics = []
                    if sections:
                        # Build a short summary from first few sections with numbering
                        sec_titles = []
                        for i, s in enumerate(sections[:4], 1):
                            if isinstance(s, dict):
                                title = s.get("section_title") or s.get("title")
                                if title:
                                    sec_titles.append(f"{ch.get('chapter_number', str(len(chapters)+1))}.{i} {title}")
                                    subtopics.append(title)
                        summary = "Includes sections: " + ", ".join(sec_titles)
                    else:
                        summary = f"Explores theoretical and applied aspects of {topic}."
                    chapters.append(ChapterPlan(title=ch_title, summary=summary, subtopics=subtopics))
        elif "chapters" in data and isinstance(data["chapters"], list):
            for ch in data["chapters"][:num_chapters]:
                if isinstance(ch, dict):
                    ch_title = ch.get("title") or ch.get("chapter_title") or "Untitled Chapter"
                    summary = ch.get("summary") or ch.get("description") or f"Important topics related to {topic}."
                    subtopics = ch.get("subtopics", [])
                    if not isinstance(subtopics, list):
                        subtopics = []
                    chapters.append(ChapterPlan(title=f"Chapter {ch.get('chapter_number', str(len(chapters)+1))}: {ch_title}", summary=summary, subtopics=subtopics))
                else:
                    chapters.append(ChapterPlan(title=str(ch), summary=f"Important concepts related to {topic}."))
        else:
            logger.warning("IndexingAgent: no recognized 'parts' or 'chapters' in model output")

        # Ensure exact number of chapters requested with diverse fallback titles
        while len(chapters) < num_chapters:
            idx = len(chapters) + 1
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, idx, num_chapters)
            chapters.append(fallback_chapter)
        chapters = chapters[:num_chapters]

        return BookPlan(title=title, chapters=chapters)

    def _generate_diverse_fallback_chapter(self, topic: str, chapter_num: int, total_chapters: int) -> ChapterPlan:
        """Generate diverse fallback chapter titles, summaries, and subtopics based on topic and position."""

        # Define chapter themes based on position in book
        chapter_themes = {
            1: ("Foundations and Fundamentals", "Core concepts, basic principles, and foundational knowledge essential for understanding the topic.", ["Introduction", "Basic Concepts", "Key Principles", "Foundational Knowledge"]),
            2: ("Core Principles and Theory", "Theoretical frameworks, key principles, and conceptual understanding of the subject matter.", ["Theoretical Frameworks", "Core Principles", "Conceptual Models", "Fundamental Theory"]),
            3: ("Practical Applications", "Real-world implementation, practical techniques, and hands-on approaches to applying the concepts.", ["Implementation Strategies", "Practical Techniques", "Hands-on Examples", "Real-world Applications"]),
            4: ("Advanced Techniques and Methods", "Sophisticated methods, advanced strategies, and specialized approaches to the topic.", ["Advanced Methods", "Specialized Techniques", "Optimization Strategies", "Expert Approaches"]),
            5: ("Case Studies and Examples", "Real-world examples, case studies, and practical demonstrations of concepts in action.", ["Case Study Analysis", "Real-world Examples", "Practical Demonstrations", "Success Stories"]),
            6: ("Challenges and Solutions", "Common challenges, problem-solving approaches, and strategies for overcoming obstacles.", ["Common Challenges", "Problem-solving Techniques", "Solution Strategies", "Overcoming Obstacles"]),
            7: ("Future Trends and Innovations", "Emerging trends, future developments, and innovative approaches shaping the field.", ["Emerging Trends", "Future Developments", "Innovative Approaches", "Industry Evolution"]),
            8: ("Implementation and Best Practices", "Practical implementation guides, best practices, and actionable recommendations.", ["Implementation Guides", "Best Practices", "Actionable Recommendations", "Practical Tips"]),
            9: ("Ethics and Governance", "Ethical considerations, governance frameworks, and responsible practices in the field.", ["Ethical Considerations", "Governance Frameworks", "Responsible Practices", "Compliance Issues"]),
            10: ("Research and Future Directions", "Current research, future directions, and emerging areas of study.", ["Current Research", "Future Directions", "Emerging Areas", "Research Opportunities"]),
            11: ("Industry Applications", "Industry-specific applications, sector implementations, and domain-specific use cases.", ["Industry Applications", "Sector Implementations", "Domain Use Cases", "Specialized Applications"]),
            12: ("Conclusion and Strategic Roadmap", "Summary of key concepts, strategic planning, and long-term roadmaps for success.", ["Key Concepts Summary", "Strategic Planning", "Long-term Roadmaps", "Final Thoughts"])
        }

        # Get theme for this chapter number, or use a generic advanced topic
        if chapter_num in chapter_themes:
            theme_title, theme_summary, subtopics = chapter_themes[chapter_num]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary} This chapter explores {theme_title.lower()} within the context of {topic}."
        else:
            # For chapters beyond our predefined themes
            advanced_themes = [
                ("Specialized Applications", "Advanced exploration of specialized applications within the topic.", ["Specialized Techniques", "Advanced Applications", "Expert Insights", "Domain Expertise"]),
                ("Cutting-Edge Developments", "Latest developments and cutting-edge approaches in the field.", ["Latest Developments", "Cutting-edge Approaches", "Innovation Highlights", "Future Technologies"]),
                ("Integration and Optimization", "Integration strategies and optimization techniques for better performance.", ["Integration Strategies", "Optimization Techniques", "Performance Enhancement", "System Integration"]),
                ("Advanced Analytics and Insights", "Advanced analytical methods and deep insights into the topic.", ["Advanced Analytics", "Deep Insights", "Data Analysis", "Strategic Intelligence"]),
                ("Strategic Implementation", "Strategic approaches to implementing concepts and achieving goals.", ["Strategic Planning", "Implementation Tactics", "Goal Achievement", "Strategic Execution"]),
                ("Innovation and Transformation", "Innovative ideas and transformative approaches to the field.", ["Innovative Ideas", "Transformative Approaches", "Change Management", "Innovation Strategies"])
            ]
            theme_title, theme_summary, subtopics = advanced_themes[(chapter_num - 1) % len(advanced_themes)]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary}"

        return ChapterPlan(title=title, summary=summary, subtopics=subtopics)

    def _extract_json(self, text: str) -> Optional[dict]:
        """Attempt multiple strategies to extract JSON from model output."""
        if not text or not isinstance(text, str):
            return None

        # Direct JSON
        try:
            return json.loads(text)
        except Exception:
            pass

        # JSON in triple backticks block
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        # Try to find first {...} block
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        return None

    def _fallback_plan(self, topic: str, num_chapters: int, tone: str = "casual") -> BookPlan:
        """Return a safe fallback BookPlan when LLM output can't be parsed."""
        title = f"The Complete Guide to {topic}"
        fallback_chapters = []
        for i in range(1, num_chapters + 1):
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, i, num_chapters)
            fallback_chapters.append(fallback_chapter)
        return BookPlan(title=title, chapters=fallback_chapters)


# ---------------------------
# Book Discovery Agent
# ---------------------------
class BookDiscoveryAgent:
    def __init__(self):
        pass

    def search_books(self, topic: str, max_results: int = 10) -> List[str]:
        """
        Use duckduckgo (ddgs) to discover candidate book/pdf URLs for a topic.
        Returns a list of URLs (best-effort).
        """
        try:
            queries = [
                f'"{topic}" book table of contents',
                f'"{topic}" textbook pdf',
                f'"{topic}" "table of contents" site:edu',
                f'"{topic}" book chapters',
            ]
            collected = []
            for q in queries:
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(q, max_results=6))
                        for r in results:
                            url = r.get("href") or r.get("link") or r.get("url")
                            if not url:
                                continue
                            url = url.strip()
                            # keep likely useful domains / pdfs
                            if any(k in url.lower() for k in ["pdf", "openlibrary", "springer", "books.google", "arxiv", "edu", "org"]):
                                collected.append(url)
                            else:
                                # still append occasionally (broad coverage)
                                collected.append(url)
                except Exception as e:
                    logger.debug(f"DDGS query failed for '{q}': {e}")
                time.sleep(0.4)
            # dedupe preserve order
            seen = set()
            urls = []
            for u in collected:
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
                if len(urls) >= max_results:
                    break
            logger.info(f"BookDiscoveryAgent: found {len(urls)} urls for topic '{topic}'")
            return urls
        except Exception as e:
            logger.error(f"BookDiscoveryAgent.search_books error: {e}")
            return []


# ---------------------------
# TOC Scraper Agent
# ---------------------------
class TOCScraperAgent:
    def __init__(self):
        pass

    def extract_toc(self, url: str) -> str:
        """Auto-detect HTML vs PDF and extract a TOC-like text snippet."""
        try:
            if url.lower().endswith(".pdf"):
                return self.scrape_pdf_toc(url)
            # some URLs contain query strings but point to pdf:
            if ".pdf?" in url.lower():
                return self.scrape_pdf_toc(url)
            return self.scrape_html_toc(url)
        except Exception as e:
            logger.warning(f"TOCScraperAgent.extract_toc error for {url}: {e}")
            return ""

    def scrape_html_toc(self, url: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
            resp = requests.get(url, headers=headers, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            selectors = [
                "#table-of-contents", ".table-of-contents", "#toc", ".toc",
                "#contents", ".contents", "[class*='toc']", "[id*='toc']"
            ]
            for sel in selectors:
                elems = soup.select(sel)
                if elems:
                    texts = []
                    for e in elems:
                        texts.append(e.get_text(separator="\n", strip=True))
                    return "\n".join(texts).strip()
            # fallback to headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            filtered = []
            for h in headings[:30]:
                t = h.get_text(strip=True)
                if not t:
                    continue
                low = t.lower()
                if any(bad in low for bad in ["contact", "about", "subscribe", "login", "copyright"]):
                    continue
                filtered.append(t)
            return "\n".join(filtered).strip()
        except Exception as e:
            logger.debug(f"HTML scrape failed for {url}: {e}")
            return ""

    def scrape_pdf_toc(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            temp_path = f"/tmp/{uuid.uuid4().hex}.pdf"
            with open(temp_path, "wb") as f:
                f.write(resp.content)
            doc = fitz.open(temp_path)
            toc_text = ""
            # get_toc returns list of tuples (level, title, page)
            try:
                toc = doc.get_toc()
            except Exception:
                toc = None
            if toc:
                lines = []
                for item in toc[:200]:
                    # item tuple format: (level, title, page)
                    if len(item) >= 2:
                        lines.append(item[1])
                toc_text = "\n".join(lines)
            else:
                # fallback: search first pages for headings 'Table of Contents', 'Contents'
                for pnum in range(min(8, len(doc))):
                    page_text = doc[pnum].get_text("text")
                    if re.search(r'(Table of Contents|Contents|Index)', page_text, re.IGNORECASE):
                        # take a chunk around that page
                        toc_text += page_text + "\n"
                        # also try next page
                        if pnum + 1 < len(doc):
                            toc_text += doc[pnum + 1].get_text("text") + "\n"
                        break
            doc.close()
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return re.sub(r'\s+\n', '\n', toc_text).strip()
        except Exception as e:
            logger.debug(f"PDF scrape failed for {url}: {e}")
            return ""


# ---------------------------
# Helper: generate_toc_context (orchestration glue)
# ---------------------------
def generate_toc_context(topic: str, max_urls: int = 6, max_sources: int = 4) -> str:
    """
    Discover books for a topic, scrape their TOCs, and return a merged context string.
    - max_urls: how many discovery URLs to examine
    - max_sources: how many scraped TOC snippets to include in the final context
    """
    disc = BookDiscoveryAgent()
    scraper = TOCScraperAgent()

    urls = disc.search_books(topic, max_results=max_urls)
    if not urls:
        logger.info("generate_toc_context: no URLs discovered")
        return ""

    context_parts = []
    for url in urls:
        try:
            toc = scraper.extract_toc(url)
            if toc and len(toc) > 120:  # keep reasonably sized snippets
                context_parts.append(f"Book TOC from {url}:\n{toc}")
            # stop when we have enough sources
            if len(context_parts) >= max_sources:
                break
        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
        time.sleep(0.35)

    merged = "\n\n".join(context_parts)
    logger.info(f"generate_toc_context: merged length={len(merged)} chars from {len(context_parts)} sources")
    return merged


# ---------------------------
# Writing Agent (writes chapters)
# ---------------------------
# Critique Agent
# ---------------------------
class CritiqueAgent:
    def __init__(self, provider: GroqProvider) -> None:
        self.provider = provider

    def critique_toc(
        self,
        toc_plan: BookPlan,
        topic: str,
        num_chapters: int,
        tone: str,
        toc_context: str = "",
    ) -> BookPlan:
        # Serialize the TOC
        toc_text = f"TOC to critique:\nTitle: {toc_plan.title}\n"
        for j, ch in enumerate(toc_plan.chapters, 1):
            toc_text += f"{j}. {ch.title} - {ch.summary}\n"

        # System prompt
        system_prompt = (
            "You are an expert content critic specializing in analyzing and improving Table of Contents for books. "
            "You identify weaknesses, redundancies, gaps, and areas for improvement. "
            "You provide constructive criticism and suggest enhancements to make the TOC more comprehensive, logical, and engaging. "
            "You strictly return valid JSON only."
        )

        # User prompt
        user_template = (
            "You have received a Table of Contents for a book on '{topic}' with {num_chapters} chapters in '{tone}' tone.\n\n"
            "ANALYZE THIS TOC:\n{toc_text}\n\n"
            "CRITIQUE REQUIREMENTS:\n"
            "- Identify any redundancies, gaps, or logical inconsistencies\n"
            "- Suggest improvements for chapter titles, summaries, and subtopics\n"
            "- Ensure the TOC flows logically and covers the topic comprehensively\n"
            "- Maintain the '{tone}' tone throughout\n"
            "- Keep exactly {num_chapters} chapters\n\n"
            "OUTPUT FORMAT:\n"
            "{{\n"
            '  "title": "Improved Book Title",\n'
            '  "chapters": [\n'
            '    {{"title": "Chapter 1: Improved Title", "summary": "Improved summary", "subtopics": ["Sub1", "Sub2", "Sub3"]}},\n'
            '    ...\n'
            '  ]\n'
            "}}\n\n"
            "Return ONLY valid JSON."
        )

        user_msg = user_template.format(topic=topic, num_chapters=num_chapters, tone=tone, toc_text=toc_text)

        # Truncate if too long
        max_chars = 12000
        if len(user_msg) > max_chars:
            user_msg = user_msg[:max_chars] + "\n\n[Content truncated due to length]"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        # Call model
        logger.info(f"CritiqueAgent: critiquing TOC for topic='{topic}'")
        raw = self.provider.complete_messages(messages, temperature=0.3, timeout=120)
        logger.info(f"CritiqueAgent raw output (truncated): {raw[:800]}")

        data = self._extract_json(raw)
        if not data:
            logger.warning("CritiqueAgent: JSON extraction failed; returning original TOC")
            return toc_plan

        # Parse
        title = data.get("title") or toc_plan.title
        chapters: List[ChapterPlan] = []

        if "chapters" in data and isinstance(data["chapters"], list):
            for ch in data["chapters"][:num_chapters]:
                if isinstance(ch, dict):
                    ch_title = ch.get("title") or "Untitled Chapter"
                    summary = ch.get("summary") or f"Chapter on {topic}."
                    subtopics = ch.get("subtopics", [])
                    if not isinstance(subtopics, list):
                        subtopics = []
                    chapters.append(ChapterPlan(title=ch_title, summary=summary, subtopics=subtopics))

        # Ensure exact number
        while len(chapters) < num_chapters:
            idx = len(chapters) + 1
            fallback_chapter = self._generate_diverse_fallback_chapter(topic, idx, num_chapters)
            chapters.append(fallback_chapter)
        chapters = chapters[:num_chapters]

        return BookPlan(title=title, chapters=chapters)

    def _generate_diverse_fallback_chapter(self, topic: str, chapter_num: int, total_chapters: int) -> ChapterPlan:
        chapter_themes = {
            1: ("Foundations and Fundamentals", "Core concepts, basic principles, and foundational knowledge essential for understanding the topic.", ["Introduction", "Basic Concepts", "Key Principles", "Foundational Knowledge"]),
            2: ("Core Principles and Theory", "Theoretical frameworks, key principles, and conceptual understanding of the subject matter.", ["Theoretical Frameworks", "Core Principles", "Conceptual Models", "Fundamental Theory"]),
            3: ("Practical Applications", "Real-world implementation, practical techniques, and hands-on approaches to applying the concepts.", ["Implementation Strategies", "Practical Techniques", "Hands-on Examples", "Real-world Applications"]),
            4: ("Advanced Techniques and Methods", "Sophisticated methods, advanced strategies, and specialized approaches to the topic.", ["Advanced Methods", "Specialized Techniques", "Optimization Strategies", "Expert Approaches"]),
            5: ("Case Studies and Examples", "Real-world examples, case studies, and practical demonstrations of concepts in action.", ["Case Study Analysis", "Real-world Examples", "Practical Demonstrations", "Success Stories"]),
            6: ("Challenges and Solutions", "Common challenges, problem-solving approaches, and strategies for overcoming obstacles.", ["Common Challenges", "Problem-solving Techniques", "Solution Strategies", "Overcoming Obstacles"]),
            7: ("Future Trends and Innovations", "Emerging trends, future developments, and innovative approaches shaping the field.", ["Emerging Trends", "Future Developments", "Innovative Approaches", "Industry Evolution"]),
            8: ("Implementation and Best Practices", "Practical implementation guides, best practices, and actionable recommendations.", ["Implementation Guides", "Best Practices", "Actionable Recommendations", "Practical Tips"]),
            9: ("Ethics and Governance", "Ethical considerations, governance frameworks, and responsible practices in the field.", ["Ethical Considerations", "Governance Frameworks", "Responsible Practices", "Compliance Issues"]),
            10: ("Research and Future Directions", "Current research, future directions, and emerging areas of study.", ["Current Research", "Future Directions", "Emerging Areas", "Research Opportunities"]),
            11: ("Industry Applications", "Industry-specific applications, sector implementations, and domain-specific use cases.", ["Industry Applications", "Sector Implementations", "Domain Use Cases", "Specialized Applications"]),
            12: ("Conclusion and Strategic Roadmap", "Summary of key concepts, strategic planning, and long-term roadmaps for success.", ["Key Concepts Summary", "Strategic Planning", "Long-term Roadmaps", "Final Thoughts"])
        }

        if chapter_num in chapter_themes:
            theme_title, theme_summary, subtopics = chapter_themes[chapter_num]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary} This chapter explores {theme_title.lower()} within the context of {topic}."
        else:
            advanced_themes = [
                ("Specialized Applications", "Advanced exploration of specialized applications within the topic.", ["Specialized Techniques", "Advanced Applications", "Expert Insights", "Domain Expertise"]),
                ("Cutting-Edge Developments", "Latest developments and cutting-edge approaches in the field.", ["Latest Developments", "Cutting-edge Approaches", "Innovation Highlights", "Future Technologies"]),
                ("Integration and Optimization", "Integration strategies and optimization techniques for better performance.", ["Integration Strategies", "Optimization Techniques", "Performance Enhancement", "System Integration"]),
                ("Advanced Analytics and Insights", "Advanced analytical methods and deep insights into the topic.", ["Advanced Analytics", "Deep Insights", "Data Analysis", "Strategic Intelligence"]),
                ("Strategic Implementation", "Strategic approaches to implementing concepts and achieving goals.", ["Strategic Planning", "Implementation Tactics", "Goal Achievement", "Strategic Execution"]),
                ("Innovation and Transformation", "Innovative ideas and transformative approaches to the field.", ["Innovative Ideas", "Transformative Approaches", "Change Management", "Innovation Strategies"])
            ]
            theme_title, theme_summary, subtopics = advanced_themes[(chapter_num - 1) % len(advanced_themes)]
            title = f"Chapter {chapter_num}: {theme_title} in {topic}"
            summary = f"{theme_summary}"

        return ChapterPlan(title=title, summary=summary, subtopics=subtopics)

    def _extract_json(self, text: str) -> Optional[dict]:
        if not text or not isinstance(text, str):
            return None

        try:
            return json.loads(text)
        except Exception:
            pass

        m = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        return None

# ---------------------------
class WritingAgent:
    def __init__(self, provider: GroqProvider) -> None:
        self.provider = provider

    def write(self, book_title: str, topic: str, chapters: List[ChapterPlan], tone: str = "casual") -> BookContent:
        contents: List[ChapterContent] = []

        # Choose writer system by tone
        if tone == "formal":
            writer_system = WRITER_SYSTEM_FORMAL()
        elif tone == "academic":
            writer_system = WRITER_SYSTEM_ACADEMIC()
        elif tone == "storytelling":
            writer_system = WRITER_SYSTEM_STORYTELLING()
        else:
            writer_system = WRITER_SYSTEM()

        for i, ch in enumerate(chapters):
            chapter_context = f"This is chapter {i+1} of {len(chapters)} in the book '{book_title}' about {topic}."
            user_prompt = (
                f"{chapter_context}\n\n"
                f"Chapter Title: {ch.title}\n"
                f"Summary: {ch.summary}\n"
                f"Subtopics: {', '.join(ch.subtopics)}\n\n"
                f"Write a 1000-1500 word chapter. Start with the chapter title as a large <h1> heading. Use the provided subtopics as <h3 style='font-size: 1.4em; font-weight: bold; margin-top: 2em; margin-bottom: 1em;'> section headings within the chapter, ensuring each subtopic becomes a distinct section with relevant content. Add TWO blank lines after each subtopic heading before starting the content paragraph for clear separation. Avoid markdown. Keep academic quality."
            )
            messages = [
                {"role": "system", "content": writer_system},
                {"role": "user", "content": user_prompt},
            ]
            logger.info(f"WritingAgent: generating chapter {i+1} - '{ch.title}'")
            text = self.provider.complete_messages(messages, temperature=0.7, timeout=40)
            contents.append(ChapterContent(title=ch.title, content=text))

        return BookContent(title=book_title, chapters=contents)


# minimal implementations of writer system functions (kept as functions to avoid duplication)
def WRITER_SYSTEM():
    return (
        "You are an expert AI research writer tasked with generating full, well-structured, and human-like book chapters. "
        "You maintain clear flow, smooth transitions, and factual accuracy while using an academic yet engaging tone. "
        "Do NOT use markdown formatting; use plain text and HTML tags for headings (<h2>)."
    )


def WRITER_SYSTEM_FORMAL():
    return (
        "You are a distinguished scholarly writer tasked with generating comprehensive, methodically structured, and academically rigorous book chapters. "
        "Use formal, authoritative tone, include citations where relevant (textual, not link format), and use <h2> headings only. Do not use markdown."
    )


def WRITER_SYSTEM_ACADEMIC():
    return (
        "You are a renowned academic writer tasked with generating erudite, research-oriented, and intellectually sophisticated book chapters. "
        "Use academic tone, include theoretical depth, and format sections with <h2> headings only."
    )


def WRITER_SYSTEM_STORYTELLING():
    return (
        "You are a masterful narrative writer tasked with generating compelling, story-driven, and emotionally engaging book chapters. "
        "Use vivid language, personal anecdotes (fictionalized examples allowed), and structure sections with <h2> headings."
    )


# ---------------------------
# Top-level orchestrator (convenience)
# ---------------------------
def create_book(
    provider: GroqProvider,
    topic: str,
    num_chapters: int = 8,
    tone: str = "casual",
    discover_max_urls: int = 6,
) -> BookContent:
    """
    Full pipeline convenience function:
      1) discover books
      2) scrape TOCs
      3) plan outline (IndexingAgent)
      4) write chapters (WritingAgent)
    Returns BookContent (title + chapter contents)
    """
    logger.info(f"create_book: starting pipeline for '{topic}' (tone={tone})")
    toc_context = generate_toc_context(topic, max_urls=discover_max_urls, max_sources=4)

    provider_for_index = provider
    indexer = IndexingAgent(provider_for_index)
    plan = indexer.plan(topic=topic, num_chapters=num_chapters, tone=tone, toc_context=toc_context)

    writer = WritingAgent(provider_for_index)
    book_content = writer.write(book_title=plan.title, topic=topic, chapters=plan.chapters, tone=tone)

    logger.info(f"create_book: finished pipeline for '{topic}'")
    return book_content


# ---------------------------
# Debug helpers
# ---------------------------
def debug_scrape_and_plan(provider: GroqProvider, topic: str):
    """
    Debug helper: prints discovered URLs, scraped snippets, plan JSON (if produced).
    """
    disc = BookDiscoveryAgent()
    scraper = TOCScraperAgent()

    urls = disc.search_books(topic, max_results=8)
    print("Discovered URLs:")
    for u in urls:
        print(" -", u)

    print("\nScraped TOC snippets (first 600 chars each):")
    snippets = []
    for u in urls[:5]:
        t = scraper.extract_toc(u)
        print(f"--- {u} ---")
        print(t[:600].replace("\n", " ") + ("\n[truncated]" if len(t) > 600 else ""))
        snippets.append((u, t))

    merged = "\n\n".join([f"Book TOC from {u}:\n{t}" for u, t in snippets if t])
    print("\nMerged context length:", len(merged))

    indexer = IndexingAgent(provider)
    plan = indexer.plan(topic=topic, num_chapters=8, tone="academic", toc_context=merged)
    print("\nGenerated Plan Title:", plan.title)
    for i, ch in enumerate(plan.chapters, 1):
        print(f"{i}. {ch.title} -> {ch.summary}")


# EOF
