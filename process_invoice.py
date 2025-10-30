# process_invoice.py
# Script para processar invoices JSON

import sys
from main import setup_database
from invoice_processor import load_invoice_json, process_invoice_items, create_invoice_with_rag_data, save_results_to_file

def main():
    if len(sys.argv) < 2:
        print("Uso: python process_invoice.py <arquivo_invoice.json> [arquivo_saida.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"{input_file.rsplit('.', 1)[0]}_with_rag.json"
    
    print("Configurando sistema RAG")
    collection = setup_database()
    
    print(f"Carregando invoice: {input_file}")
    invoice_data = load_invoice_json(input_file)
    
    print(f"Total de itens: {len(invoice_data.get('itens', []))}")
    rag_results = process_invoice_items(collection, invoice_data)
    
    print("Criando invoice com dados RAG")
    invoice_with_rag = create_invoice_with_rag_data(invoice_data, rag_results)
    
    save_results_to_file(invoice_with_rag, output_file)
    print("Processamento concluído")
    
    for result in rag_results:
        if result['ncm_encontrado']:
            print(f"  Item {result['itemNumber']}: NCM {result['ncm_encontrado']['codigo']}")
        else:
            print(f"  Item {result['itemNumber']}: NCM não encontrado")

if __name__ == "__main__":
    main()