# embedding_cache.py
# Sistema de cache para embeddings de documentos


import pickle
import hashlib
import json
from pathlib import Path
from typing import Optional, List
import numpy as np


class EmbeddingCache:
    """
    Cache persistente de embeddings para acelerar benchmark e indexação.

    Features:
    - Cache em disco usando pickle
    - Hash MD5 para identificação única (texto + modelo)
    - Invalidação automática ao mudar modelo
    - Estatísticas de hit/miss
    """

    def __init__(self, cache_dir: str = "cache/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de metadata
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()

        # Estatísticas
        self.hits = 0
        self.misses = 0

    def _load_metadata(self) -> dict:
        """Carrega metadata do cache"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"version": "1.0", "entries": {}}

    def _save_metadata(self):
        """Salva metadata do cache"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_hash(self, text: str, model_name: str) -> str:
        """
        Gera hash único para texto + modelo.

        """
        key = f"{model_name}:{text}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """
        Recupera embedding do cache se existir.

        """
        hash_key = self._get_hash(text, model_name)
        cache_file = self.cache_dir / f"{hash_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                self.hits += 1
                return embedding
            except Exception as e:
                print(f"Erro ao ler cache {hash_key}: {e}")
                cache_file.unlink()  # Remove arquivo corrompido

        self.misses += 1
        return None

    def set(self, text: str, model_name: str, embedding: np.ndarray):
        """
        Salva embedding no cache.

        """
        hash_key = self._get_hash(text, model_name)
        cache_file = self.cache_dir / f"{hash_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)

            # Atualiza metadata
            self.metadata["entries"][hash_key] = {
                "model": model_name,
                "text_length": len(text),
                "embedding_shape": embedding.shape
            }
            self._save_metadata()

        except Exception as e:
            print(f"Erro ao salvar cache {hash_key}: {e}")

    def get_batch(self, texts: List[str], model_name: str) -> tuple[List[Optional[np.ndarray]], List[int]]:
        """
        Recupera múltiplos embeddings do cache.

        """
        embeddings = []
        missing_indices = []

        for i, text in enumerate(texts):
            emb = self.get(text, model_name)
            embeddings.append(emb)
            if emb is None:
                missing_indices.append(i)

        return embeddings, missing_indices

    def set_batch(self, texts: List[str], model_name: str, embeddings: List[np.ndarray], show_progress: bool = True):
        """
        Salva múltiplos embeddings no cache de forma otimizada.

        """
        if show_progress:
            print(f"Salvando {len(texts)} embeddings no cache...")

        for idx, (text, emb) in enumerate(zip(texts, embeddings)):
            # Salva embedding sem atualizar metadata a cada vez 
            hash_key = self._get_hash(text, model_name)
            cache_file = self.cache_dir / f"{hash_key}.pkl"

            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(emb, f)

                # Atualiza metadata em memória
                self.metadata["entries"][hash_key] = {
                    "model": model_name,
                    "text_length": len(text),
                    "embedding_shape": emb.shape
                }

            except Exception as e:
                print(f"Erro ao salvar cache {hash_key}: {e}")

            # Mostra progresso a cada 10000
            if show_progress and ((idx + 1) % 10000 == 0 or (idx + 1) == len(texts)):
                print(f"  Salvos: {idx + 1}/{len(texts)} ({(idx+1)/len(texts)*100:.1f}%)")

        # Salva metadata apenas uma vez no final 
        self._save_metadata()
        if show_progress:
            print(f"✓ Cache atualizado com {len(texts)} novos embeddings")

    def clear(self, model_name: Optional[str] = None):
        """
        Limpa cache completo ou de um modelo específico.

        """
        if model_name is None:
            # Limpa tudo
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.metadata = {"version": "1.0", "entries": {}}
            self._save_metadata()
            print("Cache completo limpo")
        else:
            # Limpa apenas modelo específico
            entries_to_remove = []
            for hash_key, meta in self.metadata["entries"].items():
                if meta["model"] == model_name:
                    cache_file = self.cache_dir / f"{hash_key}.pkl"
                    if cache_file.exists():
                        cache_file.unlink()
                    entries_to_remove.append(hash_key)

            for hash_key in entries_to_remove:
                del self.metadata["entries"][hash_key]

            self._save_metadata()
            print(f"Cache do modelo {model_name} limpo ({len(entries_to_remove)} entries)")

    def get_stats(self) -> dict:
        """
        Retorna estatísticas do cache.

        """
        total_entries = len(self.metadata["entries"])
        cache_size_mb = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.pkl")
        ) / (1024 * 1024)

        hit_rate = self.hits / (self.hits + self.misses) * 100 if (self.hits + self.misses) > 0 else 0

        return {
            "total_entries": total_entries,
            "cache_size_mb": cache_size_mb,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "models": list(set(m["model"] for m in self.metadata["entries"].values()))
        }

    def print_stats(self):
        """Imprime estatísticas do cache"""
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print("ESTATÍSTICAS DO CACHE")
        print(f"{'='*50}")
        print(f"Total de entradas: {stats['total_entries']}")
        print(f"Tamanho em disco: {stats['cache_size_mb']:.2f} MB")
        print(f"Hits: {stats['hits']}")
        print(f"Misses: {stats['misses']}")
        print(f"Taxa de acerto: {stats['hit_rate']:.1f}%")
        print(f"Modelos em cache: {len(stats['models'])}")
        for model in stats['models']:
            model_entries = sum(
                1 for m in self.metadata["entries"].values()
                if m["model"] == model
            )
            print(f"  - {model}: {model_entries} embeddings")
        print(f"{'='*50}\n")


# Função auxiliar para uso no benchmark
def encode_with_cache(embedder, texts: List[str], cache: EmbeddingCache, batch_size: int = 32):
    """
    Codifica textos usando cache quando possível.

    """
    model_name = embedder._model_card_data.model_name if hasattr(embedder, '_model_card_data') else str(embedder)

    # Tenta recuperar do cache
    cached_embeddings, missing_indices = cache.get_batch(texts, model_name)

    # Se todos estão em cache, retorna
    if not missing_indices:
        print(f"✓ Todos os {len(texts)} embeddings recuperados do cache")
        return [emb.tolist() for emb in cached_embeddings]

    print(f"Cache: {len(texts) - len(missing_indices)}/{len(texts)} encontrados")

    # Calcula apenas os faltantes
    missing_texts = [texts[i] for i in missing_indices]
    new_embeddings = embedder.encode(missing_texts, batch_size=batch_size)

    # Atualiza cache com novos embeddings
    cache.set_batch(missing_texts, model_name, new_embeddings)

    # Mescla resultados
    result = []
    new_emb_idx = 0
    for i, cached_emb in enumerate(cached_embeddings):
        if cached_emb is None:
            result.append(new_embeddings[new_emb_idx].tolist())
            new_emb_idx += 1
        else:
            result.append(cached_emb.tolist())

    return result


if __name__ == "__main__":
    # Teste do cache
    cache = EmbeddingCache()

    # Simula alguns embeddings
    import numpy as np

    texts = ["café torrado", "soja em grãos", "telefone celular"]
    model = "test-model"

    print("Testando cache de embeddings...")

    # Primeira vez - deve dar miss
    for text in texts:
        emb = cache.get(text, model)
        print(f"  {text}: {'HIT' if emb is not None else 'MISS'}")

    # Salva embeddings
    for text in texts:
        fake_emb = np.random.rand(384)
        cache.set(text, model, fake_emb)

    print("\nApós salvar embeddings:")

    # Segunda vez - deve dar hit
    for text in texts:
        emb = cache.get(text, model)
        print(f"  {text}: {'HIT' if emb is not None else 'MISS'}")

    # Estatísticas
    cache.print_stats()
