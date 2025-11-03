# diagnostics_advanced.py
# Diagnostico avancado para avaliar qualidade do sistema RAG NCM

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from collections import defaultdict
from embeddings import encode_text
import time


def analyze_distance_distribution(collection, sample_queries):
    """Analisa distribuicao de distancias para queries de teste"""
    print("\n" + "="*70)
    print("ANALISE: DISTRIBUICAO DE DISTANCIAS")
    print("="*70)
    
    all_distances = []
    query_results = {}
    
    for query in sample_queries:
        emb = encode_text(query).astype(float).tolist()
        results = collection.query(
            query_embeddings=[emb],
            n_results=10,
            where={"tipo": "ncm"}
        )
        
        if results and results.get('distances'):
            distances = results['distances'][0]
            all_distances.extend(distances)
            query_results[query] = {
                'min': min(distances),
                'max': max(distances),
                'mean': np.mean(distances),
                'top1': distances[0] if distances else None
            }
    
    if all_distances:
        print(f"\nEstatisticas globais ({len(all_distances)} resultados):")
        print(f"  Media: {np.mean(all_distances):.4f}")
        print(f"  Mediana: {np.median(all_distances):.4f}")
        print(f"  Desvio padrao: {np.std(all_distances):.4f}")
        print(f"  Min: {min(all_distances):.4f}")
        print(f"  Max: {max(all_distances):.4f}")
        
        print("\n  Distribuicao por faixa:")
        ranges = [(0, 0.5), (0.5, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, 10)]
        for r_min, r_max in ranges:
            count = sum(1 for d in all_distances if r_min <= d < r_max)
            pct = 100 * count / len(all_distances)
            quality = get_quality_label(r_min)
            print(f"    [{r_min:.1f} - {r_max:.1f}): {count:4d} ({pct:5.1f}%) - {quality}")
        
        print("\n  Por query:")
        for query, stats in query_results.items():
            print(f"    '{query[:30]}': top1={stats['top1']:.3f}, mean={stats['mean']:.3f}")
    
    return all_distances, query_results


def get_quality_label(distance):
    """Rotulo de qualidade baseado na distancia"""
    if distance < 0.5:
        return "Excelente"
    elif distance < 0.8:
        return "Bom"
    elif distance < 1.0:
        return "Aceitavel"
    elif distance < 1.2:
        return "Ruim"
    else:
        return "Muito ruim"


def evaluate_known_ncm_queries(collection):
    """Testa queries com NCMs conhecidos (ground truth)"""
    print("\n" + "="*70)
    print("AVALIACAO: QUERIES COM GROUND TRUTH")
    print("="*70)
    
    # Casos de teste conhecidos (query, codigo_esperado)
    test_cases = [
        ("cafe torrado em graos", "0901"),  # Cafe
        ("soja em graos", "1201"),  # Soja
        ("carne bovina congelada", "0202"),  # Carne bovina
        ("telefone celular", "8517"),  # Telefones
        ("computador portatil", "8471"),  # Maquinas de processamento
        ("acucar cristal", "1701"),  # Acucar
        ("leite em po", "0402"),  # Leite
        ("arroz em graos", "1006"),  # Arroz
    ]
    
    hits = 0
    top1_hits = 0
    results = []
    
    print("\nTestando queries conhecidas (busca por capitulo):\n")
    
    for query, expected_chapter in test_cases:
        emb = encode_text(query).astype(float).tolist()
        search_results = collection.query(
            query_embeddings=[emb],
            n_results=5,
            where={"tipo": "ncm"}
        )
        
        if not search_results or not search_results.get('metadatas'):
            print(f"  FALHA: '{query}' - sem resultados")
            results.append({'query': query, 'hit': False, 'top1': False})
            continue
        
        top_results = search_results['metadatas'][0]
        top_distances = search_results['distances'][0]
        
        # Verifica se algum dos top 5 tem o capitulo correto
        found = False
        top1_match = False
        found_pos = -1
        
        for i, meta in enumerate(top_results):
            ncm_code = meta.get('codigo_normalizado', '') or meta.get('codigo', '')
            chapter = ncm_code[:4].replace('.', '')
            
            if chapter == expected_chapter:
                found = True
                found_pos = i + 1
                if i == 0:
                    top1_match = True
                break
        
        if found:
            hits += 1
            if top1_match:
                top1_hits += 1
            status = f"OK (pos {found_pos}, dist {top_distances[found_pos-1]:.3f})"
        else:
            status = "FALHA"
            top_ncm = top_results[0].get('codigo_normalizado', 'N/A')
            top_desc = top_results[0].get('descricao', '')[:40]
            status += f" - Top1: {top_ncm} ({top_desc})"
        
        print(f"  {query:30s} -> esperado:{expected_chapter} [{status}]")
        results.append({'query': query, 'hit': found, 'top1': top1_match})
    
    accuracy = 100 * hits / len(test_cases) if test_cases else 0
    top1_accuracy = 100 * top1_hits / len(test_cases) if test_cases else 0
    
    print(f"\n  Acuracia (Top-5): {hits}/{len(test_cases)} = {accuracy:.1f}%")
    print(f"  Acuracia (Top-1): {top1_hits}/{len(test_cases)} = {top1_accuracy:.1f}%")
    
    return accuracy, top1_accuracy, results


