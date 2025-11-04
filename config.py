# config.py
# Configuracoes do sistema RAG NCM

import os
from dotenv import load_dotenv

load_dotenv()

# Credenciais API LLM
# Obtidas de arquivo .env ou variaveis de ambiente
PLIN_URL = os.environ.get('PLIN_URL', '')
CLIENT_ID = os.environ.get('CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')

# Configuracao do banco vetorial ChromaDB
# DB_PATH: diretorio onde ChromaDB persiste dados
# COLLECTION_NAME: nome da colecao dentro do banco
DB_PATH = "ncm_atributos_rag"
COLLECTION_NAME = "ncm_atributos"

# Controla se banco deve ser limpo e recriado
# True: remove banco existente e reindexar tudo
# False: reutiliza banco existente se disponivel
CLEAR_DB = False

# Arquivos de dados fonte
# NCM_FILE: CSV com codigos e descricoes NCM
# ATRIBUTOS_FILE: JSON com atributos por NCM
NCM_FILE = "DATA/SubItemNcm.csv"
ATRIBUTOS_FILE = "DATA/ATRIBUTOS_POR_NCM_2025_09_30.json"

# Controla estrategia de indexacao hierarquica
# False: indexa todos niveis (capitulos, posicoes, subitens, items)
#        - Mais documentos, melhor contexto geral, possivel ruido
# True: indexa apenas items completos (8 digitos)
#       - Menos documentos, mais preciso, perde contexto hierarquico
INDEX_ONLY_ITEMS = False

# Tamanho do lote para indexacao no ChromaDB
# ChromaDB tem limite de ~5461 documentos por lote
BATCH_SIZE = 5000

# Modelo de embedding para vetorizacao de texto
# Modelo multilingue recomendado para textos em portugues
# Gera vetores de 768 dimensoes que capturam semantica do texto
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# Modelo LLM padrao para geracao de respostas
# Usado no modo interativo quando modelo nao especificado
DEFAULT_MODEL = "gpt-oss-120b"
