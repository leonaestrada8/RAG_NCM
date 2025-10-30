# main.py
# Sistema RAG NCM com normalizacao, hierarquia e enriquecimento + diagnosticos

# WORKAROUND: Previne erro de loop infinito do PyTorch no Windows
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import sys
from database import get_client, get_or_create_collection
from config import CLEAR_DB, DEFAULT_MODEL
import time
import argparse
import random
from diagnostics import check_prepared_documents, comprehensive_diagnostic


def setup_database():
    """Configura banco vetorial com dados enriquecidos"""
    from data_loader import (
        load_ncm_data, load_atributos_data,
        build_ncm_hierarchy, create_atributos_dict
    )
    from indexer import (
        prepare_ncm_documents, prepare_atributos_documents,
        index_documents
    )
    from config import INDEX_ONLY_ITEMS
    from datetime import datetime

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
        
        check_prepared_documents(all_docs, all_metas, n=3)
        
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
    
    show_sample_data(collection, 5)
    show_random_data(collection, 5)
    
    comprehensive_diagnostic(collection)
    
    return collection


def show_sample_data(collection, n=5):
    """Mostra N primeiros NCMs indexados com detalhes"""
    from search import find_atributos_by_ncm, find_ncm_by_description
    
    print("\n" + "="*60)
    print(f"AMOSTRA DE DADOS INDEXADOS ({n} primeiros NCMs)")
    print("="*60)
    
    try:
        ncm_results = collection.get(
            where={"tipo": "ncm"},
            limit=n
        )
        
        if not ncm_results or not ncm_results['ids']:
            print("Nenhum NCM encontrado")
            return
        
        for i in range(min(n, len(ncm_results['ids']))):
            meta = ncm_results['metadatas'][i]
            codigo = meta.get('codigo', '')
            codigo_norm = meta.get('codigo_normalizado', '')
            descricao = meta.get('descricao', '')
            
            print(f"\n{'-'*60}")
            print(f"{i+1}. NCM: {codigo_norm or codigo}")
            print('-'*60)
            
            print(f"\nDescricao: {descricao}")
            
            if descricao and len(descricao) > 3:
                print(f"\nBusca vetorial por '{descricao[:30]}...':")
                vet_results = find_ncm_by_description(collection, descricao, k=3)
                for j, vr in enumerate(vet_results[:3], 1):
                    vr_cod = vr.get('codigo_normalizado') or vr.get('codigo')
                    vr_desc = vr.get('descricao', '')[:40]
                    dist = vr.get('distance', 1)
                    print(f"  {j}. {vr_cod} (distancia: {dist:.4f}) {vr_desc}")
            
            if not codigo_norm and not codigo:
                print("   Codigo invalido")
                continue
            
            atributos = find_atributos_by_ncm(collection, codigo_norm or codigo, k=20)
            
            if not atributos:
                print("\n   Nenhum atributo cadastrado")
                continue
            
            imp = [a for a in atributos if a['modalidade'] == 'Importacao']
            exp = [a for a in atributos if a['modalidade'] == 'Exportacao']
            
            print(f"\n   Total de atributos: {len(atributos)}")
            print(f"   - Importacao: {len(imp)}")
            print(f"   - Exportacao: {len(exp)}")
            
            if imp:
                obr_count = sum(1 for a in imp if a['obrigatorio'])
                print(f"\n   Atributos de Importacao ({obr_count} obrigatorios):")
                for attr in imp[:3]:
                    obr = "[OBRIG]" if attr['obrigatorio'] else "[OPC]  "
                    print(f"   - {attr['atributo_codigo']:12s} {obr}")
                if len(imp) > 3:
                    print(f"   ... e mais {len(imp)-3}")
            
            if exp:
                obr_count = sum(1 for a in exp if a['obrigatorio'])
                print(f"\n   Atributos de Exportacao ({obr_count} obrigatorios):")
                for attr in exp[:3]:
                    obr = "[OBRIG]" if attr['obrigatorio'] else "[OPC]  "
                    print(f"   - {attr['atributo_codigo']:12s} {obr}")
                if len(exp) > 3:
                    print(f"   ... e mais {len(exp)-3}")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)


