# 🎯 PLANO DE AÇÃO - MELHORIAS RAG NCM

**Status Atual:** Benchmark inicial completo
**Score Atual:** 75.6/100
**Meta:** 85-90/100

---

## 📋 TAREFAS PRIORITÁRIAS

### ✅ CONCLUÍDO
- [x] Executar benchmark inicial com 5 modelos
- [x] Identificar melhor modelo (intfloat/multilingual-e5-base)
- [x] Documentar resultados e análise
- [x] Criar ground truth expandido (90+ casos)
- [x] Implementar sistema de cache de embeddings

---

## 🔥 FASE 1: MELHORIAS CRÍTICAS (2-3 dias)

### Tarefa 1.1: Integrar Ground Truth Expandido
**Prioridade:** ALTA
**Tempo estimado:** 30 minutos

```bash
# 1. Modificar benchmark_embeddings.py para usar novo ground truth
# Linha 242-251: Substituir test_cases
```

**Alteração necessária:**
```python
# benchmark_embeddings.py
from ground_truth_cases import TEST_CASES

def run_diagnostics(self, collection, embedder, model_name):
    # ... código existente ...

    # SUBSTITUIR:
    # test_cases = [
    #     ("cafe torrado em graos", "0901"),
    #     ...
    # ]

    # POR:
    test_cases = TEST_CASES

    # ... resto do código ...
```

**Validação:**
```bash
python ground_truth_cases.py
# Deve mostrar: Total de casos de teste: 90+
```

---

### Tarefa 1.2: Integrar Cache de Embeddings
**Prioridade:** ALTA
**Tempo estimado:** 1 hora

**Alteração em `benchmark_embeddings.py`:**

```python
# No início do arquivo
from embedding_cache import EmbeddingCache, encode_with_cache

class EmbeddingBenchmark:
    def __init__(self):
        self.results = []
        self.ncm_data = None
        self.atributos_data = None
        self.hierarchy = None
        self.atributos_dict = None
        self.cache = EmbeddingCache()  # ADICIONAR

    def encode_batch(self, embedder, texts, batch_size=32):
        """Vetoriza lista de textos em lotes com cache"""
        # SUBSTITUIR IMPLEMENTAÇÃO POR:
        return encode_with_cache(embedder, texts, self.cache, batch_size)
```

**Teste:**
```bash
# Primeiro run - deve ser lento (cache miss)
python benchmark_embeddings.py

# Segundo run - deve ser muito mais rápido (cache hit)
python benchmark_embeddings.py
```

**Resultado esperado:**
- 1ª execução: ~83 minutos
- 2ª execução: ~5-10 minutos (redução de 80-90%)

---

### Tarefa 1.3: Melhorar Normalização de Textos
**Prioridade:** MÉDIA-ALTA
**Tempo estimado:** 1 hora

**Alteração em `data_loader.py`:**

```python
import unicodedata
import re

def normalize_text_advanced(text):
    """
    Normalização avançada de texto para melhorar busca semântica.

    Aplica:
    - Remoção de acentos
    - Lowercase
    - Limpeza de pontuação
    - Remoção de stopwords
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Remove acentos (mantém semântica)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')

    # 2. Lowercase
    text = text.lower()

    # 3. Remove pontuação, mantém espaços e hífens
    text = re.sub(r'[^\w\s-]', ' ', text)

    # 4. Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text)

    # 5. Remove stopwords muito comuns (mas não todas)
    # Mantém palavras-chave importantes
    minimal_stopwords = {'de', 'da', 'do', 'em', 'na', 'no', 'para', 'com'}
    words = text.split()

    # Só remove stopwords se texto tem >3 palavras
    if len(words) > 3:
        words = [w for w in words if w not in minimal_stopwords]

    return ' '.join(words).strip()


# Modificar função existente
def create_enriched_ncm_text(row, hierarchy, atributos_dict):
    """Cria texto enriquecido do NCM com normalização"""
    # ... código existente que monta text_parts ...

    # ANTES de retornar, aplicar normalização:
    final_text = ' | '.join([p for p in text_parts if p])

    # ADICIONAR:
    return normalize_text_advanced(final_text)
```

**Teste:**
```python
# Testar normalização
from data_loader import normalize_text_advanced

tests = [
    "Café torrado em grãos",
    "Óleo de soja refinado",
    "TELEFONE CELULAR - SMARTPHONE!!!",
]

for text in tests:
    print(f"{text:40} -> {normalize_text_advanced(text)}")
```

