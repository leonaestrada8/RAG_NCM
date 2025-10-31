# 📊 ANÁLISE DETALHADA DO BENCHMARK DE EMBEDDINGS

**Data:** 2025-10-30
**Status:** PARCIALMENTE SATISFATÓRIO - Requer melhorias

---

## 🎯 RESUMO EXECUTIVO

### Resultado Final
- **Modelo Vencedor:** `intfloat/multilingual-e5-base`
- **Score Geral:** 75.6/100
- **Acurácia Top-5:** 87.5% ✅ (muito bom)
- **Acurácia Top-1:** 62.5% ⚠️ (pode melhorar)
- **Recomendação:** Implementar melhorias + testar novos modelos

---

## 📈 RESULTADOS DETALHADOS

### Ranking dos Modelos

| Posição | Modelo | Score | Top-1 | Top-5 | Tempo |
|---------|--------|-------|-------|-------|-------|
| 🥇 1º | intfloat/multilingual-e5-base | **75.6** | 62.5% | **87.5%** | 4971s |
| 🥈 2º | paraphrase-multilingual-mpnet-base-v2 | 54.0 | 62.5% | 75.0% | 7619s |
| 🥉 3º | all-MiniLM-L6-v2 | 50.1 | 37.5% | 62.5% | 1991s |
| 4º | paraphrase-multilingual-MiniLM-L12-v2 | 36.5 | 37.5% | 50.0% | 2445s |
| ❌ | paraphrase-multilingual-MiniLM-L6-v2 | ERRO | - | - | - |

### Análise por Métrica

#### 1. Acurácia (Peso: 70% do score)
- **Melhor Top-5:** intfloat/multilingual-e5-base (87.5%) ✅
- **Melhor Top-1:** Empate em 62.5% (pode melhorar)
- **Pior:** paraphrase-multilingual-MiniLM-L12-v2 (50.0%)

#### 2. Distância Média (Peso: 20% do score)
- **Melhor:** intfloat/multilingual-e5-base (0.339) ✅
- Menor distância = embeddings mais separados = melhor discriminação

#### 3. Velocidade (Peso: 10% do score)
- **Mais Rápido:** all-MiniLM-L6-v2 (33 min)
- **Mais Lento:** paraphrase-multilingual-mpnet-base-v2 (127 min)
- **Vencedor:** 83 min (aceitável para indexação offline)

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### 1. Ground Truth Insuficiente
**Problema:** Apenas 8 casos de teste
```python
test_cases = [
    ("cafe torrado em graos", "0901"),
    ("soja em graos", "1201"),
    # ... apenas 8 casos
]
```
**Impacto:** Baixa confiança estatística nos resultados
**Solução:** Expandir para 30-50 casos cobrindo diferentes categorias

### 2. Cobertura Baixa de Atributos
**Problema:** Apenas 52.4% dos NCMs têm atributos (7942/15146)
**Impacto:** Sistema não cobre metade do catálogo
**Solução:** Investigar NCMs sem atributos + melhorar dados

### 3. Tempo de Processamento Alto
**Problema:** 83 minutos para indexar
**Impacto:** Re-indexação completa é custosa
**Solução:** Implementar cache de embeddings + indexação incremental

### 4. Modelo Faltante
**Problema:** Erro 401 ao baixar `paraphrase-multilingual-MiniLM-L6-v2`
**Causa:** Autenticação HuggingFace necessária
**Solução:** Remover da lista ou configurar token HF

---

## 🚀 MELHORIAS RECOMENDADAS

### PRIORIDADE ALTA (Implementar Agora)

#### 1. Expandir Ground Truth
**Arquivo:** `benchmark_embeddings.py:242-251`

Criar arquivo separado com casos de teste mais robustos:

```python
# ground_truth_cases.py
TEST_CASES = [
    # Alimentos (Capítulos 01-24)
    ("cafe torrado em graos", "0901"),
    ("cafe solúvel instantâneo", "2101"),
    ("soja em graos para plantio", "1201"),
    ("óleo de soja refinado", "1507"),
    ("carne bovina congelada", "0202"),
    ("carne de frango fresca", "0207"),
    ("leite em pó integral", "0402"),
    ("queijo mussarela", "0406"),
    ("arroz em graos descascado", "1006"),
    ("farinha de trigo", "1101"),
    ("açucar cristal", "1701"),
    ("chocolate em barra", "1806"),

    # Eletrônicos (Capítulo 85)
    ("telefone celular smartphone", "8517"),
    ("carregador usb para celular", "8504"),
    ("monitor LCD computador", "8528"),
    ("cabo HDMI", "8544"),

    # Informática (Capítulo 84)
    ("notebook computador portátil", "8471"),
    ("impressora laser", "8443"),
    ("teclado sem fio", "8471"),
    ("mouse óptico USB", "8471"),

    # Veículos (Capítulos 87-89)
    ("automóvel sedan gasolina", "8703"),
    ("pneu radial aro 15", "4011"),
    ("bateria automotiva 60ah", "8507"),

    # Vestuário (Capítulos 61-62)
    ("camiseta algodão masculina", "6109"),
    ("calça jeans feminina", "6203"),
    ("sapato couro social", "6403"),

    # Medicamentos (Capítulo 30)
    ("antibiótico amoxicilina", "3004"),
    ("analgésico paracetamol", "3004"),

    # Cosméticos (Capítulo 33)
    ("shampoo para cabelos", "3305"),
    ("perfume fragrância", "3303"),

    # Materiais de Construção
    ("cimento portland", "2523"),
    ("tijolo cerâmico", "6904"),
    ("tinta latex acrílica", "3209"),
]
```

