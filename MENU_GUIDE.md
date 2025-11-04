# Guia do Menu Principal - Sistema RAG NCM

## Visão Geral

O Sistema RAG NCM agora possui um **menu principal completo** que integra TODAS as funcionalidades disponíveis no código, incluindo:
- Interfaces de usuário (Web e CLI)
- Visualização de dados
- Diagnósticos e análises de qualidade
- Benchmarks de modelos
- Configuração e manutenção
- Consultas rápidas

## Como Usar

### Iniciar o Sistema

```bash
# Modo padrão (menu principal)
python main.py

# Modo CLI tradicional (compatibilidade)
python main.py --cli

# Apenas configurar banco (sem interface)
python main.py --setup-only
```

Ou use o menu diretamente:

```bash
python menu.py
```

## Funcionalidades do Menu

### 📱 INTERFACES DE USUÁRIO (1-2)

#### 1. Interface Web (Gradio)
- Interface visual moderna via navegador
- Chat interativo com o sistema RAG
- Seleção de modelos LLM
- Formatação markdown nas respostas
- **Uso**: Ideal para demonstrações e uso interativo

#### 2. Modo Interativo CLI
- Interface de linha de comando tradicional
- Chat via terminal
- Comandos especiais integrados
- **Uso**: Ideal para servidores sem interface gráfica

---

### 📊 VISUALIZAÇÃO DE DADOS (3-5)

#### 3. Mostrar Primeiros N Registros
- Exibe os primeiros registros NCM do banco
- Mostra busca vetorial para cada registro
- Lista atributos associados
- **Uso**: Verificar qualidade da indexação

#### 4. Mostrar Registros Aleatórios
- Seleciona registros aleatórios do banco
- Útil para inspeção de diferentes partes do banco
- **Uso**: Identificar padrões ou problemas de indexação

#### 5. Estatísticas do Banco
- Total de documentos
- Contagem por tipo (NCM, atributo)
- Métricas gerais
- **Uso**: Verificação rápida do estado do banco

---

### 🔍 DIAGNÓSTICOS E QUALIDADE (6-12)

#### 6. Diagnóstico Básico
- Verificação rápida do sistema
- Teste de busca básica
- Contagem de documentos
- **Tempo**: ~30 segundos

#### 7. Relatório Completo de Qualidade
- Análise detalhada do sistema RAG
- Avaliação com ground truth
- Distribuição de distâncias
- Score geral do sistema
- **Tempo**: 2-5 minutos

#### 8. Análise de Distâncias
- Distribuição de similaridade vetorial
- Estatísticas de distâncias (média, mediana, desvio)
- Análise por faixas de qualidade
- **Uso**: Avaliar qualidade das buscas

#### 9. Análise de Cobertura
- Estatísticas de atributos por NCM
- Cobertura de importação/exportação
- Atributos obrigatórios vs opcionais
- **Uso**: Verificar completude dos dados

#### 10. Avaliar Ground Truth
- Testa com 90+ casos conhecidos
- Mede acurácia Top-1 e Top-5
- Identifica problemas de busca
- **Uso**: Benchmark de qualidade

#### 11. Qualidade de Embeddings
- Verifica compatibilidade do modelo com português
- Testa similaridade semântica
- Recomendações de modelos
- **Uso**: Validar modelo de embedding

#### 12. Qualidade de Textos
- Analisa documentos indexados
- Verifica estrutura dos textos
- Identifica problemas de preparação
- **Uso**: Debugging de indexação

---

### ⚡ BENCHMARKS (13-15)

#### 13. Executar Benchmark de Embeddings
- Testa múltiplos modelos de embedding
- Compara qualidade, velocidade e acurácia
- Gera relatório comparativo completo
- Salva configuração ideal automaticamente
- **Tempo**: 2-8 HORAS (múltiplos modelos)
- **Modelos testados**:
  - intfloat/multilingual-e5-base (baseline)
  - intfloat/multilingual-e5-large (melhor qualidade)
  - BAAI/bge-m3 (SOTA 2024)
  - BAAI/bge-large-en-v1.5
  - intfloat/multilingual-e5-small (mais rápido)

#### 14. Analisar Resultados de Benchmark
- Carrega resultados salvos
- Análise comparativa detalhada
- Recomendações por cenário
- Código para implementação
- **Uso**: Após executar benchmark

#### 15. Benchmark Rápido
- Testa apenas 2-3 modelos selecionados
- Versão otimizada para testes rápidos
- **Tempo**: 30-60 minutos

---

### ⚙️ CONFIGURAÇÃO E MANUTENÇÃO (16-19)

#### 16. Reconfigurar Banco de Dados
- Apaga banco atual
- Reindexar todos os documentos
- Útil após mudança de modelo
- **Tempo**: Vários minutos
- ⚠️ **ATENÇÃO**: Operação destrutiva

#### 17. Limpar Cache de Embeddings
- Remove todo o cache de embeddings
- Força recálculo completo
- **Uso**: Cache corrompido ou mudança de modelo
- ⚠️ Próximo benchmark será mais lento

#### 18. Limpar Cache (Parcial)
- Remove cache de modelo específico
- Preserva outros modelos
- **Uso**: Problemas com modelo específico

