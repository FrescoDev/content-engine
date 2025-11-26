"""Topic clustering service (MVP: keyword-based)."""

from ...core import get_logger

logger = get_logger(__name__)


class TopicClusterer:
    """Map topics to clusters (MVP: keyword-based)."""

    CLUSTER_KEYWORDS = {
        "ai-infra": [
            "AI",
            "artificial intelligence",
            "machine learning",
            "LLM",
            "GPT",
            "Claude",
            "infrastructure",
            "model",
            "neural",
            "deep learning",
            "transformer",
            "AGI",
            "singularity",
        ],
        "business-socioeconomic": [
            "business",
            "economy",
            "startup",
            "tech",
            "market",
            "finance",
            "socioeconomic",
            "industry",
            "venture",
            "IPO",
            "acquisition",
            "merger",
        ],
        "culture-music": [
            "music",
            "entertainment",
            "celebrity",
            "culture",
            "trending",
            "viral",
            "artist",
            "album",
            "song",
            "award",
            "Grammy",
            "Oscar",
        ],
        "applied-industry": [
            "insurance",
            "mortgage",
            "real estate",
            "fintech",
            "healthcare",
            "legal",
            "compliance",
            "regulation",
        ],
        "meta-content-intel": [
            "content",
            "social media",
            "platform",
            "creator",
            "marketing",
            "strategy",
            "algorithm",
            "engagement",
        ],
    }

    def cluster_topic(self, title: str, entities: list[str]) -> str:
        """
        Determine topic cluster based on keywords.

        Args:
            title: Topic title
            entities: Extracted entities

        Returns:
            Cluster identifier
        """
        title_lower = title.lower()
        entity_text = " ".join(entities).lower()
        combined = f"{title_lower} {entity_text}"

        # Score each cluster
        scores: dict[str, int] = {}
        for cluster, keywords in self.CLUSTER_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in combined)
            scores[cluster] = score

        # Return highest scoring cluster
        if scores:
            best_cluster = max(scores.items(), key=lambda x: x[1])[0]
            if scores[best_cluster] > 0:
                logger.debug(
                    f"Clustered '{title}' to '{best_cluster}' (score: {scores[best_cluster]})"
                )
                return best_cluster

        # Default fallback
        logger.debug(f"Clustered '{title}' to default 'business-socioeconomic'")
        return "business-socioeconomic"
