# config.py
# Configurações do sistema RAG

import os
from pickle import TRUE
from dotenv import load_dotenv

load_dotenv()

PLIN_URL = os.environ.get('PLIN_URL', '')
CLIENT_ID = os.environ.get('CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')

DB_PATH = "ncm_atributos_rag"
COLLECTION_NAME = "ncm_atributos"
CLEAR_DB = True # True para limpar o banco de dados

NCM_FILE = "SubItemNcm.csv"
ATRIBUTOS_FILE = "ATRIBUTOS_POR_NCM_2025_09_30.json"

BATCH_SIZE = 5000  # ChromaDB suporta até ~5461
#EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
#EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
#EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"


DEFAULT_MODEL = "gpt-oss-120b"
