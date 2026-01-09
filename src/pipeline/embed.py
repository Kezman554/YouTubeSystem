"""
Embedding generation module.

Generates vector embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2 (384 dimensions, runs locally on CPU)
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Wrapper for the embedding model.

    Uses all-MiniLM-L6-v2:
    - 384 dimensions
    - Runs on CPU
    - ~80MB model size
    - Fast: ~100 embeddings/second on modern CPU
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformers model
                       Default: 'all-MiniLM-L6-v2'
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model on first use."""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            print(f"Model loaded. Embedding dimension: {self._model.get_sentence_embedding_dimension()}")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats (384 dimensions for all-MiniLM-L6-v2)

        Example:
            >>> embedder = EmbeddingModel()
            >>> vector = embedder.embed_text("Hello world")
            >>> len(vector)
            384
        """
        vector = self.model.encode(text)
        return vector.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed multiple texts efficiently in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once (default 32)

        Returns:
            List of embedding vectors

        Example:
            >>> embedder = EmbeddingModel()
            >>> texts = ["First text", "Second text", "Third text"]
            >>> vectors = embedder.embed_batch(texts)
            >>> len(vectors)
            3
            >>> len(vectors[0])
            384
        """
        if not texts:
            return []

        # Show progress for large batches
        show_progress = len(texts) > 100

        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress
        )

        return vectors.tolist()


# Global instance for convenience
_global_embedder = None


def get_embedder() -> EmbeddingModel:
    """
    Get the global embedding model instance.

    This ensures the model is loaded only once and reused.

    Returns:
        EmbeddingModel instance
    """
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = EmbeddingModel()
    return _global_embedder


def embed_text(text: str) -> List[float]:
    """
    Convenience function to embed a single text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector (384 dimensions)

    Example:
        >>> vector = embed_text("In the beginning...")
        >>> len(vector)
        384
    """
    embedder = get_embedder()
    return embedder.embed_text(text)


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Convenience function to embed multiple texts.

    Args:
        texts: List of texts to embed
        batch_size: Batch size for processing

    Returns:
        List of embedding vectors

    Example:
        >>> texts = ["Text one", "Text two", "Text three"]
        >>> vectors = embed_batch(texts)
        >>> len(vectors)
        3
    """
    embedder = get_embedder()
    return embedder.embed_batch(texts, batch_size)
