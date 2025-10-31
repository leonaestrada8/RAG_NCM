# 📊 Benchmark de Modelos de Embedding - RAG NCM

Sistema completo de benchmark para seleção do melhor modelo de embedding para o sistema RAG de classificação NCM.

## 🎯 Objetivo

Identificar o melhor modelo de embedding para buscas semânticas em códigos NCM (Nomenclatura Comum do Mercosul), considerando:
- **Acurácia**: Precisão nas buscas (Top-1 e Top-5)
- **Performance**: Velocidade de indexação
- **Qualidade**: Score geral balanceado

---

## 📈 Resultados do Benchmark Inicial

**Data:** 2025-10-30

| Modelo | Score | Top-5 | Top-1 | Tempo |
|--------|-------|-------|-------|-------|
| 🥇 **intfloat/multilingual-e5-base** | **75.6** | 87.5% | 62.5% | 83 min |
| 🥈 paraphrase-multilingual-mpnet-base-v2 | 54.0 | 75.0% | 62.5% | 127 min |
| 🥉 all-MiniLM-L6-v2 | 50.1 | 62.5% | 37.5% | 33 min |

**Veredicto:** Parcialmente satisfatório. Recomenda-se nova rodada com melhorias.

---

## ✨ Melhorias Implementadas (Versão 2.0)

### 1. Ground Truth Expandido
- **Antes:** 8 casos de teste
- **Depois:** 90+ casos cobrindo 15+ categorias NCM
- **Impacto:** +2-3% acurácia, mais confiança estatística

### 2. Cache de Embeddings
- **Funcionalidade:** Salva embeddings em disco
- **Impacto:** Reduz tempo de re-execução em 80-90%
- **Exemplo:** 83 min → 8 min em segunda execução

### 3. Normalização Avançada
- Remove acentos mantendo semântica
- Lowercase + limpeza de pontuação
- Remoção seletiva de stopwords
- **Impacto:** +2-3% acurácia

### 4. Validação de Modelos
- Verifica existência antes de testar
- Tratamento robusto de erros
- Relatórios claros de falhas

### 5. Auto-configuração
- Gera automaticamente configuração ideal
- Exports JSON + módulo Python
- Recomendações de re-ranking

---

## 🚀 Como Executar

### Execução Padrão (Recomendado)

```bash
python run_definitive_benchmark.py
```

Testa os modelos mais promissores:
- `intfloat/multilingual-e5-base` (baseline)
- `intfloat/multilingual-e5-large` (melhor versão)
- `BAAI/bge-m3` (SOTA 2024)
- `BAAI/bge-large-en-v1.5` (alternativa)

**Tempo estimado:** 2-4 horas (primeira vez) / 20-40 min (com cache)

### Execução Rápida (Validação)

```bash
python run_definitive_benchmark.py --quick
```

Testa apenas o modelo base para validar que tudo está funcionando.

**Tempo estimado:** ~30 min (primeira vez) / ~5 min (com cache)

### Execução Completa

```bash
python run_definitive_benchmark.py --all
```

Inclui todos os modelos para comparação abrangente.

### Sem Cache (Forçar Recálculo)

```bash
python run_definitive_benchmark.py --no-cache
```

Útil para garantir resultados limpos sem cache anterior.

### Modo Automático (Sem Confirmação)

```bash
python run_definitive_benchmark.py --yes
```

Pula a confirmação interativa (útil para scripts).

---

## 📁 Arquivos Gerados

### benchmark_results_YYYYMMDD_HHMMSS.json
Resultados detalhados de todos os modelos testados.

```json
{
  "model_name": "intfloat/multilingual-e5-base",
  "score": 75.6,
  "accuracy_top1": 62.5,
  "accuracy_top5": 87.5,
  "mean_distance": 0.338,
  "elapsed_time": 4971.1,
  ...
}
```

### best_model_config.json
Configuração ideal para uso em produção.

```json
{
  "model": {
    "name": "intfloat/multilingual-e5-base",
    "score": 75.6,
    "accuracy_top1": 62.5,
    "accuracy_top5": 87.5
  },
  "settings": {
    "use_cache": true,
    "use_reranking": true,
    "batch_size": 32,
    "top_k_initial": 15,
    "top_k_final": 5
  },
  "performance": {
    "recommended_for_production": false
  }
}
```

### best_model_config.py
Módulo Python para import direto no código.

```python
from best_model_config import load_best_model

# Carrega automaticamente o melhor modelo
model = load_best_model()
```

---

## 📊 Interpretando Resultados

### Score Geral (0-100)

Fórmula ponderada:
```
Score = (Top-5 × 0.4) + (Top-1 × 0.3) + (Distância × 0.2) + (Cobertura × 0.1)
```

