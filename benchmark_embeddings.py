# benchmark_embeddings.py
# Benchmark de modelos de embedding para sistema RAG NCM
# Testa 5 modelos diferentes e gera relatorio comparativo

import os
import sys
import time
import json
import pandas as pd
import chromadb
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Adiciona diretorio do projeto ao path
sys.path.insert(0, '/mnt/project')

from data_loader import (
    load_ncm_data,
    load_atributos_data,
    build_ncm_hierarchy,
    create_atributos_dict,
    create_enriched_ncm_text,
    create_atributo_description
)
from config import BATCH_SIZE
from tqdm import tqdm

# Importa melhorias
from embedding_cache import EmbeddingCache, encode_with_cache
from ground_truth_cases import TEST_CASES


# Lista de modelos para testar - AJUSTADA APÓS BENCHMARK INICIAL
# Baseado nos resultados: e5-base venceu com 75.6/100
# Testando modelos promissores e SOTA 2024
MODELS_TO_TEST = [
    # Vencedor do benchmark inicial
    'intfloat/multilingual-e5-base',           # Score: 75.6 - Baseline atual

    # Evolução do vencedor (maior e melhor)
    'intfloat/multilingual-e5-large',          # Versão large - espera-se +5-8 pontos

    # Modelos SOTA 2024 multilíngue
    'BAAI/bge-m3',                             # SOTA 2024 - excelente multilíngue
    'BAAI/bge-large-en-v1.5',                  # Alternativa BGE large

    # Para comparação de velocidade (opcional)
    # 'sentence-transformers/all-MiniLM-L6-v2', # Rápido mas não multilíngue (50.1)
]

# Modelos REMOVIDOS (baixa performance ou erros):
# ❌ 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'  # 54.0 - muito lento (127 min)
# ❌ 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # 36.5 - performance ruim
# ❌ 'sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2'   # Erro 401 - modelo não existe