**Resultado esperado:**
```
Café torrado em grãos                    -> cafe torrado graos
Óleo de soja refinado                    -> oleo soja refinado
TELEFONE CELULAR - SMARTPHONE!!!         -> telefone celular smartphone
```

---

### Tarefa 1.4: Executar Novo Benchmark Completo
**Prioridade:** ALTA
**Tempo estimado:** 2-3 horas (com cache)

**Comando:**
```bash
# Limpar cache anterior (opcional)
rm -rf cache/embeddings/*

# Executar benchmark com melhorias
python benchmark_embeddings.py
```

**Métricas esperadas com melhorias:**
- Score Geral: **78-82/100** (vs 75.6 atual)
- Acurácia Top-5: **90-92%** (vs 87.5% atual)
- Acurácia Top-1: **68-72%** (vs 62.5% atual)
- Tempo: ~60-80 min (primeira vez) / ~5-10 min (com cache)

---

## 🚀 FASE 2: OTIMIZAÇÕES AVANÇADAS (2-3 dias)

### Tarefa 2.1: Implementar Re-ranking
**Prioridade:** ALTA
**Tempo estimado:** 3-4 horas

**Criar novo arquivo `reranker.py`:**

```python
from sentence_transformers import CrossEncoder
from typing import List, Dict

class Reranker:
    """
    Re-ranking usando CrossEncoder para melhorar Top-1.

    CrossEncoder computa score de relevância direto entre query e documento,
    geralmente mais preciso que bi-encoders (embeddings).
    """

    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Carrega modelo de re-ranking.

        Args:
            model_name: Modelo CrossEncoder (default: ms-marco-MiniLM)
        """
        print(f"Carregando reranker: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Re-rankeia resultados de busca.

        Args:
            query: Consulta original
            results: Lista de resultados com 'document' e 'metadata'
            top_k: Número de resultados finais

        Returns:
            Lista re-rankeada dos top_k melhores
        """
        if not results:
            return []

        # Prepara pares (query, documento)
        pairs = [[query, res['document']] for res in results]

        # Calcula scores de relevância
        scores = self.model.predict(pairs)

        # Adiciona scores aos resultados
        for i, res in enumerate(results):
            res['rerank_score'] = float(scores[i])

        # Ordena por score decrescente
        reranked = sorted(results, key=lambda x: x['rerank_score'], reverse=True)

        return reranked[:top_k]
```

**Modificar `rag_ncm.py` (se existir) ou criar versão com reranking:**

```python
from reranker import Reranker

class RAGSystemWithReranking:
    def __init__(self, collection, embedder):
        self.collection = collection
        self.embedder = embedder
        self.reranker = Reranker()

    def query(self, query_text, top_k=5, use_reranking=True):
        """
        Busca com re-ranking opcional.

        Args:
            query_text: Texto da consulta
            top_k: Número de resultados finais
            use_reranking: Se True, aplica re-ranking

        Returns:
            Lista de resultados re-rankeados
        """
        # 1. Busca inicial (retorna 3x mais resultados)
        initial_k = top_k * 3 if use_reranking else top_k

        query_emb = self.embedder.encode(query_text).tolist()
        raw_results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=initial_k,
            where={"tipo": "ncm"}
        )

        if not raw_results or not raw_results['documents']:
            return []

        # 2. Formata resultados
        results = [
            {
                'document': raw_results['documents'][0][i],
                'metadata': raw_results['metadatas'][0][i],
                'distance': raw_results['distances'][0][i],
            }
            for i in range(len(raw_results['documents'][0]))
        ]

        # 3. Re-ranking (se habilitado)
        if use_reranking:
            results = self.reranker.rerank(query_text, results, top_k)

        return results
```

**Teste de re-ranking:**
```python
# test_reranking.py
from reranker import Reranker

reranker = Reranker()

query = "telefone celular smartphone"
documents = [
    "Aparelho telefônico celular tipo smartphone",
    "Cabo USB para carregar celular",
    "Capa protetora para telefone",
    "Telefone fixo residencial",
]

results = [{'document': doc} for doc in documents]
reranked = reranker.rerank(query, results, top_k=3)

for i, res in enumerate(reranked):
    print(f"{i+1}. Score: {res['rerank_score']:.4f} - {res['document']}")
```

**Resultado esperado:**
```
1. Score: 0.8542 - Aparelho telefônico celular tipo smartphone
2. Score: 0.6123 - Capa protetora para telefone
3. Score: 0.4891 - Cabo USB para carregar celular
```