**Interpretação:**
- **< 70:** Insuficiente para produção
- **70-80:** Aceitável com melhorias (re-ranking)
- **80-90:** Bom para produção
- **> 90:** Excelente

### Acurácia Top-K

- **Top-1:** Resultado correto na primeira posição
- **Top-5:** Resultado correto entre os 5 primeiros

**Metas:**
- Top-5: ≥ 90% (crítico)
- Top-1: ≥ 75% (ideal)

### Distância Média

Métrica interna do ChromaDB (menor = melhor)
- Valores baixos indicam embeddings mais discriminativos
- Comparável apenas entre modelos com mesma dimensão

---

## 🔧 Próximos Passos Após Benchmark

### Se Score ≥ 80
1. ✓ Usar modelo em produção imediatamente
2. Monitorar performance real
3. Coletar feedback de usuários

### Se Score 70-80
1. Implementar re-ranking (ver `PLANO_ACAO.md`)
2. Testar em ambiente de homologação
3. Avaliar trade-off latência/qualidade

### Se Score < 70
1. Revisar dados de entrada (NCMs e atributos)
2. Implementar melhorias do `PLANO_ACAO.md`:
   - Re-ranking com CrossEncoder
   - Fine-tuning do modelo
   - Enriquecimento de dados
3. Executar novo benchmark

---

## 🛠️ Estrutura do Projeto

```
RAG_NCM/
├── benchmark_embeddings.py          # Código principal do benchmark
├── run_definitive_benchmark.py      # Script de execução facilitado
├── embedding_cache.py               # Sistema de cache
├── ground_truth_cases.py            # 90+ casos de teste
├── data_loader.py                   # Carregamento e normalização
├── config.py                        # Configurações
│
├── ANALISE_BENCHMARK.md             # Análise detalhada dos resultados
├── PLANO_ACAO.md                    # Roadmap de melhorias
├── README_BENCHMARK.md              # Este arquivo
│
└── Gerados após execução:
    ├── best_model_config.json       # Configuração ideal
    ├── best_model_config.py         # Módulo Python
    ├── benchmark_results_*.json     # Resultados detalhados
    └── cache/embeddings/            # Cache de embeddings
```

---

## 💡 Dicas e Boas Práticas

### Cache

✓ **Ativar cache** para desenvolvimento (padrão)
- Acelera iterações
- Economiza tempo e recursos

✗ **Desativar cache** para benchmark final
- Garante resultados limpos
- Evita inconsistências

### Modelos

**Priorizar modelos multilíngue:**
- `intfloat/multilingual-e5-*`
- `BAAI/bge-m3`
- `sentence-transformers/LaBSE`

**Evitar modelos inglês-only:**
- `all-MiniLM-L6-v2` (não multilíngue)
- Performance ruim com português

### Ground Truth

**Manter casos atualizados:**
- Adicionar casos de falhas reais
- Cobrir categorias representativas
- Testar edge cases

**Arquivo:** `ground_truth_cases.py`

---

## 🐛 Troubleshooting

### Erro: "Modelo não encontrado"

```
✗ ERRO: Modelo X não encontrado ou inacessível
```

**Solução:**
1. Verificar nome do modelo em https://huggingface.co/models
2. Verificar conexão com internet
3. Autenticar: `huggingface-cli login` (se modelo privado)

### Cache corrompido

```
Erro ao ler cache XXX
```

**Solução:**
```bash
rm -rf cache/embeddings/*
python run_definitive_benchmark.py --no-cache
```

### Memória insuficiente

```
CUDA out of memory / MemoryError
```

**Solução:**
1. Reduzir `BATCH_SIZE` em `config.py`
2. Usar modelos menores (-base em vez de -large)
3. Rodar sem GPU (CPU only)

### ChromaDB travado

```
Collection creation failed
```

**Solução:**
```bash
rm -rf benchmark_db_*
```

---

## 📚 Documentação Adicional

- **Análise completa:** `ANALISE_BENCHMARK.md`
- **Plano de melhorias:** `PLANO_ACAO.md`
- **Código do benchmark:** `benchmark_embeddings.py`

---

## 🤝 Contribuindo

Para adicionar novos modelos ao benchmark:

1. Editar `benchmark_embeddings.py`:
```python
MODELS_TO_TEST = [
    'intfloat/multilingual-e5-base',
    'seu/novo-modelo',  # Adicionar aqui
]
```

2. Executar benchmark:
```bash
python run_definitive_benchmark.py
```

---

## 📞 Suporte

- **Issues:** Reportar problemas via GitHub Issues
- **Dúvidas:** Consultar `ANALISE_BENCHMARK.md` ou `PLANO_ACAO.md`

---

**Última atualização:** 2025-10-31
**Versão:** 2.0 (com melhorias integradas)
