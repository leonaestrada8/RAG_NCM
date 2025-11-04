# database.py
# Gerenciamento do banco vetorial ChromaDB

import chromadb
from config import DB_PATH, COLLECTION_NAME


def get_client():
    """
    Cria e retorna cliente ChromaDB persistente.

    Utiliza PersistentClient para armazenar dados em disco no diretorio
    especificado em DB_PATH. Permite reutilizar banco entre execucoes
    sem necessidade de reindexacao.
    """
    return chromadb.PersistentClient(path=DB_PATH)


def clear_collection(client):
    """
    Remove colecao existente do banco se existir.

    Verifica lista de colecoes e deleta a colecao com nome COLLECTION_NAME
    se encontrada. Operacao destrutiva - dados sao perdidos permanentemente.
    """
    existing_collections = [col.name for col in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        client.delete_collection(COLLECTION_NAME)
        print(f"Coleção removida: {COLLECTION_NAME}")

def get_or_create_collection(client, clear=False):
    """
    Obtem colecao existente ou cria nova se nao existir.

    Se clear=True, remove colecao existente antes de criar nova (reindexacao).
    Se clear=False, tenta obter colecao existente; se nao existir, cria nova.

    Retorna objeto collection do ChromaDB pronto para operacoes de
    adicao, busca e consulta de documentos vetoriais.
    """
    if clear:
        clear_collection(client)
        collection = client.create_collection(COLLECTION_NAME)
    else:
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
        except:
            collection = client.create_collection(COLLECTION_NAME)
    
    return collection