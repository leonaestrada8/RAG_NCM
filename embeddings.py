# embeddings.py
# Vetorização de texto usando sentence transformers

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
from tqdm import tqdm

_embedder = None

def get_embedder():
    """Retorna instância do modelo de embedding"""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder

def encode_text(text):
    """Vetoriza texto único"""
    embedder = get_embedder()
    return embedder.encode(text)

def encode_batch(texts, show_progress=True, batch_size=32):
    """Vetoriza lista de textos com progresso"""
    embedder = get_embedder()
    
    if not show_progress or len(texts) < 100:
        return embedder.encode(texts).astype(float).tolist()
    
    all_embeddings = []
    
    with tqdm(total=len(texts), desc="Embeddings", unit="doc") as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = embedder.encode(batch)
            all_embeddings.extend(embeddings)
            pbar.update(len(batch))
    
    return [emb.astype(float).tolist() for emb in all_embeddings]