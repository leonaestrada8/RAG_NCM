# search.py
# Busca vetorial no banco ChromaDB com filtros e ranking

from embeddings import encode_text


def find_similars(collection, query_text, k=15, filters=None, min_score=None):
    """
    Busca documentos similares no banco vetorial.

    Processo:
    1. Vetoriza query_text usando modelo de embedding
    2. Busca k documentos mais similares no ChromaDB
    3. Aplica filtros de metadata se especificados
    4. Filtra por score minimo (distancia maxima) se especificado

    Distancia: menor = mais similar (0 = identico, >1 = muito diferente)
    Score: 1 - distancia (maior = mais similar)

    Retorna lista de dicionarios com documento, metadata e metricas
    de similaridade (distance e score).
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
    Busca NCMs por descricao usando similaridade vetorial.

    Filtra resultados para retornar apenas documentos do tipo 'ncm',
    excluindo atributos. Usa k=10 por padrao para boa cobertura de resultados.

    Retorna lista ordenada por similaridade (mais similar primeiro).
    """
    return find_similars(
        collection, 
        description_text, 
        k=k, 
        filters={"tipo": "ncm"}
    )


def find_atributos_by_ncm(collection, ncm_code, k=20):
    """
    Busca atributos associados a um codigo NCM especifico.

    Normaliza codigo NCM para formato padrao antes da busca.
    Usa busca exata por metadata (nao vetorial) filtrando por
    tipo='atributo' AND ncm_codigo=codigo_normalizado.

    Retorna lista de atributos com informacoes de modalidade
    (Importacao/Exportacao), obrigatoriedade, multivalorado, etc.
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
    """
    Busca NCM por descricao e retorna NCM com seus atributos.

    Primeiro encontra melhor NCM por similaridade vetorial, depois
    busca atributos desse NCM especifico.

    Retorna tupla: (melhor_ncm, lista_de_atributos)
    """
    ncm_hits = find_ncm_by_description(collection, description_text, k=5)
    
    if not ncm_hits:
        return None, []
    
    best_ncm = ncm_hits[0]
    ncm_code = best_ncm.get('codigo_normalizado') or best_ncm.get('codigo')
    
    atributos_hits = find_atributos_by_ncm(collection, ncm_code)
    
    return best_ncm, atributos_hits


def search_with_context(collection, query, k=8):
    """
    Busca contextualizada retornando NCMs com atributos enriquecidos.

    Para cada NCM encontrado, busca seus atributos e inclui no resultado.
    Cada resultado contem NCM completo mais lista de atributos e contagem.

    Usado para fornecer contexto completo ao LLM no sistema RAG.
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


def find_ncm_hierarchical(collection, query_text, k=10, prefer_items=True, min_distance=None):
    """
    Busca hierarquica priorizando items especificos sobre categorias gerais.

    Estrategia de busca:
    1. Busca k*3 resultados iniciais para ter opcoes de filtragem
    2. Filtra por distancia minima se especificado
    3. Se prefer_items=True, reorganiza resultados priorizando:
       - Items (8 digitos) primeiro
       - Subposicoes depois
       - Posicoes depois
       - Capitulos por ultimo
    4. Retorna top k resultados apos priorizacao

    Evita retornar categorias gerais quando existem items especificos
    relevantes, melhorando precisao das respostas.
    """
    # Busca mais resultados inicialmente para ter opções de filtragem
    results = find_similars(
        collection,
        query_text,
        k=k*3,  # Busca 3x mais para poder filtrar e priorizar
        filters={"tipo": "ncm"}
    )

    if not results:
        return []

    # Filtra por distância mínima se especificado
    if min_distance is not None:
        results = [r for r in results if r.get('distance', 1) <= min_distance]

    if prefer_items:
        # Separa por nível hierárquico
        items = [r for r in results if r.get('nivel') == 'item']
        subposicoes = [r for r in results if r.get('nivel') == 'subposicao']
        posicoes = [r for r in results if r.get('nivel') == 'posicao']
        capitulos = [r for r in results if r.get('nivel') == 'capitulo']
        outros = [r for r in results if r.get('nivel') not in ['item', 'subposicao', 'posicao', 'capitulo']]

        # Retorna priorizando items, depois subposições, depois posições, depois capítulos
        prioritized = items + subposicoes + posicoes + capitulos + outros
        return prioritized[:k]

    return results[:k]


def find_ncm_hierarchical_with_context(collection, query_text, k=8):
    """
    Busca hierarquica com contexto completo de NCMs e atributos.

    Combina find_ncm_hierarchical (priorizacao de items especificos)
    com enriquecimento de atributos (search_with_context).

    Para cada NCM encontrado hierarquicamente, adiciona seus atributos.

    Funcao principal usada no modo interativo para alimentar LLM com
    contexto completo e preciso.
    """
    ncm_results = find_ncm_hierarchical(collection, query_text, k=k, prefer_items=True)

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