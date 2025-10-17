"""
Lightweight embedding utility for vector search.

Uses sentence-transformers with a small model (all-MiniLM-L6-v2) for generating
embeddings. The model is ~80MB and provides a good balance between size and quality.

This module handles lazy loading of the model and provides a simple interface for
generating embeddings from text.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Global model instance (lazy-loaded)
_embedding_model = None


def get_embedding_model():
    """
    Get or initialize the sentence-transformers model.
    
    Uses lazy loading to avoid loading the model until it's actually needed.
    This is important for:
    - Faster application startup
    - Avoiding model loading in SQLite environments where vector search isn't available
    """
    global _embedding_model
    
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Vector search will not be available. "
                "Install with: pip install sentence-transformers"
            )
            _embedding_model = None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _embedding_model = None
    
    return _embedding_model


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate an embedding vector for the given text.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector (384 dimensions),
        or None if embedding generation fails or model is not available.
    """
    if not text or not text.strip():
        return None
    
    model = get_embedding_model()
    if model is None:
        return None
    
    try:
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)
        # Convert to list for JSON serialization
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def generate_asset_embedding(asset_name: str, asset_description: Optional[str] = None) -> Optional[List[float]]:
    """
    Generate an embedding for a catalog asset.
    
    Combines the asset name and description (if available) to create a more
    comprehensive embedding that captures both the asset identifier and its meaning.
    
    Args:
        asset_name: Name/URN of the asset
        asset_description: Optional description of the asset
        
    Returns:
        Embedding vector or None if generation fails
    """
    # Combine name and description for better semantic representation
    text_parts = [asset_name]
    
    if asset_description and asset_description.strip():
        text_parts.append(asset_description)
    
    combined_text = " ".join(text_parts)
    return generate_embedding(combined_text)