def analyze_attribute_coverage(collection):
    """Analisa cobertura de atributos nos NCMs"""
    print("\n" + "="*70)
    print("ANALISE: COBERTURA DE ATRIBUTOS")
    print("="*70)
    
    try:
        # Busca todos NCMs
        all_ncm = collection.get(where={"tipo": "ncm"}, limit=20000)
        total_ncm = len(all_ncm['ids'])
        
        # Busca todos atributos
        all_attr = collection.get(where={"tipo": "atributo"}, limit=60000)
        total_attr = len(all_attr['ids'])
        
        # Conta NCMs com atributos
        ncm_with_attr = defaultdict(int)
        attr_by_modalidade = defaultdict(int)
        attr_obrigatorios = 0
        
        for meta in all_attr['metadatas']:
            ncm_code = meta.get('ncm_codigo')
            if ncm_code:
                ncm_with_attr[ncm_code] += 1
            
            modalidade = meta.get('modalidade')
            if modalidade:
                attr_by_modalidade[modalidade] += 1
            
            if meta.get('obrigatorio'):
                attr_obrigatorios += 1
        
        ncm_count_with_attr = len(ncm_with_attr)
        pct_with_attr = 100 * ncm_count_with_attr / total_ncm if total_ncm > 0 else 0
        
        print(f"\nTotal de NCMs: {total_ncm}")
        print(f"Total de atributos: {total_attr}")
        print(f"NCMs com atributos: {ncm_count_with_attr} ({pct_with_attr:.1f}%)")
        print(f"NCMs sem atributos: {total_ncm - ncm_count_with_attr}")
        
        if ncm_with_attr:
            attr_counts = list(ncm_with_attr.values())
            print(f"\nAtributos por NCM:")
            print(f"  Media: {np.mean(attr_counts):.1f}")
            print(f"  Mediana: {int(np.median(attr_counts))}")
            print(f"  Min: {min(attr_counts)}")
            print(f"  Max: {max(attr_counts)}")
        
        print(f"\nPor modalidade:")
        for mod, count in attr_by_modalidade.items():
            pct = 100 * count / total_attr if total_attr > 0 else 0
            print(f"  {mod}: {count} ({pct:.1f}%)")
        
        pct_obr = 100 * attr_obrigatorios / total_attr if total_attr > 0 else 0
        print(f"\nAtributos obrigatorios: {attr_obrigatorios} ({pct_obr:.1f}%)")
        
        return {
            'total_ncm': total_ncm,
            'total_attr': total_attr,
            'ncm_with_attr': ncm_count_with_attr,
            'coverage_pct': pct_with_attr
        }
        
    except Exception as e:
        print(f"Erro na analise: {e}")
        return None


