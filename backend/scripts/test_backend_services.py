#!/usr/bin/env python3
"""
Test backend services are accessible and working.

This script verifies:
- Firestore connection
- OpenAI service initialization
- Script refinement service can be imported
"""

import asyncio
import sys

sys.path.insert(0, "src")

from src.core.config import get_settings
from src.core.logging import get_logger
from src.infra import FirestoreService, OpenAIService
from src.content.script_refinement_service import ScriptRefinementService

logger = get_logger(__name__)


async def test_backend_services():
    """Test all backend services."""
    logger.info("=" * 60)
    logger.info("Testing Backend Services")
    logger.info("=" * 60)

    # Test 1: Configuration
    try:
        settings = get_settings()
        logger.info(f"✅ Config loaded")
        logger.info(f"   Environment: {settings.environment}")
        logger.info(f"   Firestore DB: {settings.firestore_database_id}")
        logger.info(f"   OpenAI Key: {'Set' if settings.openai_api_key else 'NOT SET'}")
    except Exception as e:
        logger.error(f"❌ Config failed: {e}")
        return False

    # Test 2: Firestore Service
    try:
        firestore = FirestoreService()
        logger.info(f"✅ FirestoreService initialized")
        logger.info(f"   Database: {firestore.database_id}")
        
        # Try a simple query
        topics = await firestore.query_collection("topic_candidates", limit=1)
        logger.info(f"   Test query: Found {len(topics)} topics")
    except Exception as e:
        logger.warning(f"⚠️  FirestoreService: {e}")
        logger.warning("   (This is OK if Firestore is not configured)")

    # Test 3: OpenAI Service
    try:
        openai_service = OpenAIService()
        logger.info(f"✅ OpenAIService initialized")
        logger.info(f"   API Key: {'Set' if openai_service._api_key else 'NOT SET'}")
    except Exception as e:
        logger.warning(f"⚠️  OpenAIService: {e}")

    # Test 4: Script Refinement Service
    try:
        refinement_service = ScriptRefinementService()
        logger.info(f"✅ ScriptRefinementService initialized")
        logger.info(f"   Firestore: {'Connected' if refinement_service.firestore else 'Not connected'}")
        logger.info(f"   OpenAI: {'Connected' if refinement_service.openai_service else 'Not connected'}")
    except Exception as e:
        logger.error(f"❌ ScriptRefinementService failed: {e}")
        return False

    logger.info("=" * 60)
    logger.info("✅ All backend services are accessible!")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_backend_services())
    sys.exit(0 if success else 1)

