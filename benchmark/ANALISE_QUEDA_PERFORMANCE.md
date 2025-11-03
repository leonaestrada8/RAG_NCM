# 🚨 ANÁLISE: Queda de Performance no Benchmark v2.0

**Data:** 2025-10-31
**Problema:** Score caiu de 75.6 para 55.2 (-20.4 pontos)

---

## 📊 COMPARAÇÃO DE RESULTADOS

### Modelo: intfloat/multilingual-e5-base

| Métrica | Benchmark Inicial | Benchmark v2.0 | Variação |
|---------|------------------|----------------|----------|
| **Score Geral** | **75.6/100** ✅ | **55.2/100** ❌ | **-20.4** |
| **Acurácia Top-5** | **87.5%** | **55.7%** | **-31.8%** |
| **Acurácia Top-1** | **62.5%** | **36.4%** | **-26.1%** |
| **Distância Média** | 0.3387 | 0.3190 | -0.0197 ✅ |
| **Ground Truth** | 8 casos | 88 casos | +80 casos |
| **Tempo** | 4971s (83 min) | 3823s (64 min) | -19 min ✅ |

**Status:** ⚠️ **REGRESSÃO CRÍTICA**

---

## 🔍 CAUSAS IDENTIFICADAS

### 1. Ground Truth Mais Rigoroso ✅ (Esperado)

**Análise:** Expandir de 8 para 88 casos **torna o teste mais difícil**.

**Casos adicionados incluem:**
- ❌ Consultas genéricas: `"carro"` → difícil classificar
- ❌ Consultas muito específicas: `"smartphone samsung galaxy s21 128gb"`
- ❌ Erros ortográficos: `"telefon celular"` (sem 'e')
- ❌ Consultas em inglês: `"mobile phone"`

**Impacto estimado:** -5 a -10 pontos no score

**Veredicto:** ✅ **ESPERADO** - Ground truth mais realista

---

### 2. Normalização de Texto Agressiva ⚠️

**Código implementado:**
```python
def normalize_text_advanced(text):
    # Remove acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')

    # Lowercase
    text = text.lower()

    # Remove pontuação
    text = re.sub(r'[^\w\s-]', ' ', text)

    # Remove stopwords
    stopwords = {'de', 'da', 'do', 'em', 'na', 'no', 'para', 'com'}
    words = [w for w in text.split() if w not in stopwords]

    return ' '.join(words)
```

**Problema:** Pode estar removendo contexto importante!

**Exemplo:**
```
ANTES:
"NCM 0901.11.10: Café em grão não descafeinado
Capítulo: Café, chá, mate e especiarias"

DEPOIS:
"ncm 0901 11 10 cafe grao nao descafeinado | capitulo cafe cha mate especiarias"
```

**Potenciais problemas:**
- ❌ Separador ` | ` pode confundir modelo
- ❌ Remoção de stopwords pode perder contexto (`"em grão"` → `"grao"`)
- ❌ Quebra de números NCM (`0901.11.10` → `0901 11 10`)

**Impacto estimado:** -5 a -10 pontos

**Veredicto:** ⚠️ **SUSPEITO** - Normalização pode estar muito agressiva

---

### 3. Bug no Cache - Nome de Modelo Errado 🐛

**Problema detectado:**
```
Cache atual mostra:
  - SentenceTransformer: 12731 embeddings  👈 NOME GENÉRICO ERRADO!

Deveria mostrar:
  - intfloat/multilingual-e5-base: 12731 embeddings
```

**Código problemático:**
```python
# ANTES (bugado)
model_name = embedder._model_card_data.model_name if hasattr(embedder, '_model_card_data') else str(type(embedder).__name__)
#                                                                                                ^^^ Retorna "SentenceTransformer"
```

**Consequência:** Cache está salvando embeddings de **modelos diferentes com mesmo nome**!

Isso pode causar:
- ✅ Cache hit em modelo errado
- ❌ Embeddings de um modelo sendo usado por outro
- ❌ Resultados inconsistentes

**Impacto estimado:** -5 a -15 pontos (SE houver mistura de modelos)

**Veredicto:** 🐛 **BUG CRÍTICO** - Corrigido neste commit

---

## ✅ CORREÇÕES IMPLEMENTADAS

### 1. Progresso de Cache: 1000 → 10000

**Mudança:**
```python
# ANTES
if (idx + 1) % 1000 == 0:
    print(f"  Salvos: {idx + 1}/{len(texts)}")

# DEPOIS
if (idx + 1) % 10000 == 0:
    print(f"  Salvos: {idx + 1}/{len(texts)}")
```

