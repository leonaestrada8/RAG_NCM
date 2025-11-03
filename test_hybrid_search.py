"""
Teste Comparativo: Embedding Puro vs Busca Híbrida

Compara:
1. Embedding puro (ChromaDB apenas)
2. Busca híbrida (60% embedding + 40% BM25)

Métrica: Acurácia Top-1 e Top-5 nos 88 casos de ground truth
"""

import chromadb
import time
import sys
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Imports do projeto
from data_loader import load_ncm_data, load_atributos_data, create_enriched_ncm_text, build_ncm_hierarchy
from hybrid_search import HybridSearcher, create_hybrid_searcher_from_collection
from ground_truth_cases import TEST_CASES


class ComparisonBenchmark:
    """Benchmark comparativo: Embedding vs Híbrido"""

    def __init__(self, model_name="intfloat/multilingual-e5-base"):
        self.model_name = model_name
        self.embedder = None
        self.collection = None
        self.hybrid_searcher = None

        # Dados
        self.ncm_data = None
        self.atributos_data = None
        self.hierarchy = None
        self.atributos_dict = None

    def setup(self):
        """Prepara dados e cria collection"""
        print("="*70)
        print("TESTE COMPARATIVO: EMBEDDING vs HÍBRIDO")
        print("="*70)

        # 1. Carrega modelo
        print(f"\n1. Carregando modelo: {self.model_name}...")
        self.embedder = SentenceTransformer(self.model_name)
        print("[OK] Modelo carregado")

        # 2. Carrega dados NCM
        print("\n2. Carregando dados NCM...")
        self.ncm_data = load_ncm_data()
        self.atributos_data = load_atributos_data()
        self.hierarchy = build_ncm_hierarchy(self.ncm_data)

        # Prepara dicionário de atributos
        self.atributos_dict = {}
        if self.atributos_data and 'listaNcm' in self.atributos_data:
            for ncm_item in self.atributos_data['listaNcm']:
                codigo = ncm_item.get('codigo', '').strip()
                if codigo:
                    self.atributos_dict[codigo] = ncm_item

        print(f"[OK] NCMs: {len(self.ncm_data)}")
        print(f"[OK] Atributos: {len(self.atributos_dict)}")

        # 3. Cria collection ChromaDB
        print("\n3. Criando collection ChromaDB...")
        self._create_collection()
        print("[OK] Collection criada e populada")

        # 4. Cria HybridSearcher
        print("\n4. Criando HybridSearcher...")
        self.hybrid_searcher = create_hybrid_searcher_from_collection(
            self.collection,
            embedding_weight=0.6,
            bm25_weight=0.4
        )
        print("[OK] HybridSearcher pronto")

    def _create_collection(self):
        """Cria e popula collection ChromaDB"""
        # Cria cliente temporário
        client = chromadb.Client()
        self.collection = client.create_collection("ncm_test")

        # Prepara documentos
        documents = []
        metadatas = []
        ids = []

        print("  Preparando documentos NCM...")
        for idx, row in self.ncm_data.iterrows():
            doc_text = create_enriched_ncm_text(row, self.hierarchy, self.atributos_dict)

            if not doc_text or not doc_text.strip():
                continue

            codigo = str(row.get('Código', '')).strip()
            descricao = str(row.get('Descrição', '')).strip()
            codigo_norm = str(row.get('CódigoNormalizado', '')).strip()

            if not codigo and not descricao:
                continue

            documents.append(doc_text)

            hier = self.hierarchy.get(codigo, {})

            metadatas.append({
                "tipo": "ncm",
                "codigo": codigo,
                "codigo_normalizado": codigo_norm,
                "descricao": descricao,
                "nivel": hier.get('nivel', 'desconhecido'),
                "capitulo": hier.get('capitulo', {}).get('codigo', '') if hier.get('capitulo') else ''
            })

            ids.append(f"ncm_{idx}")

        print(f"  Vetorizando {len(documents)} documentos...")
        start = time.time()
        embeddings = self.embedder.encode(documents, show_progress_bar=True)
        elapsed = time.time() - start
        print(f"  Vetorização: {elapsed:.1f}s ({len(documents)/elapsed:.1f} docs/s)")

        # Adiciona à collection em lotes
        BATCH_SIZE = 5000
        print(f"  Indexando em lotes de {BATCH_SIZE}...")
        for i in range(0, len(documents), BATCH_SIZE):
            end = min(i + BATCH_SIZE, len(documents))
            self.collection.add(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end].tolist(),
                metadatas=metadatas[i:end]
            )
            print(f"    Lote {i//BATCH_SIZE + 1}: {end}/{len(documents)}")

        print(f"  [OK] {len(documents)} documentos indexados")

    def test_embedding_only(self) -> dict:
        """Testa com embedding puro (ChromaDB)"""
        print("\n" + "="*70)
        print("TESTE 1: EMBEDDING PURO (ChromaDB)")
        print("="*70)

        correct_top1 = 0
        correct_top5 = 0
        total_distance = 0
        errors = []

        start = time.time()

        for idx, (query, expected_ncm) in enumerate(TEST_CASES):
            # Usa o mesmo embedder para query que foi usado na indexação
            query_embedding = self.embedder.encode([query]).tolist()

            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=5
            )

            if not results['ids'] or len(results['ids'][0]) == 0:
                errors.append({
                    'query': query,
                    'expected': expected_ncm,
                    'error': 'Nenhum resultado encontrado'
                })
                continue

            # Top-1
            top1_code = results['metadatas'][0][0]['codigo'][:4]
            if top1_code == expected_ncm[:4]:
                correct_top1 += 1

            # Top-5
            found_in_top5 = any(
                meta['codigo'][:4] == expected_ncm[:4]
                for meta in results['metadatas'][0]
            )
            if found_in_top5:
                correct_top5 += 1
            else:
                errors.append({
                    'query': query,
                    'expected': expected_ncm,
                    'got_top1': top1_code,
                    'distance': results['distances'][0][0]
                })

            # Distância média
            total_distance += results['distances'][0][0]

        elapsed = time.time() - start

        accuracy_top1 = correct_top1 / len(TEST_CASES) * 100
        accuracy_top5 = correct_top5 / len(TEST_CASES) * 100
        mean_distance = total_distance / len(TEST_CASES)

        # Score geral (mesma fórmula do benchmark)
        score = (accuracy_top5 * 0.4) + (accuracy_top1 * 0.3) + \
                ((1 - mean_distance) * 100 * 0.2) + (52.4 * 0.1)  # 52.4 = cobertura fixa

        print(f"\nResultados:")
        print(f"  Acurácia Top-1: {accuracy_top1:.1f}% ({correct_top1}/{len(TEST_CASES)})")
        print(f"  Acurácia Top-5: {accuracy_top5:.1f}% ({correct_top5}/{len(TEST_CASES)})")
        print(f"  Distância Média: {mean_distance:.4f}")
        print(f"  Score Geral: {score:.1f}/100")
        print(f"  Tempo: {elapsed:.2f}s ({len(TEST_CASES)/elapsed:.1f} queries/s)")
        print(f"  Erros: {len(errors)}")

        return {
            'method': 'Embedding Puro',
            'accuracy_top1': accuracy_top1,
            'accuracy_top5': accuracy_top5,
            'mean_distance': mean_distance,
            'score': score,
            'elapsed': elapsed,
            'errors': errors
        }

    def test_hybrid(self, embedding_weight=0.6, bm25_weight=0.4) -> dict:
        """Testa com busca híbrida"""
        print("\n" + "="*70)
        print(f"TESTE 2: BUSCA HÍBRIDA ({int(embedding_weight*100)}% EMB + {int(bm25_weight*100)}% BM25)")
        print("="*70)

        # Atualiza pesos
        self.hybrid_searcher.embedding_weight = embedding_weight
        self.hybrid_searcher.bm25_weight = bm25_weight

        correct_top1 = 0
        correct_top5 = 0
        total_distance = 0
        errors = []

        start = time.time()

        for idx, (query, expected_ncm) in enumerate(TEST_CASES):
            results = self.hybrid_searcher.search(query, top_k=5, return_scores=True)

            if not results:
                errors.append({
                    'query': query,
                    'expected': expected_ncm,
                    'error': 'Nenhum resultado encontrado'
                })
                continue

            # Top-1
            top1_code = results[0]['metadata']['codigo'][:4]
            if top1_code == expected_ncm[:4]:
                correct_top1 += 1

            # Top-5
            found_in_top5 = any(
                r['metadata']['codigo'][:4] == expected_ncm[:4]
                for r in results
            )
            if found_in_top5:
                correct_top5 += 1
            else:
                errors.append({
                    'query': query,
                    'expected': expected_ncm,
                    'got_top1': top1_code,
                    'hybrid_score': results[0]['hybrid_score'],
                    'embedding_score': results[0]['embedding_score'],
                    'bm25_score': results[0]['bm25_score']
                })

            # Distância média (usa distância do embedding)
            total_distance += results[0].get('distance', 0.5)

        elapsed = time.time() - start

        accuracy_top1 = correct_top1 / len(TEST_CASES) * 100
        accuracy_top5 = correct_top5 / len(TEST_CASES) * 100
        mean_distance = total_distance / len(TEST_CASES)

        # Score geral (mesma fórmula do benchmark)
        score = (accuracy_top5 * 0.4) + (accuracy_top1 * 0.3) + \
                ((1 - mean_distance) * 100 * 0.2) + (52.4 * 0.1)

        print(f"\nResultados:")
        print(f"  Acurácia Top-1: {accuracy_top1:.1f}% ({correct_top1}/{len(TEST_CASES)})")
        print(f"  Acurácia Top-5: {accuracy_top5:.1f}% ({correct_top5}/{len(TEST_CASES)})")
        print(f"  Distância Média: {mean_distance:.4f}")
        print(f"  Score Geral: {score:.1f}/100")
        print(f"  Tempo: {elapsed:.2f}s ({len(TEST_CASES)/elapsed:.1f} queries/s)")
        print(f"  Erros: {len(errors)}")

        return {
            'method': f'Híbrido ({int(embedding_weight*100)}/{int(bm25_weight*100)})',
            'accuracy_top1': accuracy_top1,
            'accuracy_top5': accuracy_top5,
            'mean_distance': mean_distance,
            'score': score,
            'elapsed': elapsed,
            'errors': errors,
            'weights': {
                'embedding': embedding_weight,
                'bm25': bm25_weight
            }
        }

    def auto_tune_weights(self):
        """Auto-tune dos pesos usando ground truth"""
        print("\n" + "="*70)
        print("AUTO-TUNING DE PESOS")
        print("="*70)

        results = self.hybrid_searcher.tune_weights(
            TEST_CASES,
            weight_range=[0.4, 0.5, 0.6, 0.7, 0.8]
        )

        return results

    def compare(self):
        """Executa comparação completa"""
        # Teste 1: Embedding puro
        emb_results = self.test_embedding_only()

        # Teste 2: Híbrido (60/40)
        hybrid_results = self.test_hybrid(embedding_weight=0.6, bm25_weight=0.4)

        # Comparação
        print("\n" + "="*70)
        print("COMPARAÇÃO FINAL")
        print("="*70)

        print(f"\n{'Métrica':<20} {'Embedding':<15} {'Híbrido':<15} {'Ganho':<15}")
        print("-"*70)

        # Top-1
        diff_top1 = hybrid_results['accuracy_top1'] - emb_results['accuracy_top1']
        print(f"{'Top-1 Accuracy':<20} {emb_results['accuracy_top1']:>6.1f}%{' '*7} "
              f"{hybrid_results['accuracy_top1']:>6.1f}%{' '*7} "
              f"{diff_top1:>+6.1f}%")

        # Top-5
        diff_top5 = hybrid_results['accuracy_top5'] - emb_results['accuracy_top5']
        print(f"{'Top-5 Accuracy':<20} {emb_results['accuracy_top5']:>6.1f}%{' '*7} "
              f"{hybrid_results['accuracy_top5']:>6.1f}%{' '*7} "
              f"{diff_top5:>+6.1f}%")

        # Score
        diff_score = hybrid_results['score'] - emb_results['score']
        print(f"{'Score Geral':<20} {emb_results['score']:>6.1f}/100{' '*5} "
              f"{hybrid_results['score']:>6.1f}/100{' '*5} "
              f"{diff_score:>+6.1f}")

        # Distância
        diff_dist = emb_results['mean_distance'] - hybrid_results['mean_distance']
        print(f"{'Distância Média':<20} {emb_results['mean_distance']:>6.4f}{' '*9} "
              f"{hybrid_results['mean_distance']:>6.4f}{' '*9} "
              f"{diff_dist:>+6.4f}")

        print("\n" + "="*70)
        print("CONCLUSÃO")
        print("="*70)

        if diff_score > 0:
            print(f"[OK] Busca Híbrida GANHOU {diff_score:.1f} pontos")
            print(f"  Top-1: {diff_top1:+.1f}% | Top-5: {diff_top5:+.1f}%")
            print(f"\n  Recomendação: USAR BUSCA HÍBRIDA em produção")
        elif diff_score < 0:
            print(f"[AVISO] Busca Híbrida PERDEU {abs(diff_score):.1f} pontos")
            print(f"  Top-1: {diff_top1:+.1f}% | Top-5: {diff_top5:+.1f}%")
            print(f"\n  Recomendação: Manter embedding puro ou ajustar pesos")
        else:
            print(f"  Empate técnico - diferença desprezível")

        return {
            'embedding': emb_results,
            'hybrid': hybrid_results,
            'improvement': {
                'top1': diff_top1,
                'top5': diff_top5,
                'score': diff_score,
                'distance': diff_dist
            }
        }


