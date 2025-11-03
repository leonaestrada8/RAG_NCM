# REORGANIZAÇÃO DE ARQUIVOS - RAG NCM

## 1. ARQUIVOS ESSENCIAIS (Manter na Raiz)

### Arquivos de Configuração
- `.env` - Variáveis de ambiente (API keys, etc)
- `.gitignore` - Controle de versão
- `config.py` - Configurações do sistema

### Arquivos Core do Sistema (Embedding Puro)
- `data_loader.py` - Carregamento de NCM e atributos
- `database.py` - Gerenciamento de banco ChromaDB
- `embedding_cache.py` - Cache de embeddings
- `embeddings.py` - Interface de embeddings
- `indexer.py` - Indexação de documentos
- `llm_client.py` - Cliente LLM (Claude/OpenAI)
- `search.py` - Busca por embedding (CORE)
- `main.py` - Pipeline principal
- `run_chatbot.py` - Executor do chatbot
- `ui.py` - Interface do usuário
- `system_prompt.txt` - Prompt do sistema

### Documentação Principal
- `CONCLUSAO_BUSCA_HIBRIDA.md` - Conclusões importantes
- `RELATORIO_FINAL_BENCHMARK.md` - Relatório oficial
- `CHANGELOG_V2.md` - Histórico de mudanças

**Total: 17 arquivos essenciais na raiz**

---

## 2. ARQUIVOS PARA MOVER → benchmark/

### Scripts de Teste e Benchmark
- `analyze_benchmark_results.py`
- `benchmark_embeddings.py`
- `clear_cache.py`
- `diagnose.py`
- `diagnostics.py`
- `examples.py`
- `ground_truth_cases.py`
- `run_benchmark.py`
- `run_definitive_benchmark.py`
- `test_improvements.py`
- `test_simple.py`

### Documentação de Benchmark
- `ANALISE_BENCHMARK.md`
- `ANALISE_QUEDA_PERFORMANCE.md`
- `GUIA_DIAGNOSTICO.md`
- `README_BENCHMARK.md`

**Total: 15 arquivos → benchmark/**

---

## 3. ARQUIVOS PARA MOVER → DATA/

### Dados NCM
- `SubItemNcm.csv` (579 KB - produção)
- `SubItemNcm_MINI.csv` (36 KB - testes)

### Dados de Atributos
- `ATRIBUTOS_POR_NCM_2025_09_30.json` (13.5 MB - produção)
- `ATRIBUTOS_POR_NCM_2025_09_30_MINI.json` (27 KB - testes)

**Total: 4 arquivos → DATA/**

---

## 4. ARQUIVOS PARA REMOVER ❌

### Temporários - Busca Híbrida (Experimento Concluído)
- `hybrid_search.py` - Não agrega valor (conclusão: embedding puro é melhor)
- `test_hybrid_search.py` - Experimento finalizado
- `test_atributos_loading.py` - Diagnóstico concluído

### Arquivos de Invoice (Não relacionados ao NCM)
- `invoice_exemplo.txt` - Fora do escopo
- `invoice_processor.py` - Não utilizado
- `process_invoice.py` - Não utilizado

### Documentação Ultrapassada
- `GUIA_BUSCA_HIBRIDA.md` - Experimento concluído (info está em CONCLUSAO_BUSCA_HIBRIDA.md)
- `HOTFIX_CACHE_PROGRESS.md` - Bug resolvido
- `PLANO_ACAO.md` - Ultrapassado

**Total: 9 arquivos para remover**

---

## 5. ESTRUTURA FINAL

```
RAG_NCM/
├── .env
├── .gitignore
├── config.py
├── data_loader.py
├── database.py
├── embedding_cache.py
├── embeddings.py
├── indexer.py
├── llm_client.py
├── main.py
├── run_chatbot.py
├── search.py
├── system_prompt.txt
├── ui.py
├── CHANGELOG_V2.md
├── CONCLUSAO_BUSCA_HIBRIDA.md
├── RELATORIO_FINAL_BENCHMARK.md
│
├── benchmark/
│   ├── analyze_benchmark_results.py
│   ├── benchmark_embeddings.py
│   ├── clear_cache.py
│   ├── diagnose.py
│   ├── diagnostics.py
│   ├── examples.py
│   ├── ground_truth_cases.py
│   ├── run_benchmark.py
│   ├── run_definitive_benchmark.py
│   ├── test_improvements.py
│   ├── test_simple.py
│   ├── ANALISE_BENCHMARK.md
│   ├── ANALISE_QUEDA_PERFORMANCE.md
│   ├── GUIA_DIAGNOSTICO.md
│   └── README_BENCHMARK.md
│
└── DATA/
    ├── ATRIBUTOS_POR_NCM_2025_09_30.json
    ├── ATRIBUTOS_POR_NCM_2025_09_30_MINI.json
    ├── SubItemNcm.csv
    └── SubItemNcm_MINI.csv
```

---

## 6. ALTERAÇÕES NECESSÁRIAS NOS IMPORTS

### Arquivos que importam data files (atualizar paths):

#### config.py
```python
# ANTES:
NCM_DATA_PATH = "SubItemNcm.csv"
ATRIBUTOS_DATA_PATH = "ATRIBUTOS_POR_NCM_2025_09_30.json"

# DEPOIS:
NCM_DATA_PATH = "DATA/SubItemNcm.csv"
ATRIBUTOS_DATA_PATH = "DATA/ATRIBUTOS_POR_NCM_2025_09_30.json"
```

#### Arquivos em benchmark/ que importam módulos da raiz:
```python
# ADICIONAR no início de cada arquivo:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Depois pode importar normalmente:
from data_loader import load_ncm_data
from ground_truth_cases import ground_truth_cases
```

---

## 7. RESUMO DA OPERAÇÃO

| Ação | Quantidade | Destino |
|------|-----------|---------|
| Manter na raiz | 17 arquivos | / |
| Mover para benchmark/ | 15 arquivos | benchmark/ |
| Mover para DATA/ | 4 arquivos | DATA/ |
| Remover | 9 arquivos | - |
| **TOTAL** | **45 arquivos** | - |

---

## 8. JUSTIFICATIVA

### Por que remover busca híbrida?
- Testes comprovaram: embedding puro (55.8/100) > híbrido (52.4-53.6/100)
- BM25 não agrega valor neste domínio técnico
- Simplicidade > complexidade desnecessária

### Por que remover arquivos de invoice?
- Não relacionados ao escopo de classificação NCM
- Não são utilizados pelo sistema atual
- Causam confusão sobre o propósito do projeto

### Por que separar benchmark/ e DATA/?
- Organização clara: produção vs teste vs dados
- Facilita manutenção
- Segue padrão da estrutura proposta pelo usuário
- Permite .gitignore mais granular (ex: ignorar DATA/*.json grandes)

---

*Documento gerado para reorganização do projeto RAG_NCM*
*Data: 2025-11-03*