class EmbeddingBenchmark:
    """Classe para benchmark de modelos de embedding"""

    def __init__(self, use_cache=True):
        self.results = []
        self.ncm_data = None
        self.atributos_data = None
        self.hierarchy = None
        self.atributos_dict = None

        # Cache de embeddings para acelerar re-execuções
        self.use_cache = use_cache
        self.cache = EmbeddingCache() if use_cache else None

        if self.use_cache:
            print(f"✓ Cache de embeddings ATIVADO")
            self.cache.print_stats()
        
    def load_data(self):
        """Carrega dados NCM e atributos uma vez"""
        print("\n" + "="*70)
        print("CARREGANDO DADOS")
        print("="*70)
        
        self.ncm_data = load_ncm_data()
        self.atributos_data = load_atributos_data()
        self.hierarchy = build_ncm_hierarchy(self.ncm_data)
        self.atributos_dict = create_atributos_dict(self.atributos_data)
        
        print(f"\nNCMs carregados: {len(self.ncm_data)}")
        print(f"Atributos carregados: {len(self.atributos_data.get('listaNcm', []))}")
    
    def encode_batch(self, embedder, texts, batch_size=32):
        """Vetoriza lista de textos em lotes com cache"""
        if self.use_cache and self.cache:
            # Usa cache para acelerar
            model_name = embedder._model_card_data.model_name if hasattr(embedder, '_model_card_data') else str(type(embedder).__name__)

            # Tenta recuperar do cache
            cached_embeddings, missing_indices = self.cache.get_batch(texts, model_name)

            # Se todos estão em cache, retorna direto
            if not missing_indices:
                print(f"✓ Todos os {len(texts)} embeddings recuperados do cache")
                return [emb.tolist() for emb in cached_embeddings]

            print(f"Cache: {len(texts) - len(missing_indices)}/{len(texts)} encontrados, calculando {len(missing_indices)} faltantes...")

            # Calcula apenas os faltantes
            missing_texts = [texts[i] for i in missing_indices]
            new_embeddings = []

            with tqdm(total=len(missing_texts), desc="Embeddings (novos)", unit="doc") as pbar:
                for i in range(0, len(missing_texts), batch_size):
                    batch = missing_texts[i:i+batch_size]
                    embeddings = embedder.encode(batch)
                    new_embeddings.extend(embeddings)
                    pbar.update(len(batch))

            # Atualiza cache com novos embeddings (batch otimizado)
            missing_texts = [texts[i] for i in missing_indices]
            self.cache.set_batch(missing_texts, model_name, new_embeddings, show_progress=True)

            # Mescla resultados
            result = []
            new_emb_idx = 0
            for i, cached_emb in enumerate(cached_embeddings):
                if cached_emb is None:
                    result.append(new_embeddings[new_emb_idx].astype(float).tolist())
                    new_emb_idx += 1
                else:
                    result.append(cached_emb.tolist())

            return result

        else:
            # Sem cache - modo original
            all_embeddings = []

            with tqdm(total=len(texts), desc="Embeddings", unit="doc") as pbar:
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    embeddings = embedder.encode(batch)
                    all_embeddings.extend(embeddings)
                    pbar.update(len(batch))

            return [emb.astype(float).tolist() for emb in all_embeddings]
    
    def prepare_ncm_documents(self, embedder):
        """Prepara documentos NCM para indexacao"""
        documents = []
        metadatas = []
        ids = []
        
        cols = self.ncm_data.columns.tolist()
        col_codigo = cols[0]
        col_desc = cols[1] if len(cols) > 1 else None
        col_codigo_norm = None
        for col in cols:
            if 'Normalizado' in col or 'normalizado' in col:
                col_codigo_norm = col
                break
        if not col_codigo_norm and len(cols) > 2:
            col_codigo_norm = cols[2]
        
        print("Preparando documentos NCM...")
        skipped = 0
        
        for idx, row in tqdm(self.ncm_data.iterrows(), total=len(self.ncm_data), desc="NCM"):
            doc_text = create_enriched_ncm_text(row, self.hierarchy, self.atributos_dict)
            
            if doc_text is None or not doc_text.strip():
                skipped += 1
                continue
            
            codigo = str(row.get(col_codigo, '')).strip() if col_codigo else ''
            descricao = str(row.get(col_desc, '')).strip() if col_desc else ''
            codigo_norm = str(row.get(col_codigo_norm, '')).strip() if col_codigo_norm else codigo
            
            if not codigo and not descricao:
                skipped += 1
                continue
            
            documents.append(doc_text)
            
            hier = self.hierarchy.get(codigo, {})
            
            metadata = {
                "tipo": "ncm",
                "codigo": codigo,
                "codigo_normalizado": codigo_norm,
                "descricao": descricao,
                "nivel": hier.get('nivel', 'desconhecido'),
                "capitulo": hier.get('capitulo', {}).get('codigo', '') if hier.get('capitulo') else '',
                "tem_atributos": codigo_norm in self.atributos_dict
            }
            
            metadatas.append(metadata)
            ids.append(f"ncm_{idx}")
        
        if skipped > 0:
            print(f"  Pulados {skipped} documentos vazios")
        
        return documents, metadatas, ids
    
    def prepare_atributos_documents(self):
        """Prepara documentos de atributos"""
        documents = []
        metadatas = []
        ids = []
        
        if not self.atributos_data or 'listaNcm' not in self.atributos_data:
            return documents, metadatas, ids
        
        lista_ncm = self.atributos_data['listaNcm']
        total_atributos = sum(len(item['listaAtributos']) for item in lista_ncm)
        
        print("Preparando documentos de atributos...")
        with tqdm(total=total_atributos, desc="Atributos") as pbar:
            for idx, ncm_item in enumerate(lista_ncm):
                ncm_code = ncm_item['codigoNcm']
                
                for attr_idx, atributo in enumerate(ncm_item['listaAtributos']):
                    doc_text = create_atributo_description(ncm_code, atributo)
                    documents.append(doc_text)
                    
                    metadata = {
                        "tipo": "atributo",
                        "ncm_codigo": ncm_code,
                        "atributo_codigo": atributo['codigo'],
                        "modalidade": atributo['modalidade'],
                        "obrigatorio": atributo['obrigatorio'],
                        "multivalorado": atributo['multivalorado'],
                        "data_inicio_vigencia": atributo['dataInicioVigencia']
                    }
                    
                    metadatas.append(metadata)
                    ids.append(f"attr_{idx}_{attr_idx}")
                    pbar.update(1)
        
        return documents, metadatas, ids
    
    def index_documents(self, collection, embedder, documents, metadatas, ids):
        """Indexa documentos no banco vetorial"""
        if not documents:
            print("Nenhum documento para indexar")
            return
        
        total = len(documents)
        vectors = self.encode_batch(embedder, documents)
        
        print(f"\nIndexando {total} documentos em lotes de {BATCH_SIZE}...")
        
        num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        with tqdm(total=num_batches, desc="Indexacao") as pbar:
            for start in range(0, total, BATCH_SIZE):
                end = min(start + BATCH_SIZE, total)
                
                collection.add(
                    ids=ids[start:end],
                    documents=documents[start:end],
                    embeddings=vectors[start:end],
                    metadatas=metadatas[start:end],
                )
                
                pbar.update(1)
        
        print(f"Indexacao concluida: {total} documentos")
    
    def run_diagnostics(self, collection, embedder, model_name):
        """Executa diagnosticos para um modelo"""
        print("\n" + "="*70)
        print(f"DIAGNOSTICOS: {model_name}")
        print("="*70)
        
        stats = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Teste de busca basica
        test_queries = [
            "cafe torrado", "soja", "carne bovina", "acucar",
            "telefone celular", "arroz", "leite", "computador"
        ]
        
        all_distances = []
        for query in test_queries:
            emb = embedder.encode(query).astype(float).tolist()
            results = collection.query(
                query_embeddings=[emb],
                n_results=10,
                where={"tipo": "ncm"}
            )
            
            if results and results.get('distances'):
                all_distances.extend(results['distances'][0])
        
        if all_distances:
            import numpy as np
            stats['mean_distance'] = float(np.mean(all_distances))
            stats['median_distance'] = float(np.median(all_distances))
            stats['std_distance'] = float(np.std(all_distances))
            stats['min_distance'] = float(min(all_distances))
            stats['max_distance'] = float(max(all_distances))
            
            print(f"\nDistancias:")
            print(f"  Media: {stats['mean_distance']:.4f}")
            print(f"  Mediana: {stats['median_distance']:.4f}")
            print(f"  Desvio: {stats['std_distance']:.4f}")
            print(f"  Min: {stats['min_distance']:.4f}")
            print(f"  Max: {stats['max_distance']:.4f}")
        
        # Teste com ground truth expandido (90+ casos)
        test_cases = TEST_CASES
        print(f"\nTestando com {len(test_cases)} casos de ground truth...")
        
        hits = 0
        top1_hits = 0
        
        print("\nTestes com ground truth:")
        for query, expected_chapter in test_cases:
            emb = embedder.encode(query).astype(float).tolist()
            search_results = collection.query(
                query_embeddings=[emb],
                n_results=5,
                where={"tipo": "ncm"}
            )
            
            if not search_results or not search_results.get('metadatas'):
                continue
            
            top_results = search_results['metadatas'][0]
            
            found = False
            top1_match = False
            
            for i, meta in enumerate(top_results):
                ncm_code = meta.get('codigo_normalizado', '') or meta.get('codigo', '')
                chapter = ncm_code[:4].replace('.', '')
                
                if chapter == expected_chapter:
                    found = True
                    if i == 0:
                        top1_match = True
                    break
            
            if found:
                hits += 1
                if top1_match:
                    top1_hits += 1
        
        stats['accuracy_top5'] = 100 * hits / len(test_cases) if test_cases else 0
        stats['accuracy_top1'] = 100 * top1_hits / len(test_cases) if test_cases else 0
        
        print(f"  Acuracia Top-5: {stats['accuracy_top5']:.1f}%")
        print(f"  Acuracia Top-1: {stats['accuracy_top1']:.1f}%")
        
        # Cobertura de atributos
        try:
            all_ncm = collection.get(where={"tipo": "ncm"}, limit=20000)
            all_attr = collection.get(where={"tipo": "atributo"}, limit=60000)
            
            stats['total_ncm'] = len(all_ncm['ids'])
            stats['total_attr'] = len(all_attr['ids'])
            
            ncm_with_attr = set()
            for meta in all_attr['metadatas']:
                ncm_code = meta.get('ncm_codigo')
                if ncm_code:
                    ncm_with_attr.add(ncm_code)
            
            stats['ncm_with_attr'] = len(ncm_with_attr)
            stats['coverage_pct'] = 100 * len(ncm_with_attr) / stats['total_ncm'] if stats['total_ncm'] > 0 else 0
            
            print(f"\nCobertura:")
            print(f"  NCMs: {stats['total_ncm']}")
            print(f"  Atributos: {stats['total_attr']}")
            print(f"  Cobertura: {stats['coverage_pct']:.1f}%")
        except Exception as e:
            print(f"Erro na cobertura: {e}")
        
        # Score geral
        score = (
            stats.get('accuracy_top5', 0) * 0.4 +
            stats.get('accuracy_top1', 0) * 0.3 +
            (100 - min(100, stats.get('mean_distance', 1) * 50)) * 0.2 +
            stats.get('coverage_pct', 0) * 0.1
        )
        stats['score'] = score
        
        print(f"\nScore Geral: {score:.1f}/100")
        
        return stats
    
    def validate_model(self, model_name):
        """Valida se modelo existe antes de testar"""
        try:
            from huggingface_hub import model_info
            print(f"Validando modelo {model_name}...")
            model_info(model_name)
            print(f"✓ Modelo {model_name} validado com sucesso")
            return True
        except Exception as e:
            print(f"✗ ERRO: Modelo {model_name} não encontrado ou inacessível: {e}")
            return False

    def test_model(self, model_name):
        """Testa um modelo especifico"""
        print("\n" + "#"*70)
        print(f"# TESTANDO MODELO: {model_name}")
        print("#"*70)

        start_time = time.time()

        # Valida modelo antes de testar
        if not self.validate_model(model_name):
            print(f"\n⚠️  PULANDO modelo {model_name} - validação falhou")
            self.results.append({
                'model_name': model_name,
                'error': 'Modelo não encontrado ou inacessível',
                'elapsed_time': time.time() - start_time,
                'status': 'skipped'
            })
            return

        # Cria banco de dados especifico
        db_path = f"benchmark_db_{model_name.replace('/', '_').replace('-', '_')}"
        collection_name = "ncm_atributos"

        try:
            # Remove banco anterior se existir
            if os.path.exists(db_path):
                import shutil
                shutil.rmtree(db_path)

            # Cria novo cliente e colecao
            client = chromadb.PersistentClient(path=db_path)
            collection = client.create_collection(collection_name)

            # Carrega modelo
            print(f"\nCarregando modelo: {model_name}")
            embedder = SentenceTransformer(model_name)
            print(f"✓ Modelo carregado com sucesso")
            
            # Prepara documentos
            ncm_docs, ncm_metas, ncm_ids = self.prepare_ncm_documents(embedder)
            attr_docs, attr_metas, attr_ids = self.prepare_atributos_documents()
            
            # Indexa NCMs
            self.index_documents(collection, embedder, ncm_docs, ncm_metas, ncm_ids)
            
            # Indexa atributos
            self.index_documents(collection, embedder, attr_docs, attr_metas, attr_ids)
            
            # Executa diagnosticos
            stats = self.run_diagnostics(collection, embedder, model_name)
            
            # Tempo de execucao
            elapsed_time = time.time() - start_time
            stats['elapsed_time'] = elapsed_time
            
            print(f"\nTempo de execucao: {elapsed_time:.1f}s")
            
            self.results.append(stats)
            
        except Exception as e:
            print(f"\nERRO ao testar modelo {model_name}: {e}")
            import traceback
            traceback.print_exc()
            self.results.append({
                'model_name': model_name,
                'error': str(e),
                'elapsed_time': time.time() - start_time
            })
    
    def generate_comparative_report(self):
        """Gera relatorio comparativo"""
        print("\n" + "#"*70)
        print("# RELATORIO COMPARATIVO DE MODELOS DE EMBEDDING")
        print("#"*70)
        
        if not self.results:
            print("\nNenhum resultado disponivel")
            return
        
        # Cria DataFrame para analise
        df = pd.DataFrame(self.results)
        
        print("\n" + "="*70)
        print("RESUMO DOS RESULTADOS")
        print("="*70)
        
        for idx, row in df.iterrows():
            print(f"\n{idx+1}. {row['model_name']}")
            if 'error' in row and pd.notna(row.get('error')):
                status = row.get('status', 'error')
                print(f"   ❌ STATUS: {status.upper()}")
                print(f"   Motivo: {row['error']}")
                print(f"   Tempo: {row['elapsed_time']:.1f}s")
                continue

            # Verifica se tem dados válidos
            if pd.isna(row.get('score')):
                print(f"   ⚠️  Dados incompletos")
                continue

            print(f"   ✓ Score Geral: {row['score']:.1f}/100")
            print(f"   Acuracia Top-1: {row['accuracy_top1']:.1f}%")
            print(f"   Acuracia Top-5: {row['accuracy_top5']:.1f}%")
            print(f"   Distancia Media: {row['mean_distance']:.4f}")
            print(f"   Tempo: {row['elapsed_time']:.1f}s")
        
        # Ranking por score
        print("\n" + "="*70)
        print("RANKING POR SCORE GERAL")
        print("="*70)
        
        df_valid = df[~df['model_name'].isin(df[df.get('error', '').notna()]['model_name'])]
        if not df_valid.empty:
            df_sorted = df_valid.sort_values('score', ascending=False)
            
            for idx, row in df_sorted.iterrows():
                print(f"\n{list(df_sorted.index).index(idx)+1}. {row['model_name']}")
                print(f"   Score: {row['score']:.1f}/100")
        
        # Analise de metricas individuais
        print("\n" + "="*70)
        print("MELHOR POR METRICA")
        print("="*70)
        
        if not df_valid.empty:
            best_accuracy = df_valid.loc[df_valid['accuracy_top1'].idxmax()]
            best_distance = df_valid.loc[df_valid['mean_distance'].idxmin()]
            best_speed = df_valid.loc[df_valid['elapsed_time'].idxmin()]
            
            print(f"\nMelhor Acuracia: {best_accuracy['model_name']}")
            print(f"  Top-1: {best_accuracy['accuracy_top1']:.1f}%")
            
            print(f"\nMelhor Distancia: {best_distance['model_name']}")
            print(f"  Media: {best_distance['mean_distance']:.4f}")
            
            print(f"\nMais Rapido: {best_speed['model_name']}")
            print(f"  Tempo: {best_speed['elapsed_time']:.1f}s")
        
        # Recomendacao final
        print("\n" + "="*70)
        print("RECOMENDACAO FINAL")
        print("="*70)
        
        if not df_valid.empty:
            best_model = df_sorted.iloc[0]
            
            print(f"\nModelo Recomendado: {best_model['model_name']}")
            print(f"\nJustificativa:")
            print(f"  - Score Geral: {best_model['score']:.1f}/100 (melhor entre todos)")
            print(f"  - Acuracia Top-1: {best_model['accuracy_top1']:.1f}%")
            print(f"  - Acuracia Top-5: {best_model['accuracy_top5']:.1f}%")
            print(f"  - Distancia Media: {best_model['mean_distance']:.4f}")
            print(f"  - Tempo de Indexacao: {best_model['elapsed_time']:.1f}s")
            
            # Confianca na recomendacao
            if len(df_sorted) > 1:
                second_best = df_sorted.iloc[1]
                score_diff = best_model['score'] - second_best['score']
                
                print(f"\nConfianca:")
                if score_diff > 10:
                    print(f"  ALTA - Diferenca de {score_diff:.1f} pontos para o segundo colocado")
                elif score_diff > 5:
                    print(f"  MEDIA - Diferenca de {score_diff:.1f} pontos para o segundo colocado")
                else:
                    print(f"  BAIXA - Diferenca de apenas {score_diff:.1f} pontos")
                    print(f"  Considere testar ambos: {best_model['model_name']} e {second_best['model_name']}")
        
        # Salva resultados em JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"benchmark_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nResultados salvos em: {output_file}")
        
        print("\n" + "#"*70)
        print("# FIM DO RELATORIO")
        print("#"*70)

        # Salva configuração ideal
        self.save_best_config(df_valid, df_sorted)

    def save_best_config(self, df_valid, df_sorted):
        """Salva configuração do melhor modelo para uso em produção"""
        if df_sorted.empty:
            print("\n⚠️  Nenhum modelo válido para salvar configuração")
            return

        best_model = df_sorted.iloc[0]

        config = {
            "model": {
                "name": best_model['model_name'],
                "score": float(best_model['score']),
                "accuracy_top1": float(best_model['accuracy_top1']),
                "accuracy_top5": float(best_model['accuracy_top5']),
                "mean_distance": float(best_model['mean_distance']),
                "elapsed_time": float(best_model['elapsed_time']),
                "timestamp": best_model['timestamp']
            },
            "settings": {
                "use_cache": True,
                "use_reranking": best_model['accuracy_top1'] < 75,  # Ativa reranking se Top-1 < 75%
                "batch_size": 32,
                "top_k_initial": 15,  # Para reranking
                "top_k_final": 5
            },
            "performance": {
                "quality_score": float(best_model['score']),
                "speed_score": 100 - min(100, (best_model['elapsed_time'] / 3600) * 100),
                "recommended_for_production": best_model['score'] >= 80
            },
            "alternatives": []
        }

        # Adiciona alternativas (top 3)
        for idx in range(1, min(3, len(df_sorted))):
            alt = df_sorted.iloc[idx]
            config["alternatives"].append({
                "name": alt['model_name'],
                "score": float(alt['score']),
                "reason": self._get_alternative_reason(best_model, alt)
            })

        # Salva em arquivo
        config_file = "best_model_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print("CONFIGURAÇÃO IDEAL SALVA")
        print(f"{'='*70}")
        print(f"Arquivo: {config_file}")
        print(f"Modelo recomendado: {config['model']['name']}")
        print(f"Score: {config['model']['score']:.1f}/100")
        print(f"Reranking recomendado: {'SIM' if config['settings']['use_reranking'] else 'NÃO'}")
        print(f"Pronto para produção: {'SIM ✓' if config['performance']['recommended_for_production'] else 'NÃO (score < 80)'}")

        # Cria arquivo Python para import direto
        self._create_config_module(config)

    def _get_alternative_reason(self, best, alt):
        """Gera razão para considerar modelo alternativo"""
        if alt['elapsed_time'] < best['elapsed_time'] * 0.7:
            return f"Mais rápido ({alt['elapsed_time']/60:.1f} min vs {best['elapsed_time']/60:.1f} min)"
        elif alt['accuracy_top1'] > best['accuracy_top1']:
            return f"Melhor Top-1 ({alt['accuracy_top1']:.1f}% vs {best['accuracy_top1']:.1f}%)"
        else:
            return f"Alternativa viável (score {alt['score']:.1f})"

    def _create_config_module(self, config):
        """Cria módulo Python com configuração para import"""
        module_content = f'''# best_model_config.py
# Configuração automática gerada pelo benchmark
# Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Modelo recomendado
BEST_MODEL_NAME = "{config['model']['name']}"
BEST_MODEL_SCORE = {config['model']['score']}

# Configurações recomendadas
USE_CACHE = {config['settings']['use_cache']}
USE_RERANKING = {config['settings']['use_reranking']}
BATCH_SIZE = {config['settings']['batch_size']}
TOP_K_INITIAL = {config['settings']['top_k_initial']}
TOP_K_FINAL = {config['settings']['top_k_final']}

# Métricas de performance
ACCURACY_TOP1 = {config['model']['accuracy_top1']}
ACCURACY_TOP5 = {config['model']['accuracy_top5']}
MEAN_DISTANCE = {config['model']['mean_distance']}
INDEXING_TIME_SECONDS = {config['model']['elapsed_time']}

# Status de produção
RECOMMENDED_FOR_PRODUCTION = {config['performance']['recommended_for_production']}

# Função helper para carregar modelo
def load_best_model():
    """Carrega o melhor modelo do benchmark"""
    from sentence_transformers import SentenceTransformer
    print(f"Carregando modelo recomendado: {{BEST_MODEL_NAME}}")
    print(f"Score do benchmark: {{BEST_MODEL_SCORE:.1f}}/100")
    print(f"Acurácia Top-5: {{ACCURACY_TOP5:.1f}}%")
    return SentenceTransformer(BEST_MODEL_NAME)

# Alternativas (caso o modelo principal não esteja disponível)
ALTERNATIVE_MODELS = {config['alternatives']}

if __name__ == "__main__":
    print("="*60)
    print("CONFIGURAÇÃO DO MELHOR MODELO")
    print("="*60)
    print(f"Modelo: {{BEST_MODEL_NAME}}")
    print(f"Score: {{BEST_MODEL_SCORE:.1f}}/100")
    print(f"Top-1: {{ACCURACY_TOP1:.1f}}%")
    print(f"Top-5: {{ACCURACY_TOP5:.1f}}%")
    print(f"Reranking: {{'Recomendado' if USE_RERANKING else 'Não necessário'}}")
    print(f"Produção: {{'Pronto ✓' if RECOMMENDED_FOR_PRODUCTION else 'Requer melhorias'}}")
    print("="*60)
'''

        with open("best_model_config.py", 'w', encoding='utf-8') as f:
            f.write(module_content)

        print(f"✓ Módulo Python criado: best_model_config.py")
        print(f"  Use: from best_model_config import load_best_model")
    
    def run_benchmark(self):
        """Executa benchmark completo"""
        print("\n" + "#"*70)
        print("# BENCHMARK DE MODELOS DE EMBEDDING")
        print(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)
        
        # Carrega dados uma vez
        self.load_data()
        
        # Testa cada modelo
        for model_name in MODELS_TO_TEST:
            self.test_model(model_name)
        
        # Gera relatorio comparativo
        self.generate_comparative_report()


if __name__ == "__main__":
    benchmark = EmbeddingBenchmark()
    benchmark.run_benchmark()