def main():
    """Executa teste comparativo completo"""
    print("\n" + "="*70)
    print("TESTE COMPARATIVO: EMBEDDING vs BUSCA HIBRIDA")
    print("="*70 + "\n")

    # Cria benchmark
    benchmark = ComparisonBenchmark(model_name="intfloat/multilingual-e5-base")

    # Setup
    benchmark.setup()

    # Executa comparação
    results = benchmark.compare()

    # Optional: Auto-tune
    print("\n" + "="*70)
    print("EXTRA: AUTO-TUNING DE PESOS")
    print("="*70)
    print("Deseja executar auto-tuning de pesos? (S/n): ", end='')
    try:
        response = input().strip().lower()
        if response in ['s', 'sim', '']:
            tune_results = benchmark.auto_tune_weights()

            # Re-testa com pesos otimizados
            print("\n" + "="*70)
            print(f"RE-TESTANDO COM PESOS OTIMIZADOS")
            print("="*70)
            optimized_results = benchmark.test_hybrid(
                embedding_weight=tune_results['best_embedding_weight'],
                bm25_weight=tune_results['best_bm25_weight']
            )

            print(f"\nScore com pesos otimizados: {optimized_results['score']:.1f}/100")
            print(f"Ganho vs embedding puro: {optimized_results['score'] - results['embedding']['score']:+.1f}")
    except:
        pass

    print("\n[OK] Teste completo!")
    print(f"\nArquivos de referência:")
    print(f"  - hybrid_search.py: Módulo de busca híbrida")
    print(f"  - test_hybrid_search.py: Este script de teste")


if __name__ == "__main__":
    main()