**Impacto estimado:**
- Acurácia Top-1: **+8-12%** (de 62.5% para ~72-75%)
- Acurácia Top-5: +2-3%
- Latência: +100-200ms por consulta (aceitável)

---

### Tarefa 2.2: Testar Novos Modelos
**Prioridade:** MÉDIA
**Tempo estimado:** 4-5 horas

**Modificar `benchmark_embeddings.py`:**

```python
MODELS_TO_TEST = [
    # Baseline atual
    'intfloat/multilingual-e5-base',

    # Modelo maior do mesmo fabricante
    'intfloat/multilingual-e5-large',  # Melhor qualidade

    # Modelos SOTA 2024
    'BAAI/bge-m3',  # Excelente para multilíngue

    # Para comparação de velocidade
    'sentence-transformers/all-MiniLM-L6-v2',  # Rápido
]
```

**Executar:**
```bash
# Com cache ativado, deve ser mais rápido
python benchmark_embeddings.py
```

**Modelos recomendados para teste:**

| Modelo | Dimensão | Velocidade | Qualidade | Multilíngue |
|--------|----------|------------|-----------|-------------|
| multilingual-e5-base | 768 | Média | ⭐⭐⭐⭐ | ✅ |
| multilingual-e5-large | 1024 | Lenta | ⭐⭐⭐⭐⭐ | ✅ |
| bge-m3 | 1024 | Média | ⭐⭐⭐⭐⭐ | ✅ |
| all-MiniLM-L6-v2 | 384 | Rápida | ⭐⭐⭐ | ❌ |

**Resultado esperado:**
- `multilingual-e5-large`: Score **80-85/100** (melhor qualidade)
- `bge-m3`: Score **82-87/100** (SOTA)

---

### Tarefa 2.3: Adicionar Métricas Avançadas
**Prioridade:** BAIXA
**Tempo estimado:** 2 horas

**Modificar `run_diagnostics` em `benchmark_embeddings.py`:**

```python
def run_diagnostics(self, collection, embedder, model_name):
    # ... código existente ...

    # ADICIONAR métricas avançadas
    mrr_score = self.calculate_mrr(collection, embedder, TEST_CASES)
    recall_at_10 = self.calculate_recall_at_k(collection, embedder, TEST_CASES, k=10)

    stats['mrr'] = mrr_score
    stats['recall@10'] = recall_at_10

    print(f"  MRR: {mrr_score:.3f}")
    print(f"  Recall@10: {recall_at_10:.1f}%")

    return stats

def calculate_mrr(self, collection, embedder, test_cases):
    """
    Mean Reciprocal Rank - posição média do primeiro resultado correto.

    MRR = 1/N * sum(1/rank_i)
    onde rank_i é a posição do primeiro resultado correto.
    """
    mrr_sum = 0

    for query, expected_chapter in test_cases:
        emb = embedder.encode(query).tolist()
        results = collection.query(
            query_embeddings=[emb],
            n_results=10,
            where={"tipo": "ncm"}
        )

        if not results or not results['metadatas']:
            continue

        # Encontra posição do primeiro resultado correto
        for i, meta in enumerate(results['metadatas'][0]):
            ncm_code = meta.get('codigo_normalizado', '') or meta.get('codigo', '')
            chapter = ncm_code[:4].replace('.', '')

            if chapter == expected_chapter:
                mrr_sum += 1 / (i + 1)  # Rank começa em 1
                break

    return mrr_sum / len(test_cases) if test_cases else 0

def calculate_recall_at_k(self, collection, embedder, test_cases, k=10):
    """
    Recall@K - % de casos em que o resultado correto aparece nos top-K.
    """
    hits = 0

    for query, expected_chapter in test_cases:
        emb = embedder.encode(query).tolist()
        results = collection.query(
            query_embeddings=[emb],
            n_results=k,
            where={"tipo": "ncm"}
        )

        if not results or not results['metadatas']:
            continue

        for meta in results['metadatas'][0]:
            ncm_code = meta.get('codigo_normalizado', '') or meta.get('codigo', '')
            chapter = ncm_code[:4].replace('.', '')

            if chapter == expected_chapter:
                hits += 1
                break

    return 100 * hits / len(test_cases) if test_cases else 0
```

---

## 📊 FASE 3: VALIDAÇÃO E DEPLOY (1 dia)

