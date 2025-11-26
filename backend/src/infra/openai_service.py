"""
OpenAI service wrapper for Content Engine.
"""

import asyncio
import json
from typing import Any

from openai import AsyncOpenAI

from ..core import get_logger, get_settings

logger = get_logger(__name__)

# Cost per 1M tokens for GPT-4o-mini (as of 2024)
COST_PER_MILLION_INPUT_TOKENS = 0.15
COST_PER_MILLION_OUTPUT_TOKENS = 0.60


class OpenAIService:
    """Service for OpenAI API calls with retry logic and cost tracking."""

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
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any,
    ) -> str:
        """
        Generate chat completion with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gpt-4o-mini)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            **kwargs: Additional arguments for completion

        Returns:
            Generated text content
        """
        last_error = None
        for attempt in range(max_retries):
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
                last_error = e
                if attempt < max_retries - 1:
                    delay = retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"OpenAI API call failed after {max_retries} attempts: {e}")
        raise last_error or ValueError("OpenAI API call failed")

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate chat completion and parse as JSON.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gpt-4o-mini)
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for completion

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        # Force JSON response format
        kwargs.setdefault("response_format", {"type": "json_object"})

        content = await self.chat(messages, model=model, max_retries=max_retries, **kwargs)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}\nContent: {content[:200]}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}") from e

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini"
    ) -> float:
        """
        Estimate cost for API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        # For now, only support gpt-4o-mini pricing
        if model != "gpt-4o-mini":
            logger.warning(
                f"Cost estimation not supported for model {model}, using gpt-4o-mini rates"
            )

        input_cost = (input_tokens / 1_000_000) * COST_PER_MILLION_INPUT_TOKENS
        output_cost = (output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost

    async def chat_with_cost_tracking(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate chat completion and return content with cost tracking.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gpt-4o-mini)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            **kwargs: Additional arguments for completion

        Returns:
            Tuple of (content, cost_info) where cost_info contains:
            - input_tokens: int
            - output_tokens: int
            - cost_usd: float
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from OpenAI")

                # Extract token usage
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0

                cost_info = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": self.estimate_cost(input_tokens, output_tokens, model),
                    "model": model,
                }

                return content, cost_info
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"OpenAI API call failed after {max_retries} attempts: {e}")
        raise last_error or ValueError("OpenAI API call failed")
