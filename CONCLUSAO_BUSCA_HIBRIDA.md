# CONCLUSÃO: BUSCA HÍBRIDA vs EMBEDDING PURO

## Resumo Executivo

**DECISÃO: MANTER EMBEDDING PURO**

Após testes extensivos, a busca híbrida (Embedding + BM25) **não demonstrou ganhos** para o domínio de classificação NCM. O embedding puro apresentou performance superior.

---

## Resultados dos Testes

### Teste com Documentos Enriquecidos (10.560 atributos)

| Métrica | Embedding Puro | Híbrido 60/40 | Híbrido Otimizado 80/20 |
|---------|----------------|---------------|-------------------------|
| **Score Geral** | **55.8/100** ⭐ | 52.4/100 | 53.6/100 |
| Top-1 Accuracy | 42.0% | 33.0% | 35.2% |
| Top-5 Accuracy | 60.2% | 62.5% | 60.2% |
| Distância Média | 0.3083 | 0.3881 | 0.3140 |

**Resultado:** Híbrido perdeu 2.2 a 3.4 pontos mesmo com auto-tuning.

---

## Problema Crítico Identificado e Resolvido

### Descoberta: Atributos não estavam sendo carregados

**Antes da correção:**
- Atributos carregados: **0** (deveria ser 10.560)
- Score: 50.2/100

**Depois da correção:**
- Atributos carregados: **10.560** ✓
- Score: **55.8/100** (+5.6 pontos)

### Root Cause
O código em `test_hybrid_search.py` criava o dicionário de atributos manualmente com chave errada:

```python
# ERRADO (resultava em 0 atributos):
codigo = ncm_item.get('codigo', '')  # chave inexistente

# CORRETO:
from data_loader import create_atributos_dict
self.atributos_dict = create_atributos_dict(self.atributos_data)
```

**Fix:** Commit `8795576` - Usar função `create_atributos_dict()` de `data_loader.py`

---

## Por que Busca Híbrida Não Funciona Aqui?

1. **Domínio altamente especializado**: NCM tem nomenclatura técnica padronizada
2. **Embedding já captura semântica**: multilingual-e5-base entende contexto técnico
3. **BM25 não agrega valor**: Matching lexical não supera busca semântica neste caso
4. **Hierarquia + Atributos**: Enriquecimento de documentos é mais efetivo que BM25

---

## Recomendações

### 1. MANTER Sistema Atual (Embedding Puro)
- ✓ Melhor performance (55.8/100)
- ✓ Mais rápido (17.5 queries/s vs 9.3 do híbrido)
- ✓ Simplicidade de manutenção

### 2. REMOVER Código de Busca Híbrida (Opcional)
Arquivos que podem ser removidos:
- `hybrid_search.py` - Não agrega valor
- `test_hybrid_search.py` - Experimento concluído
- `test_atributos_loading.py` - Diagnóstico concluído

### 3. MANTER Enriquecimento de Documentos
**CRÍTICO**: Garantir que `create_atributos_dict()` seja sempre usado:
- Adiciona hierarquia NCM
- Adiciona 10.560 atributos
- Resulta em +5.6 pontos de melhoria

---

## Evolução da Performance

| Versão | Score | Descrição |
|--------|-------|-----------|
| Inicial (sem atributos) | 50.2/100 | Bug: 0 atributos carregados |
| Após correção | **55.8/100** | Fix: 10.560 atributos OK |
| Target do benchmark | 57.3/100 | Diferença de 1.5 pontos |

**Gap residual (1.5 pontos)** pode ser devido a:
- Variações nos casos de teste (88 vs benchmark)
- Diferenças na forma de calcular score
- Possíveis melhorias no enrichment

---

## Commits Relacionados

1. `35bcf4f` - FEAT: Implementa Busca Híbrida (Embedding + BM25)
2. `6ca5f3c` - FIX: Corrige import de load_atributos_data
3. `6e52b4f` - FIX: Corrige import de build_ncm_hierarchy
4. `b12300f` - FIX: Corrige nomes de colunas e remove emojis
5. `b323f5e` - FIX: Usa embedder correto para query
6. `55b31f0` - FIX: Adiciona suporte a embedder customizado no HybridSearcher
7. **`8795576`** - **FIX: Corrige carregamento de atributos** (CRÍTICO)
8. `2d6ce02` - DEBUG: Adiciona debug detalhado ao test_atributos_loading.py

---

## Conclusão Final

**A busca híbrida foi implementada e testada extensivamente, mas não se mostrou benéfica para classificação NCM.**

**O fator crítico de sucesso é o enriquecimento de documentos com atributos**, não a combinação com BM25.

**Recomendação: Manter embedding puro com documentos enriquecidos (55.8/100).**

---

*Testes realizados em: 2025-11-03*
*Modelo: intfloat/multilingual-e5-base (768 dim)*
*Dataset: 15.146 NCMs | 10.560 com atributos | 88 casos de teste*