def show_random_data(collection, n=5):
    """Mostra N registros aleatorios do banco"""
    from search import find_atributos_by_ncm, find_ncm_by_description
    
    print("\n" + "="*60)
    print(f"DADOS ALEATORIOS ({n} registros)")
    print("="*60)
    
    try:
        all_ncm = collection.get(
            where={"tipo": "ncm"},
            limit=20000
        )
        
        if not all_ncm or not all_ncm['ids']:
            print("Nenhum NCM encontrado")
            return
        
        total_ncm = len(all_ncm['ids'])
        print(f"\nTotal de NCMs no banco: {total_ncm}")
        print(f"Selecionando {min(n, total_ncm)} aleatoriamente...\n")
        
        n_to_show = min(n, total_ncm)
        random_indices = random.sample(range(total_ncm), n_to_show)
        
        for i, idx in enumerate(random_indices, 1):
            meta = all_ncm['metadatas'][idx]
            codigo_norm = meta.get('codigo_normalizado', 'N/A')
            descricao = meta.get('descricao', '')[:60]
            
            print(f"{'-'*60}")
            print(f"{i}. NCM: {codigo_norm}")
            print(f"{'-'*60}")
            print(f"   Descricao: {descricao}")
            
            if descricao and len(descricao) > 5:
                print(f"\n   Busca vetorial:")
                vet_results = find_ncm_by_description(collection, descricao, k=2)
                for j, vr in enumerate(vet_results[:2], 1):
                    vr_cod = vr.get('codigo_normalizado', 'N/A')
                    dist = vr.get('distance', 1)
                    print(f"     {j}. {vr_cod} (distancia: {dist:.4f})")
            
            atributos = find_atributos_by_ncm(collection, codigo_norm, k=20)
            
            if atributos:
                imp = [a for a in atributos if a['modalidade'] == 'Importacao']
                exp = [a for a in atributos if a['modalidade'] == 'Exportacao']
                
                print(f"\n   Total de atributos: {len(atributos)}")
                
                if imp or exp:
                    if imp:
                        obr_imp = sum(1 for a in imp if a['obrigatorio'])
                        print(f"   - Importacao: {len(imp)} ({obr_imp} obrigatorios)")
                        for attr in imp[:2]:
                            obr = "[OBRIG] " if attr['obrigatorio'] else "[OPC]   "
                            print(f"     {obr}{attr['atributo_codigo']}")
                        if len(imp) > 2:
                            print(f"     ... e mais {len(imp)-2}")
                    
                    if exp:
                        obr_exp = sum(1 for a in exp if a['obrigatorio'])
                        print(f"   - Exportacao: {len(exp)} ({obr_exp} obrigatorios)")
                        for attr in exp[:2]:
                            obr = "[OBRIG] " if attr['obrigatorio'] else "[OPC]   "
                            print(f"     {obr}{attr['atributo_codigo']}")
                        if len(exp) > 2:
                            print(f"     ... e mais {len(exp)-2}")
            else:
                print("   Sem atributos cadastrados")
            
            print()
    
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60)


def show_statistics(collection):
    """Exibe estatisticas do banco"""
    print("\n" + "="*60)
    print("ESTATISTICAS DO BANCO")
    print("="*60)
    
    total = collection.count()
    print(f"\nTotal de documentos: {total}")
    
    try:
        ncm_count = len(collection.get(where={"tipo": "ncm"}, limit=20000)['ids'])
        print(f"Documentos NCM: {ncm_count}")
        
        attr_count = len(collection.get(where={"tipo": "atributo"}, limit=60000)['ids'])
        print(f"Documentos Atributo: {attr_count}")
    except Exception as e:
        print(f"Erro ao contar: {e}")
    
    print("="*60)