def analyze_embedding_quality(collection):
    """Analisa qualidade dos embeddings"""
    print("\n" + "="*70)
    print("ANALISE: QUALIDADE DOS EMBEDDINGS")
    print("="*70)
    
    from config import EMBEDDING_MODEL
    
    print(f"\nModelo: {EMBEDDING_MODEL}")
    
    # Verifica se modelo e apropriado para portugues
    is_multilingual = 'multilingual' in EMBEDDING_MODEL.lower() or 'paraphrase' in EMBEDDING_MODEL.lower()
    is_portuguese = 'portuguese' in EMBEDDING_MODEL.lower() or 'pt' in EMBEDDING_MODEL.lower()
    
    print("\nCompatibilidade com portugues:")
    if is_portuguese:
        print("  Status: OTIMO - Modelo especifico para portugues")
    elif is_multilingual:
        print("  Status: BOM - Modelo multilingue")
    else:
        print("  Status: RUIM - Modelo ingles (recomenda-se multilingual)")
        print("  Sugestao: sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    
    # Testa similaridade entre termos relacionados
    print("\nTeste de similaridade semantica:")
    test_pairs = [
        ("cafe", "cafe torrado"),
        ("soja", "graos de soja"),
        ("carne", "carne bovina"),
        ("telefone", "celular"),
    ]
    
    for term1, term2 in test_pairs:
        emb1 = encode_text(term1)
        emb2 = encode_text(term2)
        
        # Calcula distancia L2
        dist = np.linalg.norm(emb1 - emb2)
        
        # Calcula similaridade cosseno
        cos_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        print(f"  '{term1}' <-> '{term2}':")
        print(f"    Distancia L2: {dist:.4f}")
        print(f"    Similaridade cosseno: {cos_sim:.4f}")


def analyze_indexed_text_quality(collection, n_samples=10):
    """Analisa qualidade dos textos indexados"""
    print("\n" + "="*70)
    print("ANALISE: QUALIDADE DOS TEXTOS INDEXADOS")
    print("="*70)
    
    try:
        sample = collection.get(where={"tipo": "ncm"}, limit=n_samples)
        
        if not sample or not sample['documents']:
            print("Sem documentos para analisar")
            return
        
        doc_lengths = [len(doc) for doc in sample['documents']]
        
        print(f"\nAmostra de {len(doc_lengths)} documentos NCM:")
        print(f"  Tamanho medio: {np.mean(doc_lengths):.0f} caracteres")
        print(f"  Tamanho mediano: {int(np.median(doc_lengths))}")
        print(f"  Min: {min(doc_lengths)}, Max: {max(doc_lengths)}")
        
        # Mostra exemplos
        print("\n  Exemplos de textos indexados:")
        for i in range(min(3, len(sample['documents']))):
            doc = sample['documents'][i]
            meta = sample['metadatas'][i]
            codigo = meta.get('codigo_normalizado', 'N/A')
            print(f"\n  [{i+1}] NCM {codigo}:")
            print(f"      {doc[:150]}...")
        
        # Analisa estrutura
        print("\n  Estrutura dos textos:")
        has_ncm = sum(1 for doc in sample['documents'] if 'NCM:' in doc)
        has_posicao = sum(1 for doc in sample['documents'] if 'Posição' in doc or 'Posiç' in doc)
        has_subposicao = sum(1 for doc in sample['documents'] if 'Subposição' in doc or 'Subposiç' in doc)
        
        print(f"    Com 'NCM:': {has_ncm}/{len(sample['documents'])}")
        print(f"    Com 'Posicao:': {has_posicao}/{len(sample['documents'])}")
        print(f"    Com 'Subposicao:': {has_subposicao}/{len(sample['documents'])}")
        
        # Avalia se texto tem muita informacao extra
        avg_ncm_mentions = np.mean([doc.count('NCM:') for doc in sample['documents']])
        print(f"\n    Media de mencoes 'NCM:' por doc: {avg_ncm_mentions:.1f}")
        
        if avg_ncm_mentions > 1.5:
            print("    ALERTA: Textos podem conter multiplos NCMs (diluicao)")
        
    except Exception as e:
        print(f"Erro: {e}")


def generate_recommendations(stats):
    """Gera recomendacoes baseadas nas analises"""
    print("\n" + "="*70)
    print("RECOMENDACOES DE MELHORIA")
    print("="*70)
    
    from config import EMBEDDING_MODEL
    
    recommendations = []
    
    # Analise do modelo
    if 'multilingual' not in EMBEDDING_MODEL.lower():
        recommendations.append({
            'prioridade': 'ALTA',
            'categoria': 'Modelo',
            'problema': 'Modelo de embedding nao e multilingue',
            'solucao': 'Trocar para: paraphrase-multilingual-mpnet-base-v2',
            'impacto': 'Melhora significativa na qualidade das buscas em portugues'
        })
    
    # Analise de distancias
    if stats.get('mean_distance', 0) > 1.0:
        recommendations.append({
            'prioridade': 'ALTA',
            'categoria': 'Qualidade',
            'problema': 'Distancias medias muito altas (> 1.0)',
            'solucao': 'Revisar preparacao dos textos indexados',
            'impacto': 'Resultados mais relevantes nas buscas'
        })
    
    # Analise de acuracia
    if stats.get('accuracy', 100) < 70:
        recommendations.append({
            'prioridade': 'ALTA',
            'categoria': 'Acuracia',
            'problema': f"Acuracia baixa ({stats.get('accuracy', 0):.1f}%)",
            'solucao': 'Melhorar preparacao de documentos e modelo de embedding',
            'impacto': 'Respostas mais precisas'
        })
    
    # Analise de cobertura
    coverage = stats.get('coverage_pct', 0)
    if coverage < 50:
        recommendations.append({
            'prioridade': 'MEDIA',
            'categoria': 'Cobertura',
            'problema': f'Apenas {coverage:.1f}% dos NCMs tem atributos',
            'solucao': 'Verificar se arquivo de atributos esta completo',
            'impacto': 'Maior utilidade do sistema'
        })
    
    # Exibe recomendacoes
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['prioridade']}] {rec['categoria']}")
            print(f"   Problema: {rec['problema']}")
            print(f"   Solucao: {rec['solucao']}")
            print(f"   Impacto: {rec['impacto']}")
    else:
        print("\nNenhuma recomendacao critica identificada.")
        print("Sistema funcionando dentro dos parametros esperados.")



