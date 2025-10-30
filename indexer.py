# indexer.py
# Indexacao de documentos enriquecidos no banco vetorial

from embeddings import encode_batch
from config import BATCH_SIZE
from tqdm import tqdm


def prepare_ncm_documents(ncm_data, hierarchy, atributos_dict, index_only_items=False):
    """
    Prepara documentos NCM enriquecidos para indexacao
    Com deteccao robusta de nomes de colunas (encoding issues)

    Args:
        ncm_data: DataFrame com dados NCM
        hierarchy: Dicionário com hierarquia NCM
        atributos_dict: Dicionário com atributos por NCM
        index_only_items: Se True, indexa apenas items (8 dígitos completos),
                         ignorando capítulos/posições/subposições estruturais
    """
    from data_loader import create_enriched_ncm_text, detect_ncm_level

    documents = []
    metadatas = []
    ids = []

    if ncm_data.empty:
        return documents, metadatas, ids

    # CORRECAO: Detecta nomes reais das colunas (independente de encoding)
    cols = ncm_data.columns.tolist()

    # Primeira coluna = Codigo
    col_codigo = cols[0]

    # Segunda coluna = Descricao
    col_desc = cols[1] if len(cols) > 1 else None

    # Terceira coluna = CodigoNormalizado (ou buscar por nome)
    col_codigo_norm = None
    for col in cols:
        if 'Normalizado' in col or 'normalizado' in col:
            col_codigo_norm = col
            break
    if not col_codigo_norm and len(cols) > 2:
        col_codigo_norm = cols[2]

    print("Preparando documentos NCM enriquecidos...")
    print(f"Colunas detectadas: [{col_codigo}], [{col_desc}], [{col_codigo_norm}]")
    if index_only_items:
        print("Modo: Indexando apenas ITEMS completos (ignorando estrutura hierárquica)")
    else:
        print("Modo: Indexando TODOS os níveis (capítulos, posições, subitens e items)")

    skipped = 0
    skipped_structural = 0

    for idx, row in tqdm(ncm_data.iterrows(), total=len(ncm_data), desc="NCM"):
        # Usar nomes detectados
        codigo = str(row.get(col_codigo, '')).strip() if col_codigo else ''
        descricao = str(row.get(col_desc, '')).strip() if col_desc else ''
        codigo_norm = str(row.get(col_codigo_norm, '')).strip() if col_codigo_norm else codigo

        if not codigo and not descricao:
            skipped += 1
            continue

        # NOVO: Filtragem de registros estruturais
        if index_only_items and codigo_norm:
            nivel = detect_ncm_level(codigo_norm)
            # Pula capítulos, posições e subposições se index_only_items=True
            if nivel in ['capitulo', 'posicao', 'subposicao']:
                skipped_structural += 1
                continue

        doc_text = create_enriched_ncm_text(row, hierarchy, atributos_dict)

        if doc_text is None or not doc_text.strip():
            skipped += 1
            continue

        documents.append(doc_text)

        hier = hierarchy.get(codigo, {})

        metadata = {
            "tipo": "ncm",
            "codigo": codigo,
            "codigo_normalizado": codigo_norm,
            "descricao": descricao,
            "nivel": hier.get('nivel', 'desconhecido'),
            "capitulo": hier.get('capitulo', {}).get('codigo', '') if hier.get('capitulo') else '',
            "tem_atributos": codigo_norm in atributos_dict
        }

        metadatas.append(metadata)
        ids.append(f"ncm_{idx}")

    if skipped > 0:
        print(f"  Pulados {skipped} documentos vazios")
    if skipped_structural > 0:
        print(f"  Pulados {skipped_structural} registros estruturais (capítulos/posições/subposições)")

    return documents, metadatas, ids


def prepare_atributos_documents(atributos_data):
    """Prepara documentos de atributos para indexacao"""
    from data_loader import create_atributo_description
    
    documents = []
    metadatas = []
    ids = []
    
    if not atributos_data or 'listaNcm' not in atributos_data:
        return documents, metadatas, ids
    
    lista_ncm = atributos_data['listaNcm']
    total_atributos = sum(len(item['listaAtributos']) for item in lista_ncm)
    
    print("Preparando documentos de atributos...")
    with tqdm(total=total_atributos, desc="Atributos") as pbar:
        for idx, ncm_item in enumerate(lista_ncm):
            ncm_code = ncm_item['codigoNcm']
            
            for attr_idx, atributo in enumerate(ncm_item['listaAtributos']):
                doc_text = create_atributo_description(ncm_code, atributo)
                documents.append(doc_text)
                
                metadata = {
                    "tipo": "atributo",
                    "ncm_codigo": ncm_code,
                    "atributo_codigo": atributo['codigo'],
                    "modalidade": atributo['modalidade'],
                    "obrigatorio": atributo['obrigatorio'],
                    "multivalorado": atributo['multivalorado'],
                    "data_inicio_vigencia": atributo['dataInicioVigencia']
                }
                
                metadatas.append(metadata)
                ids.append(f"attr_{idx}_{attr_idx}")
                pbar.update(1)
    
    return documents, metadatas, ids


def index_documents(collection, documents, metadatas, ids):
    """Indexa documentos no banco vetorial em lotes"""
    if not documents:
        print("Nenhum documento para indexar")
        return
    
    total = len(documents)
    vectors = encode_batch(documents)
    
    print(f"\nIndexando {total} documentos em lotes de {BATCH_SIZE}...")
    
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    with tqdm(total=num_batches, desc="Indexacao") as pbar:
        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                embeddings=vectors[start:end],
                metadatas=metadatas[start:end],
            )
            
            pbar.update(1)
    
    print(f"Indexacao concluida: {total} documentos")