def interactive_mode(collection, prompt_file="system_prompt.txt"):
    """Modo interativo com busca hierárquica melhorada"""
    from llm_client import chat, get_models, load_system_prompt
    from search import (
        find_ncm_by_description, find_atributos_by_ncm,
        find_ncm_hierarchical, find_ncm_hierarchical_with_context
    )
    
    print(f"\nCarregando prompt: {prompt_file}")
    load_system_prompt(prompt_file)
    
    print("\n" + "="*60)
    print("MODO INTERATIVO - RAG NCM COM BUSCA HIERÁRQUICA")
    print("="*60)
    print("\nComandos disponiveis:")
    print("  Digite sua pergunta e pressione Enter")
    print("  'consulta <descricao>' - busca NCM por descricao (hierarquica)")
    print("  'atributos <codigo_ncm>' - busca atributos de NCM")
    print("  'stats' - estatisticas do banco de dados")
    print("  'diagnostico' - relatorio completo de qualidade")
    print("  'sample <n>' - mostra n primeiros registros")
    print("  'random <n>' - mostra n registros aleatorios")
    print("  'modelos' - lista modelos disponiveis")
    print("  'modelo <nome>' - troca modelo atual")
    print("  'sair' - encerra o programa")
    print("="*60)
    
    try:
        models = get_models()
        current_model = DEFAULT_MODEL if DEFAULT_MODEL in models else (models[8] if models else DEFAULT_MODEL)
        print(f"\nModelo atual: {current_model}")
    except Exception as e:
        print(f"\nErro ao carregar modelos: {e}")
        current_model = DEFAULT_MODEL
    
    print("\n" + "-"*60)
    
    while True:
        try:
            prompt = input("\n[VOCE] ").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() in ['sair', 'exit', 'quit']:
                print("\nEncerrando...")
                break
            
            if prompt.lower() == 'stats':
                show_statistics(collection)
                continue
            
            if prompt.lower() == 'diagnostico':
                try:
                    from diagnostics_advanced import comprehensive_quality_report
                    comprehensive_quality_report(collection)
                except ImportError:
                    print("diagnostics_advanced.py nao encontrado")
                    print("Execute comprehensive_diagnostic padrao:")
                    comprehensive_diagnostic(collection)
                continue
            
            if prompt.lower().startswith('consulta '):
                descricao = prompt[9:].strip()
                print(f"\nBuscando (hierarquico): {descricao}")
                results = find_ncm_hierarchical(collection, descricao, k=5, prefer_items=True)
                if results:
                    print("\nResultados (priorizando items específicos):")
                    for i, r in enumerate(results, 1):
                        cod = r.get('codigo_normalizado') or r.get('codigo')
                        desc = r['descricao'][:60]
                        dist = r['distance']
                        nivel = r.get('nivel', 'desconhecido')
                        print(f"  {i}. NCM {cod} [{nivel}] (distancia: {dist:.4f})")
                        print(f"     {desc}")
                else:
                    print("Nenhum resultado")
                continue
            
            if prompt.lower().startswith('atributos '):
                ncm_code = prompt[10:].strip()
                print(f"\nBuscando atributos: {ncm_code}")
                results = find_atributos_by_ncm(collection, ncm_code, k=20)
                if results:
                    imp = [r for r in results if r['modalidade'] == 'Importacao']
                    exp = [r for r in results if r['modalidade'] == 'Exportacao']
                    print(f"\nTotal: {len(results)} atributos")
                    if imp:
                        print(f"\nImportacao ({len(imp)}):")
                        for r in imp[:5]:
                            obr = "Obrig" if r['obrigatorio'] else "Opc"
                            print(f"  - {r['atributo_codigo']} ({obr})")
                    if exp:
                        print(f"\nExportacao ({len(exp)}):")
                        for r in exp[:5]:
                            obr = "Obrig" if r['obrigatorio'] else "Opc"
                            print(f"  - {r['atributo_codigo']} ({obr})")
                else:
                    print("Nenhum atributo")
                continue
            
            if prompt.lower().startswith('sample '):
                try:
                    n = int(prompt[7:].strip())
                    show_sample_data(collection, n)
                except ValueError:
                    print("Uso: sample <numero>")
                continue
            
            if prompt.lower().startswith('random '):
                try:
                    n = int(prompt[7:].strip())
                    show_random_data(collection, n)
                except ValueError:
                    print("Uso: random <numero>")
                continue
            
            if prompt.lower() == 'modelos':
                try:
                    models = get_models()
                    print("\nModelos disponiveis:")
                    for i, m in enumerate(models, 1):
                        print(f"  {i}. {m}")
                except Exception as e:
                    print(f"Erro ao listar modelos: {e}")
                continue
            
            if prompt.lower().startswith('modelo '):
                new_model = prompt[7:].strip()
                current_model = new_model
                print(f"Modelo alterado para: {current_model}")
                continue
            
            print(f"\n[RAG] Buscando informacoes (modo hierarquico)...")
            print(f"[LLM] Gerando resposta com {current_model}...\n")

            result = ""
            for chunk in chat(collection, prompt, current_model, find_ncm_hierarchical_with_context):
                result = chunk

            print(f"[ASSISTENTE]\n{result}")
            print("\n" + "-"*60)
            
        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            break
        except Exception as e:
            print(f"\nErro: {e}")
            continue


def main():
    """Funcao principal"""
    parser = argparse.ArgumentParser(description='Sistema RAG NCM Aprimorado')
    parser.add_argument('--prompt', type=str, default='system_prompt.txt')
    parser.add_argument('--setup-only', action='store_true')
    
    args = parser.parse_args()
    
    collection = setup_database()
    
    if not args.setup_only:
        interactive_mode(collection, prompt_file=args.prompt)
    
    return collection


if __name__ == "__main__":
    main()