def check_prepared_documents(documents, metadatas, n=3):
    """Verifica documentos preparados antes da indexacao"""
    print("\n" + "="*70)
    print("DIAGNOSTICO: DOCUMENTOS PREPARADOS")
    print("="*70)
    
    print(f"\nTotal de documentos: {len(documents)}")
    print(f"Total de metadatas: {len(metadatas)}")
    
    if not documents:
        print("ERRO: Nenhum documento preparado")
        return
    
    print(f"\n--- AMOSTRA DE {min(n, len(documents))} DOCUMENTOS ---")
    for i in range(min(n, len(documents))):
        meta = metadatas[i]
        doc_text = documents[i]
        
        print(f"\n[{i+1}] ID: {meta.get('codigo', 'N/A')}")
        print(f"    Tipo: {meta.get('tipo', 'N/A')}")
        print(f"    Codigo Normalizado: {meta.get('codigo_normalizado', 'N/A')}")
        print(f"    Descricao: {meta.get('descricao', 'N/A')[:80]}")
        print(f"    Texto (300 primeiros chars):")
        print(f"    {doc_text[:300]}...")
        print(f"    Tamanho: {len(doc_text)} caracteres")


def comprehensive_diagnostic(collection):
    """Diagnostico basico do sistema"""
    print("\n" + "#"*70)
    print("# DIAGNOSTICO DO SISTEMA RAG NCM")
    print("#"*70)
    
    try:
        total = collection.count()
        print(f"\nTotal de documentos no banco: {total}")
        
        # Conta NCMs
        ncm_results = collection.get(where={"tipo": "ncm"}, limit=20000)
        ncm_count = len(ncm_results['ids']) if ncm_results else 0
        print(f"Documentos NCM: {ncm_count}")
        
        # Conta Atributos
        attr_results = collection.get(where={"tipo": "atributo"}, limit=60000)
        attr_count = len(attr_results['ids']) if attr_results else 0
        print(f"Documentos Atributo: {attr_count}")
        
        # Teste de busca
        print("\n" + "="*70)
        print("TESTE DE BUSCA")
        print("="*70)
        
        from embeddings import encode_text
        
        test_queries = ["cafe", "soja", "carne"]
        
        for query in test_queries:
            print(f"\nBuscando: '{query}'")
            
            query_emb = encode_text(query).astype(float).tolist()
            results = collection.query(
                query_embeddings=[query_emb],
                n_results=3,
                where={"tipo": "ncm"}
            )
            
            if results and results.get('metadatas') and results['metadatas'][0]:
                for i, (meta, dist) in enumerate(zip(results['metadatas'][0], results['distances'][0]), 1):
                    codigo = meta.get('codigo_normalizado', 'N/A')
                    desc = meta.get('descricao', '')[:50]
                    print(f"  {i}. {codigo} (dist: {dist:.3f}) - {desc}")
            else:
                print("  Sem resultados")
        
    except Exception as e:
        print(f"Erro no diagnostico: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "#"*70)
    print("# FIM DO DIAGNOSTICO")
    print("#"*70)

def comprehensive_quality_report(collection):
    """Relatorio completo de qualidade do RAG"""
    print("\n" + "#"*70)
    print("# RELATORIO DE QUALIDADE DO SISTEMA RAG NCM")
    print("#"*70)
    
    stats = {}
    
    # 1. Distribuicao de distancias
    sample_queries = [
        "cafe torrado", "soja", "carne bovina", "acucar", 
        "telefone celular", "arroz", "leite", "computador"
    ]
    
    distances, query_results = analyze_distance_distribution(collection, sample_queries)
    if distances:
        stats['mean_distance'] = np.mean(distances)
        stats['median_distance'] = np.median(distances)
    
    # 2. Avaliacao com ground truth
    accuracy, top1_acc, _ = evaluate_known_ncm_queries(collection)
    stats['accuracy'] = accuracy
    stats['top1_accuracy'] = top1_acc
    
    # 3. Cobertura de atributos
    coverage = analyze_attribute_coverage(collection)
    if coverage:
        stats['coverage_pct'] = coverage['coverage_pct']
        stats['total_ncm'] = coverage['total_ncm']
        stats['total_attr'] = coverage['total_attr']
    
    # 4. Qualidade dos embeddings
    analyze_embedding_quality(collection)
    
    # 5. Qualidade dos textos indexados
    analyze_indexed_text_quality(collection, n_samples=20)
    
    # 6. Recomendacoes
    generate_recommendations(stats)
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO EXECUTIVO")
    print("="*70)
    print(f"\nAcuracia Top-5: {stats.get('accuracy', 0):.1f}%")
    print(f"Acuracia Top-1: {stats.get('top1_accuracy', 0):.1f}%")
    print(f"Distancia media: {stats.get('mean_distance', 0):.3f}")
    print(f"Cobertura atributos: {stats.get('coverage_pct', 0):.1f}%")
    
    # Score geral
    score = (
        stats.get('accuracy', 0) * 0.4 +
        stats.get('top1_accuracy', 0) * 0.3 +
        (100 - min(100, stats.get('mean_distance', 1) * 50)) * 0.2 +
        stats.get('coverage_pct', 0) * 0.1
    )
    
    print(f"\nScore Geral: {score:.1f}/100")
    
    if score >= 80:
        status = "EXCELENTE"
    elif score >= 60:
        status = "BOM"
    elif score >= 40:
        status = "REGULAR"
    else:
        status = "NECESSITA MELHORIAS"
    
    print(f"Status: {status}")
    
    print("\n" + "#"*70)
    print("# FIM DO RELATORIO")
    print("#"*70)
    
    return stats