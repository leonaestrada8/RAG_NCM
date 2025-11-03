"""
Módulo de Busca Híbrida: Embedding (semântico) + BM25 (léxico)

Combina o melhor dos dois mundos:
- Embedding: captura semântica ("bebida quente" → café)
- BM25: captura keywords exatas ("0901", "café", "torrado")

Performance esperada: +5-10 pontos vs embedding puro
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from rank_bm25 import BM25Okapi
import unicodedata


def normalize_text_for_bm25(text: str) -> str:
    """
    Normaliza texto para busca BM25

    Estratégia:
    - Remove acentos (café → cafe)
    - Lowercase
    - Preserva números (importante para NCM)
    - Remove pontuação excessiva
    """
    if not text:
        return ""

    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

    # Lowercase
    text = text.lower()

    # Remove pontuação, mas preserva números e espaços
    text = re.sub(r'[^\w\s]', ' ', text)

    # Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def tokenize_for_bm25(text: str) -> List[str]:
    """
    Tokeniza texto para BM25

    Preserva:
    - Códigos NCM (ex: "0901", "8703")
    - Palavras importantes
    - Números
    """
    normalized = normalize_text_for_bm25(text)

    # Split por espaços
    tokens = normalized.split()

    # Remove tokens muito curtos (exceto se forem números)
    tokens = [t for t in tokens if len(t) >= 2 or t.isdigit()]

    return tokens


class HybridSearcher:
    """
    Busca Híbrida: Combina Embedding (ChromaDB) + BM25 (léxico)

    Pesos padrão:
    - 60% embedding (semântico)
    - 40% BM25 (léxico)

    Uso:
        searcher = HybridSearcher(collection, documents, metadatas, ids)
        results = searcher.search("café torrado", top_k=5)
    """

    def __init__(
        self,
        collection,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embedding_weight: float = 0.6,
        bm25_weight: float = 0.4
    ):
        """
        Inicializa busca híbrida

        Args:
            collection: ChromaDB collection (para embedding search)
            documents: Lista de textos dos documentos
            metadatas: Lista de metadados
            ids: Lista de IDs
            embedding_weight: Peso do embedding (padrão: 0.6)
            bm25_weight: Peso do BM25 (padrão: 0.4)
        """
        self.collection = collection
        self.documents = documents
        self.metadatas = metadatas
        self.ids = ids

        # Pesos
        self.embedding_weight = embedding_weight
        self.bm25_weight = bm25_weight

        # Validação
        assert abs(embedding_weight + bm25_weight - 1.0) < 0.001, \
            "Pesos devem somar 1.0"

        # Prepara BM25
        print("Preparando índice BM25...")
        self._prepare_bm25()
        print(f"✓ BM25 pronto com {len(self.documents)} documentos")

    def _prepare_bm25(self):
        """Prepara índice BM25"""
        # Tokeniza todos os documentos
        self.tokenized_docs = [tokenize_for_bm25(doc) for doc in self.documents]

        # Cria índice BM25
        self.bm25 = BM25Okapi(self.tokenized_docs)

        # Mapeia ID -> índice para acesso rápido
        self.id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.ids)}

    def search(
        self,
        query: str,
        top_k: int = 5,
        return_scores: bool = False
    ) -> List[Dict]:
        """
        Busca híbrida: combina embedding + BM25

        Args:
            query: Texto da busca
            top_k: Número de resultados
            return_scores: Se True, retorna scores detalhados

        Returns:
            Lista de resultados ordenados por score híbrido
        """
        # 1. Busca por embedding (semântico)
        embedding_results = self._search_embedding(query, top_k=top_k * 3)

        # 2. Busca por BM25 (léxico)
        bm25_results = self._search_bm25(query, top_k=top_k * 3)

        # 3. Combina scores
        combined = self._combine_scores(embedding_results, bm25_results)

        # 4. Ordena e retorna top-k
        sorted_results = sorted(combined, key=lambda x: x['hybrid_score'], reverse=True)

        final_results = sorted_results[:top_k]

        # Adiciona informações detalhadas se solicitado
        if return_scores:
            for result in final_results:
                result['weights'] = {
                    'embedding': self.embedding_weight,
                    'bm25': self.bm25_weight
                }
        else:
            # Remove scores intermediários para simplicidade
            for result in final_results:
                result.pop('embedding_score', None)
                result.pop('bm25_score', None)

        return final_results

    def _search_embedding(self, query: str, top_k: int) -> List[Dict]:
        """Busca por embedding (ChromaDB)"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Converte para formato unificado
        embedding_results = []

        if results['ids'] and len(results['ids'][0]) > 0:
            for idx, doc_id in enumerate(results['ids'][0]):
                # Distância no ChromaDB (menor = mais similar)
                distance = results['distances'][0][idx]

                # Converte distância para similarity (0-1, maior = melhor)
                similarity = max(0, 1 - distance)

                embedding_results.append({
                    'id': doc_id,
                    'embedding_score': similarity,
                    'distance': distance,
                    'metadata': results['metadatas'][0][idx],
                    'document': results['documents'][0][idx]
                })

        return embedding_results

    def _search_bm25(self, query: str, top_k: int) -> List[Dict]:
        """Busca por BM25 (léxico)"""
        # Tokeniza query
        query_tokens = tokenize_for_bm25(query)

        # Busca BM25
        scores = self.bm25.get_scores(query_tokens)

        # Pega top-k índices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Normaliza scores para 0-1
        max_score = scores.max() if len(scores) > 0 and scores.max() > 0 else 1.0

        bm25_results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Apenas resultados com score positivo
                normalized_score = scores[idx] / max_score

                bm25_results.append({
                    'id': self.ids[idx],
                    'bm25_score': normalized_score,
                    'bm25_raw_score': scores[idx],
                    'metadata': self.metadatas[idx],
                    'document': self.documents[idx]
                })

        return bm25_results

    def _combine_scores(
        self,
        embedding_results: List[Dict],
        bm25_results: List[Dict]
    ) -> List[Dict]:
        """
        Combina scores de embedding e BM25

        Formula:
            hybrid_score = (embedding_weight * emb_score) + (bm25_weight * bm25_score)
        """
        # Cria dicionário para combinar resultados
        combined = {}

        # Adiciona scores de embedding
        for result in embedding_results:
            doc_id = result['id']
            combined[doc_id] = {
                'id': doc_id,
                'embedding_score': result['embedding_score'],
                'bm25_score': 0.0,  # Será atualizado se aparecer no BM25
                'metadata': result['metadata'],
                'document': result['document'],
                'distance': result.get('distance', 0)
            }

        # Adiciona/atualiza scores de BM25
        for result in bm25_results:
            doc_id = result['id']
            if doc_id in combined:
                combined[doc_id]['bm25_score'] = result['bm25_score']
            else:
                combined[doc_id] = {
                    'id': doc_id,
                    'embedding_score': 0.0,  # Não apareceu no embedding search
                    'bm25_score': result['bm25_score'],
                    'metadata': result['metadata'],
                    'document': result['document'],
                    'distance': 1.0  # Distância máxima se não apareceu no embedding
                }

        # Calcula score híbrido
        for doc_id in combined:
            emb_score = combined[doc_id]['embedding_score']
            bm25_score = combined[doc_id]['bm25_score']

            hybrid_score = (
                self.embedding_weight * emb_score +
                self.bm25_weight * bm25_score
            )

            combined[doc_id]['hybrid_score'] = hybrid_score

        return list(combined.values())

    def tune_weights(
        self,
        test_cases: List[Tuple[str, str]],
        weight_range: List[float] = None
    ) -> Dict:
        """
        Auto-tune dos pesos embedding/BM25 usando casos de teste

        Args:
            test_cases: Lista de (query, ncm_esperado)
            weight_range: Lista de pesos para embedding (ex: [0.5, 0.6, 0.7, 0.8])

        Returns:
            Dict com melhor peso e acurácia
        """
        if weight_range is None:
            weight_range = [0.5, 0.6, 0.7, 0.8]

        best_weight = None
        best_accuracy = 0
        results = []

        print(f"\n🔧 Tunando pesos com {len(test_cases)} casos de teste...")

        for emb_weight in weight_range:
            bm25_weight = 1.0 - emb_weight

            # Atualiza pesos temporariamente
            original_emb = self.embedding_weight
            original_bm25 = self.bm25_weight

            self.embedding_weight = emb_weight
            self.bm25_weight = bm25_weight

            # Testa acurácia
            correct_top1 = 0
            correct_top5 = 0

            for query, expected_ncm in test_cases:
                search_results = self.search(query, top_k=5)

                # Verifica Top-1
                if search_results and search_results[0]['metadata']['codigo'][:4] == expected_ncm[:4]:
                    correct_top1 += 1

                # Verifica Top-5
                found_in_top5 = any(
                    r['metadata']['codigo'][:4] == expected_ncm[:4]
                    for r in search_results[:5]
                )
                if found_in_top5:
                    correct_top5 += 1

            accuracy_top1 = correct_top1 / len(test_cases) * 100
            accuracy_top5 = correct_top5 / len(test_cases) * 100

            results.append({
                'embedding_weight': emb_weight,
                'bm25_weight': bm25_weight,
                'accuracy_top1': accuracy_top1,
                'accuracy_top5': accuracy_top5
            })

            print(f"  Emb={emb_weight:.1f} / BM25={bm25_weight:.1f} → "
                  f"Top-1: {accuracy_top1:.1f}% | Top-5: {accuracy_top5:.1f}%")

            # Score combinado (priorizando Top-1)
            combined_score = accuracy_top1 * 0.7 + accuracy_top5 * 0.3

            if combined_score > best_accuracy:
                best_accuracy = combined_score
                best_weight = emb_weight

        # Restaura pesos originais
        self.embedding_weight = original_emb
        self.bm25_weight = original_bm25

        # Atualiza para melhor peso encontrado
        if best_weight is not None:
            self.embedding_weight = best_weight
            self.bm25_weight = 1.0 - best_weight

            print(f"\n✓ Melhor peso encontrado:")
            print(f"  Embedding: {self.embedding_weight:.1f}")
            print(f"  BM25: {self.bm25_weight:.1f}")

        return {
            'best_embedding_weight': best_weight,
            'best_bm25_weight': 1.0 - best_weight,
            'best_accuracy': best_accuracy,
            'all_results': results
        }


def create_hybrid_searcher_from_collection(
    collection,
    embedding_weight: float = 0.6,
    bm25_weight: float = 0.4
) -> HybridSearcher:
    """
    Helper para criar HybridSearcher a partir de uma collection existente

    Args:
        collection: ChromaDB collection
        embedding_weight: Peso do embedding (padrão: 0.6)
        bm25_weight: Peso do BM25 (padrão: 0.4)

    Returns:
        HybridSearcher configurado
    """
    # Recupera todos os documentos da collection
    results = collection.get()

    documents = results['documents']
    metadatas = results['metadatas']
    ids = results['ids']

    print(f"Criando HybridSearcher com {len(documents)} documentos...")

    return HybridSearcher(
        collection=collection,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embedding_weight=embedding_weight,
        bm25_weight=bm25_weight
    )
