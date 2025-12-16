from __future__ import annotations
import os
import logging
from typing import Optional, List, Dict, Any
from groq import Groq

logger = logging.getLogger(__name__)

class GroqProvider:
	def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant") -> None:
		self.api_key = api_key or os.environ.get("GROQ_API_KEY")
		self.model = model
		self._client = None
		
		logger.info(f"GroqProvider init: api_key={'***' if self.api_key else 'None'}, model={model}")
		
		if self.api_key:
			try:
				self._client = Groq(api_key=self.api_key)
				logger.info("Groq client initialized successfully")
			except Exception as e:
				logger.error(f"Failed to initialize Groq client: {e}")
				self._client = None
		else:
			logger.warning("No GROQ_API_KEY provided, using mock mode")

	def is_available(self) -> bool:
		return self._client is not None

	def complete(self, prompt: str, temperature: float = 0.7, timeout: int = 30) -> str:
		if not self._client:
			logger.warning("Groq client not available, returning mock response")
			return f"[GROQ_MOCK]\n{prompt[:300]} ..."
		
		try:
			logger.info(f"Calling Groq API with prompt length: {len(prompt)}")
			resp = self._client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": prompt}],
				temperature=temperature,
				timeout=timeout,
			)
			content = (resp.choices[0].message.content or "").strip()
			logger.info(f"Groq API success, response length: {len(content)}")
			return content
		except Exception as e:
			logger.error(f"Groq API call failed: {e}")
			if "429" in str(e) or "rate_limit" in str(e).lower():
				logger.warning("Rate limit exceeded, using fallback content")
				return self._generate_fallback_content(prompt, "rate_limit")
			return f"[GROQ_ERROR: {str(e)}]\n{prompt[:300]} ..."

	def complete_messages(self, messages: List[Dict[str, Any]], temperature: float = 0.7, timeout: int = 30) -> str:
		if not self._client:
			# Join messages for mock
			joined = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
			return f"[GROQ_MOCK]\n{joined[:500]} ..."
		
		try:
			logger.info(f"Calling Groq API with {len(messages)} messages")
			resp = self._client.chat.completions.create(
				model=self.model,
				messages=messages,
				temperature=temperature,
				timeout=timeout,
			)
			content = (resp.choices[0].message.content or "").strip()
			logger.info(f"Groq API success, response length: {len(content)}")
			return content
		except Exception as e:
			logger.error(f"Groq API call failed: {e}")
			if "429" in str(e) or "rate_limit" in str(e).lower():
				logger.warning("Rate limit exceeded, using fallback content")
				joined = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
				return self._generate_fallback_content(joined, "rate_limit")
			# Join messages for error response
			joined = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
			return f"[GROQ_ERROR: {str(e)}]\n{joined[:500]} ..."

	def _generate_fallback_content(self, prompt: str, reason: str) -> str:
		"""Generate fallback content when Groq API is unavailable"""
		prompt_lower = prompt.lower()
		
		# Check for TOC generation requests (more specific detection)
		if any(keyword in prompt_lower for keyword in [
			"table of contents", "generate a professional", "pedagogically structured", 
			"exactly", "chapters with engaging", "book outline", "toc"
		]) and not any(keyword in prompt_lower for keyword in [
			"write", "chapter content", "full chapter", "book chapter"
		]):
			# This is a TOC generation request
			return self._generate_toc_fallback(prompt)
		
		# Check for chapter writing requests (more specific detection)
		elif any(keyword in prompt_lower for keyword in [
			"write", "chapter content", "full chapter", "book chapter", 
			"mandatory chapter structure", "introduction", "core concepts"
		]) and "chapter" in prompt_lower:
			# This is a chapter writing request
			return self._generate_chapter_fallback(prompt)
		
		else:
			# Generic fallback - try to determine from context
			if "chapters" in prompt_lower and "generate" in prompt_lower:
				return self._generate_toc_fallback(prompt)
			else:
				return f"[FALLBACK_CONTENT]\n{prompt[:300]} ..."

	def _generate_chapter_fallback(self, prompt: str) -> str:
		"""Generate a complete chapter when API is unavailable"""
		# Extract topic from prompt
		topic = "the subject"
		if "topic:" in prompt.lower():
			topic_match = prompt.lower().split("topic:")[1].split("\n")[0].strip()
			if topic_match:
				topic = topic_match

		chapter_content = f"""<h1>INTRODUCTION</h1>
This chapter provides a comprehensive exploration of {topic}, examining its fundamental principles and practical applications. As we delve into this important subject, we will uncover the key concepts that make it relevant in today's rapidly evolving landscape.

<h2>CORE CONCEPTS</h2>
The foundation of {topic} rests upon several critical pillars that shape our understanding and implementation. These core concepts form the bedrock upon which more advanced applications are built, providing essential context for practitioners and researchers alike.

Key principles include systematic analysis, evidence-based approaches, and continuous improvement methodologies. These elements work together to create a robust framework for understanding and applying {topic} in various contexts.

<h2>IN-DEPTH ANALYSIS</h2>
A deeper examination reveals the intricate mechanisms and underlying processes that drive {topic}. Current research indicates significant developments in this field, with emerging trends pointing toward more sophisticated and efficient approaches.

The analysis encompasses both theoretical frameworks and practical implementations, offering insights into how {topic} continues to evolve and adapt to changing requirements and technological advances.

<h2>APPLICATIONS AND EXAMPLES</h2>
Real-world applications of {topic} demonstrate its versatility and impact across multiple industries. From healthcare and finance to technology and education, organizations are discovering innovative ways to leverage these concepts for improved outcomes.

Specific examples include automated systems that enhance efficiency, data-driven decision making processes, and collaborative platforms that facilitate knowledge sharing and innovation.

<h2>CHALLENGES AND OPEN QUESTIONS</h2>
Despite significant progress, several challenges remain in the field of {topic}. Current limitations include scalability concerns, integration complexities, and the need for standardized approaches across different implementations.

Open questions center around optimization strategies, long-term sustainability, and the development of more robust frameworks that can adapt to future technological changes.

<h2>FUTURE DIRECTIONS</h2>
The future of {topic} appears promising, with emerging trends pointing toward more intelligent, adaptive, and user-centric solutions. Key areas of development include artificial intelligence integration, cloud-based architectures, and enhanced user experience design.

These developments are expected to address current limitations while opening new possibilities for innovation and application across various domains.

<h2>CONCLUSION</h2>
This chapter has provided a comprehensive overview of {topic}, covering its fundamental concepts, practical applications, and future potential. The insights presented here form a foundation for deeper exploration and implementation in subsequent chapters.

As we continue to advance in this field, the principles and practices outlined here will serve as valuable guides for practitioners seeking to leverage {topic} for improved outcomes and innovative solutions."""

		return chapter_content

	def _generate_toc_fallback(self, prompt: str) -> str:
		"""Generate a table of contents when API is unavailable"""
		# Extract topic and number of chapters from prompt
		topic = "the subject"
		num_chapters = 8
		
		if "topic:" in prompt.lower():
			topic_match = prompt.lower().split("topic:")[1].split("\n")[0].strip()
			if topic_match:
				topic = topic_match
		
		if "exactly" in prompt.lower() and "chapters" in prompt.lower():
			import re
			chapter_match = re.search(r'exactly (\d+) chapters', prompt.lower())
			if chapter_match:
				num_chapters = int(chapter_match.group(1))

		# Create more engaging and specific chapter titles
		chapter_templates = [
			(f"Chapter {1}: Demystifying {topic}: From Buzzword to Business Reality", f"This chapter introduces the fundamentals of {topic}, its modern context, and practical relevance in today's business landscape. Readers will understand the core concepts and how these technologies are transforming industries."),
			(f"Chapter {2}: Setting Up Your {topic} Toolkit: Essential Components and Frameworks", f"In this chapter, readers will learn about the most important components and frameworks in {topic}, with practical examples and implementation strategies to get started effectively."),
			(f"Chapter {3}: Building Production-Ready {topic} Systems: From Prototype to Scale", f"This chapter delves into the process of building production-ready {topic} systems, from prototyping to scaling. Readers will learn about best practices and deployment strategies."),
			(f"Chapter {4}: Unleashing the Power of Advanced {topic}: Sophisticated Techniques and Strategies", f"In this chapter, readers will explore advanced {topic} techniques, including optimization strategies, performance tuning, and cutting-edge methodologies for experienced practitioners."),
			(f"Chapter {5}: The {topic}-Powered Enterprise: Transforming Business Through Strategic Implementation", f"This chapter examines the impact of {topic} on business, with a focus on strategic implementation and organizational transformation. Readers will learn about ROI and business value."),
			(f"Chapter {6}: Streamlining {topic} Operations: Efficiency, Scalability, and Best Practices", f"In this chapter, readers will learn about operational excellence in {topic}, including workflow optimization, resource management, and proven methodologies for sustainable success."),
			(f"Chapter {7}: Edge Computing and Real-Time {topic}: Opportunities and Challenges", f"This chapter explores the intersection of {topic} and modern computing paradigms, with a focus on real-time processing and emerging opportunities in distributed systems."),
			(f"Chapter {8}: Cloud Computing for {topic}: Scalability, Security, and Cost-Effectiveness", f"In this chapter, readers will learn about cloud-based {topic} implementations, including scalability considerations, security best practices, and cost optimization strategies."),
			(f"Chapter {9}: Sustainable {topic}: Reducing Environmental Impact and Energy Consumption", f"This chapter examines the environmental impact of {topic}, with a focus on sustainable practices, energy efficiency, and responsible implementation strategies."),
			(f"Chapter {10}: {topic} for Social Good: Applications and Opportunities", f"In this chapter, readers will explore the applications of {topic} for social impact, including healthcare, education, and environmental conservation initiatives."),
			(f"Chapter {11}: Ethics and Responsible {topic}: Principles and Practices", f"This chapter delves into the principles and practices of ethical {topic}, including fairness, transparency, accountability, and responsible implementation guidelines."),
			(f"Chapter {12}: {topic} in Healthcare: Diagnosis, Treatment, and Patient Outcomes", f"In this chapter, readers will learn about the applications of {topic} in healthcare, including diagnostic tools, treatment optimization, and patient care improvements."),
			(f"Chapter {13}: {topic} in Finance: Risk Management, Portfolio Optimization, and Trading", f"This chapter examines the applications of {topic} in finance, including risk assessment, portfolio management, and algorithmic trading strategies."),
			(f"Chapter {14}: {topic} in Retail: Customer Segmentation, Recommendation Systems, and Supply Chain", f"In this chapter, readers will learn about {topic} applications in retail, including customer analytics, recommendation engines, and supply chain optimization."),
			(f"Chapter {15}: {topic} in Manufacturing: Predictive Maintenance, Quality Control, and Process Optimization", f"This chapter explores {topic} applications in manufacturing, including predictive maintenance, quality assurance, and process optimization strategies."),
			(f"Chapter {16}: Measuring ROI and Business Impact: Evaluating {topic} Initiatives", f"In this chapter, readers will learn about measuring the return on investment and business impact of {topic} initiatives, including metrics, benchmarks, and evaluation frameworks."),
			(f"Chapter {17}: Implementing {topic} in the Enterprise: Organizational Transformation and Change Management", f"This chapter examines the challenges and opportunities of implementing {topic} in enterprise environments, including change management and organizational transformation strategies."),
			(f"Chapter {18}: Getting Started with {topic}: Actionable Implementation Roadmap and Best Practices", f"In this chapter, readers will learn practical steps for implementing {topic}, including data preparation, system design, and deployment best practices."),
			(f"Chapter {19}: Emerging Trends in {topic}: Innovation, Research, and Future Developments", f"This chapter explores emerging trends in {topic}, including cutting-edge research, innovative applications, and future development directions."),
			(f"Chapter {20}: The Future of {topic}: Predictions, Opportunities, and Challenges", f"In this final chapter, readers will learn about the future of {topic}, including predictions, emerging opportunities, and potential challenges in the evolving landscape.")
		]

		chapters = []
		for i in range(1, num_chapters + 1):
			if i <= len(chapter_templates):
				title, summary = chapter_templates[i-1]
				# Replace the chapter number in the title
				title = title.replace(f"Chapter {1}:", f"Chapter {i}:")
				chapters.append({
					"title": title,
					"summary": summary
				})
			else:
				# Generate additional chapters if needed
				title = f"Chapter {i}: Advanced Topics in {topic}"
				summary = f"Exploring sophisticated concepts and emerging trends in {topic} for experienced practitioners and industry leaders."
				chapters.append({
					"title": title,
					"summary": summary
				})

		import json
		return json.dumps({
			"title": f"{topic.title()}: From Fundamentals to Advanced Applications",
			"chapters": chapters
		}, indent=2)