#### 19. Informações do Sistema
- Configurações atuais
- Estado do banco de dados
- Arquivos disponíveis
- Estatísticas de cache
- **Uso**: Verificação geral do sistema

---

### 🔎 CONSULTAS (20-22)

#### 20. Consulta Rápida NCM
- Busca hierárquica por descrição
- Prioriza items específicos
- Exibe distâncias e níveis
- **Uso**: Busca rápida de códigos NCM

#### 21. Consulta Atributos
- Lista atributos de um código NCM
- Separa importação/exportação
- Indica obrigatórios vs opcionais
- **Uso**: Verificar atributos de NCM específico

#### 22. Busca com LLM
- Query completa com resposta gerada
- Usa RAG + LLM
- Seleção de modelo
- Resposta em linguagem natural
- **Uso**: Consulta complexa com explicação

---

## Fluxo de Trabalho Recomendado

### Para Novos Usuários:

1. **Iniciar**: Execute `python main.py`
2. **Verificar Sistema**: Opção 19 (Informações do Sistema)
3. **Testar Interface**: Opção 1 (Interface Web Gradio) ou 2 (CLI)
4. **Explorar Dados**: Opções 3-5 (Visualizações)

### Para Análise de Qualidade:

1. **Diagnóstico Rápido**: Opção 6 (Diagnóstico Básico)
2. **Análise Completa**: Opção 7 (Relatório de Qualidade)
3. **Detalhamento**: Opções 8-12 (Análises específicas)

### Para Otimização:

1. **Avaliar Atual**: Opção 10 (Ground Truth)
2. **Benchmark**: Opção 13 ou 15 (Benchmark de modelos)
3. **Analisar**: Opção 14 (Análise de resultados)
4. **Reconfigurar**: Opção 16 (com novo modelo)

### Para Manutenção:

1. **Verificar**: Opção 19 (Informações do Sistema)
2. **Limpar Cache**: Opção 17 ou 18 (se necessário)
3. **Reindexar**: Opção 16 (se necessário)

---

## Dicas e Truques

### Performance
- **Cache de Embeddings**: Acelera benchmarks subsequentes em 10-20x
- **Benchmark Rápido**: Use opção 15 para testes iniciais
- **Index Only Items**: Configure `INDEX_ONLY_ITEMS=True` para banco menor

### Qualidade
- **Score > 80**: Sistema excelente, pronto para produção
- **Score 60-80**: Sistema bom, considere otimizações
- **Score < 60**: Necessita melhorias (modelo, preparação de dados)

### Modelos
- **multilingual-e5-large**: Melhor qualidade, mais lento
- **multilingual-e5-base**: Bom equilíbrio
- **multilingual-e5-small**: Mais rápido, qualidade aceitável

### Troubleshooting
- **Erro de importação**: Instale dependências: `pip install -r requirements.txt`
- **Cache corrompido**: Use opção 17 (Limpar Cache)
- **Banco corrompido**: Use opção 16 (Reconfigurar)
- **Modelo não encontrado**: Verifique conexão com HuggingFace

---

## Atalhos

```bash
# Executar menu principal
python main.py

# Executar menu diretamente
python menu.py

# Modo CLI antigo
python main.py --cli

# Interface Gradio direta
python run_chatbot.py

# Apenas setup
python main.py --setup-only

# Benchmark direto
python benchmark/benchmark_embeddings.py

# Análise de benchmark
python benchmark/analyze_benchmark_results.py

# Limpar cache
python benchmark/clear_cache.py
```

---

## Arquivos Gerados

O sistema gera automaticamente:

### Resultados de Benchmark
- `benchmark_results_YYYYMMDD_HHMMSS.json` - Resultados detalhados
- `best_model_config.json` - Configuração do melhor modelo
- `best_model_config.py` - Módulo Python importável

### Cache
- `cache/embeddings/*.pkl` - Cache de embeddings
- `cache/embeddings/metadata.json` - Metadados do cache

### Banco de Dados
- `chroma_db/` - Banco vetorial ChromaDB

---

## Requisitos do Sistema

### Mínimo
- Python 3.8+
- 4GB RAM
- 2GB espaço em disco

### Recomendado
- Python 3.10+
- 16GB RAM
- 10GB espaço em disco
- GPU (opcional, acelera embeddings)

### Dependências Principais
- chromadb
- sentence-transformers
- pandas
- numpy
- tqdm
- gradio (para interface web)
- ollama (para LLM)

---

## Suporte

Para problemas ou sugestões:
1. Verifique opção 19 (Informações do Sistema)
2. Execute opção 6 (Diagnóstico Básico)
3. Consulte logs e mensagens de erro
4. Abra issue no repositório

---

## Changelog

### v2.0 - Menu Principal Completo
- ✅ Menu unificado com 22 funcionalidades
- ✅ Integração de todas features existentes
- ✅ Documentação completa
- ✅ Modo compatibilidade (--cli)
- ✅ Interface Web Gradio integrada
- ✅ Benchmarks completos
- ✅ Diagnósticos avançados
- ✅ Sistema de cache otimizado

---

**Desenvolvido com ❤️ para o Sistema RAG NCM**
