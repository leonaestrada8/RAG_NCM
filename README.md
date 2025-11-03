# RAG NCM - Sistema de Classificação NCM com RAG

Sistema de Retrieval-Augmented Generation (RAG) para classificação de códigos NCM (Nomenclatura Comum do Mercosul) usando embeddings semânticos.

## 📁 Estrutura do Projeto

```
RAG_NCM/
├── 📄 Arquivos Essenciais (Raiz)
│   ├── config.py                  # Configurações do sistema
│   ├── data_loader.py             # Carregamento de NCM e atributos
│   ├── database.py                # Gerenciamento ChromaDB
│   ├── embedding_cache.py         # Cache de embeddings
│   ├── embeddings.py              # Interface de embeddings
│   ├── indexer.py                 # Indexação de documentos
│   ├── llm_client.py              # Cliente LLM (Claude/OpenAI)
│   ├── search.py                  # ⭐ Busca por embedding (CORE)
│   ├── main.py                    # Pipeline principal
│   ├── run_chatbot.py             # Executor do chatbot
│   ├── ui.py                      # Interface do usuário
│   ├── system_prompt.txt          # Prompt do sistema
│   ├── .env                       # Variáveis de ambiente
│   └── .gitignore                 # Controle de versão
│
├── 📊 benchmark/
│   ├── benchmark_embeddings.py    # Benchmark de modelos
│   ├── ground_truth_cases.py      # Casos de teste (88 queries)
│   ├── run_benchmark.py           # Executor de benchmark
│   ├── run_definitive_benchmark.py
│   ├── analyze_benchmark_results.py
│   ├── diagnose.py                # Diagnósticos
│   ├── diagnostics.py
│   ├── test_improvements.py
│   ├── test_simple.py
│   ├── examples.py
│   ├── clear_cache.py
│   └── *.md                       # Documentação de análises
│
└── 💾 DATA/
    ├── SubItemNcm.csv                          # 15.146 códigos NCM
    ├── SubItemNcm_MINI.csv                     # Subset para testes
    ├── ATRIBUTOS_POR_NCM_2025_09_30.json       # 10.560 atributos
    └── ATRIBUTOS_POR_NCM_2025_09_30_MINI.json  # Subset para testes
```

---

## 🚀 Como Usar

### 1. Executar o Chatbot

```bash
python run_chatbot.py
```

### 2. Rodar Benchmark de Modelos

```bash
cd benchmark
python benchmark_embeddings.py
```

### 3. Executar Pipeline Completo

```bash
python main.py
```

---

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# API Keys
PLIN_URL=https://...
CLIENT_ID=seu_client_id
CLIENT_SECRET=seu_client_secret

# Opcional: Desabilitar normalização de texto
DISABLE_NORMALIZATION=0
```

### Arquivos de Configuração

**config.py** - Principais configurações:

```python
# Caminhos de dados
NCM_FILE = "DATA/SubItemNcm.csv"
ATRIBUTOS_FILE = "DATA/ATRIBUTOS_POR_NCM_2025_09_30.json"

