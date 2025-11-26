"""Entity extraction service (MVP: keyword-based)."""

from ...core import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    """Extract entities from topic titles (MVP: keyword-based)."""

    # Common entities to extract
    TECH_COMPANIES = [
        "Google",
        "Apple",
        "Microsoft",
        "OpenAI",
        "Anthropic",
        "Meta",
        "Amazon",
        "Tesla",
        "Netflix",
        "Twitter",
        "X",
        "Facebook",
        "Instagram",
        "TikTok",
        "YouTube",
        "LinkedIn",
        "Reddit",
        "GitHub",
        "NVIDIA",
        "AMD",
        "Intel",
    ]

    AI_MODELS = [
        "GPT-4",
        "GPT-3",
        "GPT-3.5",
        "Claude",
        "Claude 3",
        "Claude 3.5",
        "Gemini",
        "Llama",
        "Mistral",
        "PaLM",
        "BERT",
        "Transformer",
    ]

    def extract_entities(self, title: str) -> list[str]:
        """
        Extract entities using keyword matching.

        Args:
            title: Topic title to extract entities from

        Returns:
            List of extracted entity names
        """
        entities: list[str] = []
        title_lower = title.lower()

        # Check tech companies
        for company in self.TECH_COMPANIES:
            if company.lower() in title_lower:
                entities.append(company)

        # Check AI models
        for model in self.AI_MODELS:
            if model.lower() in title_lower:
                entities.append(model)

        # Deduplicate and return
        return list(set(entities))
