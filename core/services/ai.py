"""AI service layer with dynamic database context injection (RAG).

Encapsulates all interactions with the OpenAI-compatible Hugging Face
router used by the portfolio chatbot. Builds a system prompt at request
time from:
  * the developer's static bio, and
  * up to three featured, non-deleted ``Project`` rows from the
    ``projects`` app, so the model can answer questions with grounded,
    project-aware context.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from openai import OpenAI

from projects.models import Project

logger = logging.getLogger(__name__)

_OPENAI_BASE_URL: str = "https://router.huggingface.co/v1"
_MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"
_TEMPERATURE: float = 0.1
_MAX_TOKENS: int = 120
_FEATURED_PROJECT_LIMIT: int = 3


class AIServiceError(Exception):
    """Raised when the AI model fails to generate a response."""


_BASE_BIO: str = (
    "Mohammad Hamdan is a senior Python/Django backend developer and "
    "Odoo ERP specialist with strong Linux and open-source experience. "
    "He builds scalable, clean, and maintainable systems using Django, "
    "PostgreSQL, REST APIs, Odoo (HR, Payroll, Accounting, custom "
    "modules), and modern front-end tooling (TailwindCSS, Alpine.js). "
    "He is comfortable across the full stack: backend engineering, "
    "data engineering (ETL pipelines, Prefect, SQL), and DevOps. "
    "Keep answers short (max 120 tokens), clear, and grounded in the "
    "context provided below. If the answer is not in the context, say "
    "so honestly rather than inventing details."
)


def _build_featured_projects_block() -> str:
    """Return a short bulleted summary of featured projects for the prompt."""
    featured = (
        Project.objects
        .filter(deleted_at__isnull=True, is_featured=True)
        .prefetch_related("tags")
        .order_by("-created_at")[:_FEATURED_PROJECT_LIMIT]
    )
    if not featured:
        return "No featured projects are currently listed."

    lines: list[str] = []
    for project in featured:
        tag_names: list[str] = sorted(
            tag.name for tag in project.tags.all() if tag.name
        )
        tag_fragment: str = (
            f" | Tech: {', '.join(tag_names)}" if tag_names else ""
        )
        description: str = (project.short_description or "").strip()
        lines.append(
            f"- {project.title}: {description}{tag_fragment}"
        )
    return "\n".join(lines)


def _build_dynamic_context() -> str:
    """Compose the system prompt from the bio + live project data."""
    projects_block: str = _build_featured_projects_block()
    return (
        f"{_BASE_BIO}\n\n"
        "Featured projects currently on the portfolio:\n"
        f"{projects_block}\n\n"
        "Use the bio and project list above as the only source of truth "
        "when answering. Do not invent skills, employers, or projects "
        "that are not listed."
    )


def _build_client() -> OpenAI:
    """Construct an OpenAI client pointed at the HF router."""
    return OpenAI(
        base_url=_OPENAI_BASE_URL,
        api_key=settings.HF_TOKEN,
    )


def generate_portfolio_response(user_question: str) -> str:
    """Generate a short answer to ``user_question`` about the portfolio.

    Args:
        user_question: The raw text submitted by the visitor.

    Returns:
        The trimmed completion text from the model.

    Raises:
        AIServiceError: If the upstream model call fails for any reason.
    """
    if not user_question or not user_question.strip():
        raise AIServiceError("Empty question supplied to AI service.")

    system_prompt: str = _build_dynamic_context()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question.strip()},
    ]

    try:
        client: OpenAI = _build_client()
        completion: Any = client.chat.completions.create(
            model=_MODEL_NAME,
            messages=messages,
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )
        answer: str = completion.choices[0].message.content.strip()
        return answer
    except Exception as exc:  # noqa: BLE001
        logger.exception("AI completion failed: %s", exc)
        raise AIServiceError("Failed to generate response from AI model.") from exc