### Tarefa 3.1: Validação Final
**Checklist:**
- [ ] Score geral > 85/100
- [ ] Acurácia Top-5 > 90%
- [ ] Acurácia Top-1 > 70%
- [ ] MRR > 0.75
- [ ] Tempo de indexação < 60 min
- [ ] Cache funcionando (>80% hit rate em re-runs)
- [ ] Re-ranking melhorando Top-1 em >5%

### Tarefa 3.2: Documentação
- [ ] Atualizar README.md com resultados finais
- [ ] Documentar como usar cache
- [ ] Documentar como usar re-ranking
- [ ] Adicionar exemplos de uso

### Tarefa 3.3: Deploy
- [ ] Configurar modelo final em produção
- [ ] Configurar cache persistente
- [ ] Ativar re-ranking por default
- [ ] Monitorar performance real

---

## 📈 ROADMAP DE SCORES ESPERADOS

| Fase | Melhorias | Score Estimado | Top-5 | Top-1 |
|------|-----------|----------------|-------|-------|
| Inicial | Benchmark base | 75.6 | 87.5% | 62.5% |
| Fase 1.1 | + Ground truth | 76-78 | 88-90% | 64-66% |
| Fase 1.2 | + Cache | 76-78 | 88-90% | 64-66% |
| Fase 1.3 | + Normalização | 78-80 | 90-91% | 66-68% |
| Fase 2.1 | + Re-ranking | 82-85 | 91-93% | 74-77% |
| Fase 2.2 | + Modelo melhor | **87-90** | **93-95%** | **78-82%** |

**Meta Final:** Score 87-90/100 com 95% Top-5 e 80% Top-1

---

## 🚨 DECISÕES PENDENTES

### 1. Qual modelo usar em produção?
**Opções:**
- **A) intfloat/multilingual-e5-base** (atual)
  - ✅ Bom equilíbrio velocidade/qualidade
  - ✅ Score 75.6 já é bom
  - ❌ Deixa margem para melhoria

- **B) intfloat/multilingual-e5-large**
  - ✅ Melhor qualidade (~+5-8 pontos)
  - ❌ 30% mais lento
  - ❌ Precisa mais memória

- **C) BAAI/bge-m3**
  - ✅ SOTA 2024 multilíngue
  - ✅ Excelente qualidade (~+8-12 pontos)
  - ⚠️ Menos testado

**Recomendação:** Testar **B** e **C** na Fase 2.2, depois decidir.

### 2. Ativar re-ranking por padrão?
**Análise:**
- ✅ Melhora Top-1 significativamente (+8-12%)
- ✅ Latência adicional aceitável (~150ms)
- ❌ Adiciona complexidade

**Recomendação:** SIM, ativar por padrão com opção de desabilitar.

### 3. Cobertura de atributos baixa (52%)?
**Problema:** Apenas metade dos NCMs têm atributos.

**Investigar:**
- Faltam atributos na base de dados?
- NCMs sem atributos são esperados?
- Precisa enriquecer dados?

**Ação:** Investigar na Fase 2.

---

## ✅ CRITÉRIOS DE SUCESSO

### Mínimo Aceitável (MVP)
- [x] Score ≥ 75/100 ✅ (75.6 atual)
- [ ] Top-5 ≥ 90%
- [ ] Top-1 ≥ 70%

### Ideal (Produção)
- [ ] Score ≥ 85/100
- [ ] Top-5 ≥ 92%
- [ ] Top-1 ≥ 75%
- [ ] Cache funcionando
- [ ] Re-ranking ativo

### Excelente (Best-in-class)
- [ ] Score ≥ 90/100
- [ ] Top-5 ≥ 95%
- [ ] Top-1 ≥ 80%
- [ ] Tempo indexação < 30 min
- [ ] Métricas avançadas (MRR > 0.80)

---

## 📞 PRÓXIMOS PASSOS IMEDIATOS

**AGORA (Hoje):**
1. ✅ Revisar análise do benchmark
2. ✅ Criar ground truth expandido
3. ✅ Implementar cache
4. ⏳ Integrar melhorias no código

**AMANHÃ:**
1. Testar benchmark com melhorias
2. Analisar novos resultados
3. Implementar re-ranking

**ESTA SEMANA:**
1. Testar novos modelos (e5-large, bge-m3)
2. Validar melhorias
3. Decidir configuração final

---

**Última atualização:** 2025-10-31
**Status:** Fase 1 em andamento
