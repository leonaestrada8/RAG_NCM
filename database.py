# database.py
# Gerenciamento do banco vetorial ChromaDB

import chromadb
from config import DB_PATH, COLLECTION_NAME

def get_client():
    """Retorna cliente ChromaDB persistente"""
    return chromadb.PersistentClient(path=DB_PATH)

def clear_collection(client):
    """Remove coleção existente"""
    existing_collections = [col.name for col in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        client.delete_collection(COLLECTION_NAME)
        print(f"Coleção removida: {COLLECTION_NAME}")

def get_or_create_collection(client, clear=False):
    """Obtém ou cria coleção no banco"""
    if clear:
        clear_collection(client)
        collection = client.create_collection(COLLECTION_NAME)
    else:
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
        except:
            collection = client.create_collection(COLLECTION_NAME)
    
    return collection