**Benefício:** Menos poluição visual, progresso mais limpo

---

### 2. Nome Correto do Modelo no Cache

**Mudança:**
```python
# ANTES (bugado)
model_name = embedder._model_card_data.model_name if hasattr(embedder, '_model_card_data') else str(type(embedder).__name__)

# DEPOIS (corrigido)
if hasattr(embedder, '_model_card_data') and hasattr(embedder._model_card_data, 'model_name'):
    model_name = embedder._model_card_data.model_name
elif hasattr(embedder, 'model_card_data') and hasattr(embedder.model_card_data, 'model_name'):
    model_name = embedder.model_card_data.model_name
elif hasattr(embedder, '_model_name'):
    model_name = embedder._model_name
else:
    # Fallback robusto
    if hasattr(embedder, '_modules') and '0' in embedder._modules:
        transformer = embedder._modules['0']
        if hasattr(transformer, 'auto_model'):
            model_name = transformer.auto_model.name_or_path
        else:
            model_name = "unknown_model"
```

**Benefício:** Cache agora usa nome real do modelo

---

### 3. Debug de Nome do Modelo

**Adicionado:**
```python
# Debug: mostra nome do modelo usado no cache
if len(texts) > 1000:
    print(f"Cache: usando modelo '{model_name}'")
```

**Benefício:** Visibilidade de qual modelo está sendo usado

---

### 4. Script para Limpar Cache Corrompido

**Criado:** `clear_cache.py`

**Uso:**
```bash
# Limpar todo o cache
python clear_cache.py

# Limpar apenas modelos específicos
python clear_cache.py --model e5
```

---

## 🎯 RECOMENDAÇÕES

### Ação Imediata

1. **Limpar cache corrompido:**
   ```bash
   python clear_cache.py
   ```

2. **Re-executar benchmark:**
   ```bash
   python run_definitive_benchmark.py
   ```

3. **Comparar resultados:**
   - Se score voltar para ~75: bug do cache era a causa
   - Se continuar ~55: problema é a normalização ou ground truth

---

### Teste A/B da Normalização

Se score continuar baixo, testar **sem normalização**:

```python
# Em data_loader.py, comentar normalização:
# return normalize_text_advanced(final_text)
return final_text  # SEM normalização
```

Re-executar e comparar.

---

### Análise do Ground Truth

Verificar quais casos estão falhando:

```python
# Adicionar em run_diagnostics():
for query, expected in test_cases:
    results = ...
    if not match:
        print(f"❌ FALHOU: '{query}' esperava '{expected}'")
```

---

## 📈 EXPECTATIVA PÓS-CORREÇÃO

### Cenário 1: Bug do Cache era a Causa Principal

**Se limpar cache e re-executar:**
- Score esperado: **70-75/100** ✅
- Top-5: **80-85%**
- Top-1: **55-60%**

**Diferença do inicial:** Leve queda devido a ground truth mais rigoroso (esperado)

---

### Cenário 2: Normalização é o Problema

**Se desabilitar normalização:**
- Score esperado: **75-80/100** ✅
- Top-5: **85-90%**
- Top-1: **60-65%**

**Ação:** Ajustar normalização para ser menos agressiva

---

### Cenário 3: Ground Truth Muito Difícil

**Se score continuar baixo mesmo sem normalização:**
- Revisar ground truth
- Remover casos impossíveis
- Categorizar casos por dificuldade

---

## 📝 CHECKLIST DE VALIDAÇÃO

Após correções:

- [ ] Cache limpo
- [ ] Benchmark re-executado
- [ ] Score >= 70/100
- [ ] Top-5 >= 80%
- [ ] Cache mostra nome correto do modelo
- [ ] Resultados comparados com inicial

---

## 🐛 BUGS CORRIGIDOS NESTE COMMIT

1. ✅ Nome de modelo no cache (crítico)
2. ✅ Progresso muito verboso (10000 em vez de 1000)
3. ✅ Falta de debug de qual modelo está sendo usado

---

## 📞 PRÓXIMOS PASSOS

1. **Usuário deve executar:**
   ```bash
   git pull
   python clear_cache.py
   python run_definitive_benchmark.py
   ```

2. **Aguardar resultado**

3. **Reportar score final:**
   - Se >= 70: ✅ Problema resolvido
   - Se < 70: ⚠️ Investigar normalização

---

**Preparado por:** Claude Code
**Data:** 2025-10-31
**Status:** 🔧 CORREÇÕES APLICADAS - AGUARDANDO VALIDAÇÃO
