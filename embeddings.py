# embeddings.py
# Vetorizacao de texto usando sentence transformers

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
from tqdm import tqdm

_embedder = None


def get_embedder():
    """
    Retorna instancia singleton do modelo de embedding.

    Carrega modelo especificado em EMBEDDING_MODEL apenas na primeira
    chamada. Chamadas subsequentes retornam mesma instancia para
    economizar memoria e tempo de carregamento.

    Modelo carregado fica em memoria durante toda execucao do programa.
    """
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder

def encode_text(text):
    """
    Vetoriza texto unico em embedding.

    Converte texto em vetor numerico de alta dimensionalidade (tipicamente
    768 dimensoes) que captura significado semantico do texto.

    Retorna numpy array com embedding do texto.
    """
    embedder = get_embedder()
    return embedder.encode(text)


def encode_batch(texts, show_progress=True, batch_size=32):
    """
    Vetoriza lista de textos em lote com barra de progresso.

    Para listas pequenas (<100 textos), processa sem mostrar progresso.
    Para listas grandes, processa em batches mostrando barra de progresso.

    Processamento em batch e mais eficiente que processar textos
    individualmente, especialmente com GPU.

    Retorna lista de embeddings no formato float (compativel com ChromaDB).
    """
    embedder = get_embedder()
    
    if not show_progress or len(texts) < 100:
        return embedder.encode(texts).astype(float).tolist()
    
    all_embeddings = []
    
    with tqdm(total=len(texts), desc="Embeddings", unit="doc") as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = embedder.encode(batch)
            all_embeddings.extend(embeddings)
            pbar.update(len(batch))
    
    return [emb.astype(float).tolist() for emb in all_embeddings]