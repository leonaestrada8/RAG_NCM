# search.py
# Busca aprimorada no banco vetorial com filtros e normalização

from embeddings import encode_text


def find_similars(collection, query_text, k=15, filters=None, min_score=None):
    """
    Busca documentos similares com opção de filtro por score
    
    Args:
        collection: Coleção ChromaDB
        query_text: Texto da consulta
        k: Número de resultados
        filters: Filtros de metadata
        min_score: Score mínimo (distância máxima)
    """
    emb = encode_text(query_text).astype(float).tolist()
    
    res = collection.query(
        query_embeddings=[emb],
        n_results=k,
        where=filters
    )
    
    if not res or not res.get("documents") or not res["documents"][0]:
        return []
    
    distances = (res.get("distances") or [[]])[0]
    ids = (res.get("ids") or [[]])[0]
    
    hits = []
    for doc, meta, _id, dist in zip(res["documents"][0], res["metadatas"][0], ids, distances):
        if min_score is not None and dist > min_score:
            continue
        
        hits.append({
            "id": _id,
            "document": doc,
            "distance": dist,
            "score": 1 - dist,
            "tipo": meta.get("tipo"),
            "codigo": meta.get("codigo"),
            "codigo_normalizado": meta.get("codigo_normalizado"),
            "descricao": meta.get("descricao"),
            "ncm_codigo": meta.get("ncm_codigo"),
            "atributo_codigo": meta.get("atributo_codigo"),
            "modalidade": meta.get("modalidade"),
            "obrigatorio": meta.get("obrigatorio"),
            "multivalorado": meta.get("multivalorado"),
            "data_inicio_vigencia": meta.get("data_inicio_vigencia"),
            "nivel": meta.get("nivel"),
            "capitulo": meta.get("capitulo")
        })
    
    return hits


def find_ncm_by_description(collection, description_text, k=10):
    """
    Busca NCMs por descrição com k maior para melhor cobertura
    """
    return find_similars(
        collection, 
        description_text, 
        k=k, 
        filters={"tipo": "ncm"}
    )


def find_atributos_by_ncm(collection, ncm_code, k=20):
    """
    Busca atributos para NCM com normalização de código
    """
    from data_loader import normalize_ncm_code
    
    if not ncm_code or str(ncm_code).strip() == '':
        return []
    
    ncm_normalized = normalize_ncm_code(ncm_code)
    
    try:
        results = collection.get(
            where={
                "$and": [
                    {"tipo": "atributo"}, 
                    {"ncm_codigo": ncm_normalized}
                ]
            },
            limit=k
        )
        
        if not results or not results.get('ids'):
            return []
        
        hits = []
        for meta in results['metadatas']:
            hits.append({
                "tipo": "atributo",
                "ncm_codigo": meta.get("ncm_codigo"),
                "atributo_codigo": meta.get("atributo_codigo"),
                "modalidade": meta.get("modalidade"),
                "obrigatorio": meta.get("obrigatorio"),
                "multivalorado": meta.get("multivalorado"),
                "data_inicio_vigencia": meta.get("data_inicio_vigencia")
            })
        
        return hits
        
    except Exception as e:
        print(f"Erro ao buscar atributos: {e}")
        return []


def find_ncm_and_atributos(collection, description_text):
    """Busca NCM e seus atributos por descrição"""
    ncm_hits = find_ncm_by_description(collection, description_text, k=5)
    
    if not ncm_hits:
        return None, []
    
    best_ncm = ncm_hits[0]
    ncm_code = best_ncm.get('codigo_normalizado') or best_ncm.get('codigo')
    
    atributos_hits = find_atributos_by_ncm(collection, ncm_code)
    
    return best_ncm, atributos_hits


def search_with_context(collection, query, k=8):
    """
    Busca contextualizada que retorna NCMs e atributos relacionados
    """
    ncm_results = find_ncm_by_description(collection, query, k=k)
    
    enriched_results = []
    for ncm in ncm_results:
        ncm_code = ncm.get('codigo_normalizado') or ncm.get('codigo')
        atributos = find_atributos_by_ncm(collection, ncm_code, k=10)
        
        enriched_results.append({
            **ncm,
            "atributos": atributos,
            "num_atributos": len(atributos)
        })
    
    return enriched_results