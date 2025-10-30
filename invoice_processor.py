# invoice_processor.py
# Processamento de invoices JSON com dados RAG

import json
from search import find_ncm_and_atributos

def load_invoice_json(file_path):
    """Carrega arquivo JSON de invoice"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_invoice_items(collection, invoice_data):
    """Processa itens de invoice buscando NCM e atributos"""
    results = []
    
    for item in invoice_data.get('itens', []):
        descricao = item.get('descricao', '')
        ncm_existente = item.get('ncm', '')
        
        ncm_encontrado, atributos_encontrados = find_ncm_and_atributos(collection, descricao)
        
        item_result = {
            'itemNumber': item.get('itemNumber'),
            'descricao': descricao,
            'ncm_existente': ncm_existente,
            'ncm_encontrado': ncm_encontrado,
            'atributos_encontrados': atributos_encontrados
        }
        
        results.append(item_result)
    
    return results

def create_invoice_with_rag_data(invoice_data, rag_results):
    """Cria JSON combinando invoice com dados RAG"""
    invoice_with_rag = invoice_data.copy()
    
    for i, item in enumerate(invoice_with_rag.get('itens', [])):
        if i < len(rag_results):
            rag_info = rag_results[i]
            item['rag_info'] = {
                'ncm_encontrado': rag_info['ncm_encontrado'],
                'atributos_encontrados': rag_info['atributos_encontrados']
            }
    
    return invoice_with_rag

def save_results_to_file(invoice_with_rag, filename):
    """Salva resultado em arquivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(invoice_with_rag, f, indent=2, ensure_ascii=False)
    print(f"Resultado salvo em: {filename}")