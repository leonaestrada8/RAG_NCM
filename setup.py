# setup.py
# Configuracao e indexacao do banco vetorial NCM

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import time
from datetime import datetime
from database import get_client, get_or_create_collection
from config import CLEAR_DB, INDEX_ONLY_ITEMS
# from diagnostico.diagnostics import check_prepared_documents  # Removido - função não essencial


def setup_database():
    """
    Configura o banco vetorial ChromaDB com dados enriquecidos de NCM e atributos.

    Realiza as seguintes operacoes em sequencia:
    1. Carrega dados NCM do arquivo CSV configurado
    2. Carrega atributos do arquivo JSON configurado
    3. Constroi hierarquia NCM (capitulos, posicoes, subitens, items)
    4. Cria indice de atributos por codigo NCM
    5. Prepara documentos enriquecidos com contexto hierarquico
    6. Indexa documentos no banco vetorial usando embeddings

    O processo cria embeddings vetoriais para cada documento usando o modelo
    configurado em EMBEDDING_MODEL. Os documentos sao enriquecidos com:
    - Descricao do item NCM
    - Contexto hierarquico (capitulo, posicao)
    - Indicacao de atributos cadastrados
    - Nivel hierarquico (capitulo/posicao/subposicao/item)

    Se CLEAR_DB=True ou banco vazio, executa indexacao completa.
    Se banco ja existe, reutiliza dados existentes.

    Ao final, exibe diagnostico basico do banco indexado.
    """
    from data_loader import (
        load_ncm_data, load_atributos_data,
        build_ncm_hierarchy, create_atributos_dict
    )
    from indexer import (
        prepare_ncm_documents, prepare_atributos_documents,
        index_documents
    )

    start_total = time.time()
    print("="*60)
    print("CONFIGURANDO BANCO VETORIAL ENRIQUECIDO COM HIERARQUIA")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    client = get_client()
    collection = get_or_create_collection(client, clear=CLEAR_DB)

    if CLEAR_DB or collection.count() == 0:
        print("\n[1/6] Carregando dados NCM...")
        t0 = time.time()
        ncm_data = load_ncm_data()
        print(f"  Total: {len(ncm_data)} registros ({time.time()-t0:.1f}s)")

        print("\n[2/6] Carregando atributos...")
        t0 = time.time()
        atributos_data = load_atributos_data()
        total_ncm_attr = len(atributos_data.get('listaNcm', []))
        print(f"  Total: {total_ncm_attr} NCMs com atributos ({time.time()-t0:.1f}s)")

        print("\n[3/6] Construindo hierarquia NCM...")
        t0 = time.time()
        hierarchy = build_ncm_hierarchy(ncm_data)
        print(f"  Hierarquia: {len(hierarchy)} niveis ({time.time()-t0:.1f}s)")

        print("\n[4/6] Criando indice de atributos...")
        t0 = time.time()
        atributos_dict = create_atributos_dict(atributos_data)
        print(f"  Atributos: {len(atributos_dict)} NCMs mapeados ({time.time()-t0:.1f}s)")

        print("\n[5/6] Preparando documentos enriquecidos...")
        t0 = time.time()
        ncm_docs, ncm_metas, ncm_ids = prepare_ncm_documents(
            ncm_data, hierarchy, atributos_dict, index_only_items=INDEX_ONLY_ITEMS
        )
        attr_docs, attr_metas, attr_ids = prepare_atributos_documents(
            atributos_data
        )

        all_docs = ncm_docs + attr_docs
        all_metas = ncm_metas + attr_metas
        all_ids = ncm_ids + attr_ids

        print(f"\n  Total preparado: {len(all_docs)} documentos ({time.time()-t0:.1f}s)")
        print(f"    NCMs: {len(ncm_docs)}")
        print(f"    Atributos: {len(attr_docs)}")

        # check_prepared_documents(all_docs, all_metas, n=3)  # Removido - função não essencial

        print("\n[6/6] Indexando no banco vetorial...")
        t0 = time.time()
        index_documents(collection, all_docs, all_metas, all_ids)
        print(f"  Indexacao concluida ({time.time()-t0:.1f}s)")

        elapsed = time.time() - start_total
        print(f"\nTempo total: {elapsed:.1f}s")
        print(f"Total no banco: {collection.count()} documentos")
    else:
        print(f"\nBanco existente: {collection.count()} documentos")
        print("Use CLEAR_DB=True em config.py para recriar")

    print("="*60)

    return collection