**Modificação no benchmark:**
```python
# benchmark_embeddings.py
from ground_truth_cases import TEST_CASES

def run_diagnostics(self, collection, embedder, model_name):
    # ... código existente ...

    hits = 0
    top1_hits = 0

    for query, expected_chapter in TEST_CASES:
        # ... teste ...
```

#### 2. Implementar Cache de Embeddings
**Novo arquivo:** `embedding_cache.py`

```python
import pickle
import hashlib
from pathlib import Path

class EmbeddingCache:
    def __init__(self, cache_dir="cache/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_hash(self, text, model_name):
        key = f"{model_name}:{text}"
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, text, model_name):
        hash_key = self.get_hash(text, model_name)
        cache_file = self.cache_dir / f"{hash_key}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, text, model_name, embedding):
        hash_key = self.get_hash(text, model_name)
        cache_file = self.cache_dir / f"{hash_key}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)
```

#### 3. Adicionar Re-ranking
**Novo arquivo:** `reranker.py`

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        # Modelo menor e rápido para re-ranking
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank(self, query, documents, top_k=5):
        """Re-rankeia documentos usando cross-encoder"""
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)

        # Ordena por score
        ranked_indices = scores.argsort()[::-1][:top_k]
        return ranked_indices, scores[ranked_indices]
```

**Integração no RAG:**
```python
# rag_ncm.py
from reranker import Reranker

class RAGSystem:
    def __init__(self):
        # ... código existente ...
        self.reranker = Reranker()

    def query(self, query_text, top_k=5):
        # 1. Busca inicial (retorna mais resultados)
        initial_results = self.collection.query(
            query_embeddings=[self.embed(query_text)],
            n_results=top_k * 3  # 3x mais resultados
        )

        # 2. Re-ranking
        docs = initial_results['documents'][0]
        indices, scores = self.reranker.rerank(query_text, docs, top_k)

        # 3. Retorna top-k re-rankeados
        return [
            {
                'document': docs[i],
                'metadata': initial_results['metadatas'][0][i],
                'score': float(scores[j])
            }
            for j, i in enumerate(indices)
        ]
```

#### 4. Melhorar Normalização de Textos
**Modificação:** `data_loader.py`

```python
import unicodedata
import re

def normalize_text(text):
    """Normalização avançada de texto"""
    if not text:
        return ""

    # 1. Remove acentos mantendo semântica
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')

    # 2. Lowercase
    text = text.lower()

    # 3. Remove pontuação extra
    text = re.sub(r'[^\w\s-]', ' ', text)

    # 4. Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text)

    # 5. Remove stopwords comuns mas mantém palavras-chave
    stopwords = {'de', 'da', 'do', 'dos', 'das', 'em', 'na', 'no', 'para'}
    words = text.split()
    words = [w for w in words if w not in stopwords or len(words) <= 3]

    return ' '.join(words).strip()

def create_enriched_ncm_text(row, hierarchy, atributos_dict):
    """Versão melhorada com normalização"""
    # ... código existente ...

    # Adiciona normalização
    text_parts = [p for p in text_parts if p]
    final_text = ' | '.join(text_parts)

    return normalize_text(final_text)
```

---

### PRIORIDADE MÉDIA (Próxima Iteração)

#### 5. Testar Novos Modelos SOTA

Adicionar ao `benchmark_embeddings.py:30-36`:

```python
MODELS_TO_TEST = [
    # Modelo atual (baseline)
    'intfloat/multilingual-e5-base',

    # Novos modelos para testar
    'intfloat/multilingual-e5-large',  # Versão maior do vencedor
    'BAAI/bge-m3',  # SOTA 2024 multilíngue
    'sentence-transformers/LaBSE',  # Focado em multilíngue

    # Para comparação
    'sentence-transformers/all-MiniLM-L6-v2',  # Modelo rápido
]
```

#### 6. Adicionar Métricas Avançadas

```python
def run_advanced_metrics(self, collection, embedder, test_cases):
    """Métricas adicionais de qualidade"""
    from sklearn.metrics import ndcg_score

    metrics = {
        'mrr': 0,  # Mean Reciprocal Rank
        'ndcg@10': 0,  # Normalized Discounted Cumulative Gain
        'recall@10': 0,
        'precision@5': 0
    }

    for query, expected in test_cases:
        results = self.search(query, k=10)

        # MRR: 1/posição do primeiro resultado correto
        for i, res in enumerate(results):
            if matches_expected(res, expected):
                metrics['mrr'] += 1 / (i + 1)
                break

        # Recall@10: % de resultados corretos nos top-10
        relevant = [r for r in results if matches_expected(r, expected)]
        metrics['recall@10'] += len(relevant) / min(10, len(all_relevant))

    # Média
    n = len(test_cases)
    return {k: v/n for k, v in metrics.items()}