# Modelo de embedding (MELHOR conforme benchmark)
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# ChromaDB
DB_PATH = "ncm_atributos_rag"
COLLECTION_NAME = "ncm_atributos"
BATCH_SIZE = 5000
```

---

## 📈 Performance

### Modelo Recomendado

**intfloat/multilingual-e5-base**
- Score: **55.8/100**
- Top-1 Accuracy: 42.0%
- Top-5 Accuracy: 60.2%
- Velocidade: 17.5 queries/s

### Por que Embedding Puro?

✅ **Busca Híbrida NÃO agrega valor** (ver CONCLUSAO_BUSCA_HIBRIDA.md)
- Embedding puro: 55.8/100
- Híbrido (BM25): 52.4-53.6/100 ❌

**Fatores críticos de sucesso:**
1. ✓ Documentos enriquecidos com atributos (+5.6 pontos)
2. ✓ Hierarquia NCM (capítulos → posições → items)
3. ✓ Modelo multilingual-e5-base (768 dim)

---

## 📚 Documentação Importante

### Relatórios e Análises

| Arquivo | Conteúdo |
|---------|----------|
| `RELATORIO_FINAL_BENCHMARK.md` | Benchmark oficial de 5 modelos |
| `CONCLUSAO_BUSCA_HIBRIDA.md` | Análise de busca híbrida vs embedding puro |
| `REORGANIZACAO_ARQUIVOS.md` | Documentação desta reorganização |
| `CHANGELOG_V2.md` | Histórico de mudanças |

### Documentação de Benchmark

Localizada em `benchmark/*.md`:
- `ANALISE_BENCHMARK.md`
- `ANALISE_QUEDA_PERFORMANCE.md`
- `GUIA_DIAGNOSTICO.md`
- `README_BENCHMARK.md`

---

## 🎯 Arquitetura do Sistema

### Pipeline de Busca

```
Query do usuário
    ↓
[1] Embedding da query (multilingual-e5-base, 768 dim)
    ↓
[2] Busca semântica no ChromaDB
    ↓
[3] Retorna Top-5 NCMs mais similares
    ↓
[4] LLM processa contexto + query
    ↓
Resposta final com NCM correto
```

### Enriquecimento de Documentos

Cada NCM é indexado com:

1. **Código normalizado** (8 dígitos com pontos)
2. **Descrição oficial**
3. **Hierarquia completa**:
   - Capítulo (2 dígitos)
   - Posição (4 dígitos)
   - Subitem (6 dígitos)
   - Item (8 dígitos)
4. **Atributos cadastrados** (até 10.560 NCMs com atributos)

**Impacto:** +5.6 pontos de melhoria (50.2 → 55.8)

---

## 🔍 Casos de Teste

O sistema é validado com **88 casos reais** definidos em `benchmark/ground_truth_cases.py`:

- Produtos simples (ex: "caneta esferográfica")
- Produtos técnicos (ex: "cabo HDMI")
- Edge cases (ambiguidades, sinônimos)

---

## 🛠️ Desenvolvimento

### Executar Testes

```bash
cd benchmark
python test_simple.py        # Teste básico
python test_improvements.py  # Teste de melhorias
```

### Limpar Cache

```bash
cd benchmark
python clear_cache.py
```

### Diagnósticos

```bash
cd benchmark
python diagnose.py --all     # Diagnóstico completo
```

---

## 📊 Histórico de Melhorias

| Versão | Score | Mudança |
|--------|-------|---------|
| v1.0 | 50.2/100 | Baseline (BUG: 0 atributos) |
| v2.0 | 55.8/100 | ✓ Atributos corrigidos (10.560) |
| - | 52.4/100 | ❌ Busca híbrida testada (descartada) |

**Próximos passos possíveis:**
- Ajuste fino do modelo de embedding
- Expansão do ground truth
- Otimização do prompt do LLM

---

## ⚙️ Requisitos

### Python Packages

```bash
pip install sentence-transformers
pip install chromadb
pip install pandas
pip install python-dotenv
pip install tqdm
```

### Modelos de Embedding

O sistema baixa automaticamente:
- `intfloat/multilingual-e5-base` (768 dim, 420 MB)

---

## 📝 Notas Importantes

### O que foi removido nesta reorganização?

**Arquivos temporários (experimentos concluídos):**
- `hybrid_search.py` - Busca híbrida não agrega valor
- `test_hybrid_search.py` - Testes finalizados
- `test_atributos_loading.py` - Diagnóstico concluído

**Arquivos fora do escopo:**
- `invoice_*.py` - Processamento de notas fiscais
- `invoice_exemplo.txt`

**Documentos ultrapassados:**
- `GUIA_BUSCA_HIBRIDA.md` (info em CONCLUSAO_BUSCA_HIBRIDA.md)
- `HOTFIX_CACHE_PROGRESS.md` (bug resolvido)
- `PLANO_ACAO.md` (ultrapassado)

**Total removido:** 9 arquivos

---

## 📧 Contato e Contribuições

Este é um projeto interno do SERPRO para classificação automatizada de NCM.

**Decisões de design importantes documentadas em:**
- `CONCLUSAO_BUSCA_HIBRIDA.md` - Por que não usar BM25
- `RELATORIO_FINAL_BENCHMARK.md` - Por que multilingual-e5-base

---

**Versão:** 2.0
**Data:** 2025-11-03
**Modelo:** intfloat/multilingual-e5-base (embedding puro)
**Performance:** 55.8/100 (42% Top-1, 60.2% Top-5)
