"""
OpenAI service wrapper for Content Engine.
"""

from typing import Any

from openai import AsyncOpenAI

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class OpenAIService:
    """Service for OpenAI API calls."""

    def __init__(self, api_key: str | None = None):
        """Initialize OpenAI service."""
        settings = get_settings()
        api_key = api_key or settings.get_openai_key()
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI service initialized")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        **kwargs: Any,
    ) -> str:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gpt-4o-mini)
            **kwargs: Additional arguments for completion

        Returns:
            Generated text content
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            return content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