```

#### 7. Implementar Indexação Incremental

```python
class IncrementalIndexer:
    """Permite adicionar documentos sem re-indexar tudo"""

    def __init__(self, collection, embedder, cache):
        self.collection = collection
        self.embedder = embedder
        self.cache = cache

    def add_documents(self, new_docs):
        """Adiciona apenas novos documentos"""
        # Verifica quais já existem
        existing_ids = set(self.collection.get()['ids'])

        docs_to_add = [
            doc for doc in new_docs
            if doc['id'] not in existing_ids
        ]

        if not docs_to_add:
            return 0

        # Gera embeddings com cache
        embeddings = []
        for doc in docs_to_add:
            cached = self.cache.get(doc['text'], self.embedder.model_name)
            if cached:
                embeddings.append(cached)
            else:
                emb = self.embedder.encode(doc['text'])
                self.cache.set(doc['text'], self.embedder.model_name, emb)
                embeddings.append(emb)

        # Adiciona à coleção
        self.collection.add(
            ids=[d['id'] for d in docs_to_add],
            documents=[d['text'] for d in docs_to_add],
            embeddings=embeddings,
            metadatas=[d['metadata'] for d in docs_to_add]
        )

        return len(docs_to_add)
```

---

### PRIORIDADE BAIXA (Otimizações)

#### 8. Paralelizar Processamento

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def encode_batch_parallel(self, embedder, texts, batch_size=32, workers=4):
    """Vetorização paralela"""
    batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]

    embeddings = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(embedder.encode, batch) for batch in batches]

        for future in tqdm(as_completed(futures), total=len(batches)):
            embeddings.extend(future.result())

    return embeddings
```

#### 9. Usar GPU se Disponível

```python
def __init__(self):
    import torch
    self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Usando dispositivo: {self.device}")

def load_model(self, model_name):
    embedder = SentenceTransformer(model_name, device=self.device)
    return embedder
```

---

## 📊 PROJEÇÃO DE MELHORIAS

### Impacto Estimado das Melhorias

| Melhoria | Score Atual | Score Projetado | Ganho |
|----------|-------------|-----------------|-------|
| Ground Truth expandido | 75.6 | 76-78 | +2 |
| Re-ranking | 76-78 | 82-85 | +6 |
| Normalização melhorada | 82-85 | 84-87 | +2 |
| Novo modelo (e5-large) | 84-87 | 87-90 | +3 |
| **TOTAL PROJETADO** | **75.6** | **87-90** | **+12-15** |

### Meta de Qualidade

**Score Alvo:** 85-90/100
- Acurácia Top-5: >90%
- Acurácia Top-1: >75%
- Tempo: <60 min

---

## 🎯 PLANO DE AÇÃO RECOMENDADO

### Fase 1: Melhorias Críticas (1-2 dias)
- [ ] Expandir ground truth para 30+ casos
- [ ] Implementar cache de embeddings
- [ ] Melhorar normalização de textos
- [ ] Executar novo benchmark

### Fase 2: Otimizações (2-3 dias)
- [ ] Implementar re-ranking
- [ ] Testar intfloat/multilingual-e5-large
- [ ] Testar BAAI/bge-m3
- [ ] Adicionar métricas avançadas (MRR, NDCG)

### Fase 3: Produção (1 dia)
- [ ] Implementar indexação incremental
- [ ] Configurar cache persistente
- [ ] Documentar modelo final
- [ ] Deploy em produção

---

## ✅ CONCLUSÃO

### Veredicto Final
**O benchmark foi ÚTIL e REVELADOR**, mas:
- ✅ Identificou claramente o melhor modelo
- ✅ 87.5% Top-5 é bom para MVP
- ⚠️ Precisa de melhorias para produção robusta
- ⚠️ Ground truth pequeno limita confiança

### Recomendação
**SIM, executar nova rodada** com:
1. Melhorias implementadas (re-ranking, normalização)
2. Ground truth expandido (30+ casos)
3. Novos modelos (e5-large, bge-m3)
4. Métricas avançadas (MRR, NDCG)

### Modelo para Produção Imediata
Se precisar decidir AGORA sem nova rodada:
- **Use:** `intfloat/multilingual-e5-base`
- **Com:** Re-ranking implementado
- **Resultado esperado:** 80-85% eficácia real

---

**Preparado por:** Claude Code
**Data:** 2025-10-31
**Versão:** 1.0
