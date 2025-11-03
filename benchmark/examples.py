# examples.py
# Exemplos de uso dos módulos do sistema RAG

from main import setup_database
from search import find_ncm_by_description, find_atributos_by_ncm, find_ncm_and_atributos

def example_busca_ncm():
    """Exemplo de busca de NCM por descrição"""
    collection = setup_database()
    
    resultados = find_ncm_by_description(collection, "cavalo reprodutor de raça pura")
    
    print("Busca de NCM:")
    for r in resultados[:3]:
        print(f"  NCM: {r['codigo']} - {r['descricao']}")

def example_busca_atributos():
    """Exemplo de busca de atributos por NCM"""
    collection = setup_database()
    
    atributos = find_atributos_by_ncm(collection, "0101.21.00")
    
    print("Atributos do NCM 0101.21.00:")
    for attr in atributos[:5]:
        print(f"  {attr['atributo_codigo']} ({attr['modalidade']}) - Obrigatório: {attr['obrigatorio']}")

def example_busca_completa():
    """Exemplo de busca completa de NCM e atributos"""
    collection = setup_database()
    
    ncm, atributos = find_ncm_and_atributos(collection, "bovino para reprodução")
    
    if ncm:
        print(f"NCM encontrado: {ncm['codigo']}")
        print(f"Descrição: {ncm['descricao']}")
        print(f"Total de atributos: {len(atributos)}")

if __name__ == "__main__":
    print("Exemplo 1: Busca de NCM")
    example_busca_ncm()
    
    print("\nExemplo 2: Busca de atributos")
    example_busca_atributos()
    
    print("\nExemplo 3: Busca completa")
    example_busca_completa()