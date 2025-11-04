# diagnostics.py
# Diagnóstico para avaliar qualidade do sistema RAG NCM

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from embeddings import encode_text


def get_quality_label(distance):
    """Rótulo de qualidade baseado na distância"""
    if distance < 0.5:
        return "Excelente"
    elif distance < 0.8:
        return "Bom"
    elif distance < 1.0:
        return "Aceitável"
    elif distance < 1.2:
        return "Ruim"
    else:
        return "Muito ruim"


def analyze_distance_distribution(collection, sample_queries):
    """Analisa distribuição de distâncias para queries de teste"""
    print("\n" + "="*70)
    print("ANÁLISE: DISTRIBUIÇÃO DE DISTÂNCIAS")
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
        print(f"\nEstatísticas globais ({len(all_distances)} resultados):")
        print(f"  Média: {np.mean(all_distances):.4f}")
        print(f"  Mediana: {np.median(all_distances):.4f}")
        print(f"  Desvio padrão: {np.std(all_distances):.4f}")
        print(f"  Min: {min(all_distances):.4f}")
        print(f"  Max: {max(all_distances):.4f}")

        print("\n  Distribuição por faixa:")
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


def evaluate_known_ncm_queries(collection):
    """Testa queries com NCMs conhecidos (ground truth)"""
    print("\n" + "="*70)
    print("AVALIAÇÃO: QUERIES COM GROUND TRUTH")
    print("="*70)

    # Importa casos de teste
    try:
        from diagnostico.ground_truth_cases import TEST_CASES
        test_cases = [(case['query'], case['expected_ncm_prefix']) for case in TEST_CASES]
    except:
        # Fallback para casos básicos
        test_cases = [
            ("cafe torrado em graos", "0901"),
            ("soja em graos", "1201"),
            ("carne bovina congelada", "0202"),
            ("telefone celular", "8517"),
            ("computador portatil", "8471"),
            ("acucar cristal", "1701"),
            ("leite em po", "0402"),
            ("arroz em graos", "1006"),
        ]

    hits = 0
    top1_hits = 0
    results = []

    print("\nTestando queries conhecidas:\n")

    for query, expected_prefix in test_cases:
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

        found = False
        top1_match = False
        found_pos = -1

        for i, meta in enumerate(top_results):
            ncm_code = meta.get('codigo_normalizado', '') or meta.get('codigo', '')
            prefix = ncm_code[:4].replace('.', '')

            if prefix == expected_prefix:
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
            status += f" - Top1: {top_ncm}"

        print(f"  {query:30s} -> esperado:{expected_prefix} [{status}]")
        results.append({'query': query, 'hit': found, 'top1': top1_match})

    accuracy = 100 * hits / len(test_cases) if test_cases else 0
    top1_accuracy = 100 * top1_hits / len(test_cases) if test_cases else 0

    print(f"\n{'='*70}")
    print(f"Acurácia Top-5: {accuracy:.1f}% ({hits}/{len(test_cases)})")
    print(f"Acurácia Top-1: {top1_accuracy:.1f}% ({top1_hits}/{len(test_cases)})")
    print(f"{'='*70}")

    return accuracy, top1_accuracy, results


def analyze_attribute_coverage(collection):
    """Analisa cobertura de atributos por NCM"""
    print("\n" + "="*70)
    print("ANÁLISE: COBERTURA DE ATRIBUTOS")
    print("="*70)

    try:
        # Busca todos atributos
        atributos = collection.get(where={"tipo": "atributo"}, limit=100000)

        if not atributos or not atributos['metadatas']:
            print("Nenhum atributo encontrado.")
            return

        ncm_attr_count = {}
        modalidades = {'Importacao': 0, 'Exportacao': 0}
        obrigatorios = 0

        for meta in atributos['metadatas']:
            ncm = meta.get('ncm_codigo', 'N/A')
            mod = meta.get('modalidade', 'N/A')
            obr = meta.get('obrigatorio', False)

            if ncm not in ncm_attr_count:
                ncm_attr_count[ncm] = 0
            ncm_attr_count[ncm] += 1

            if mod in modalidades:
                modalidades[mod] += 1

            if obr:
                obrigatorios += 1

        print(f"\nTotal de atributos: {len(atributos['metadatas'])}")
        print(f"NCMs com atributos: {len(ncm_attr_count)}")
        print(f"\nPor modalidade:")
        print(f"  Importação: {modalidades['Importacao']}")
        print(f"  Exportação: {modalidades['Exportacao']}")
        print(f"\nObrigatórios: {obrigatorios} ({100*obrigatorios/len(atributos['metadatas']):.1f}%)")

        if ncm_attr_count:
            counts = list(ncm_attr_count.values())
            print(f"\nAtributos por NCM:")
            print(f"  Média: {np.mean(counts):.1f}")
            print(f"  Mediana: {int(np.median(counts))}")
            print(f"  Min: {min(counts)}, Max: {max(counts)}")

    except Exception as e:
        print(f"Erro: {e}")


def comprehensive_diagnostic(collection):
    """Diagnóstico rápido do sistema"""
    print("\n" + "#"*70)
    print("# DIAGNÓSTICO RÁPIDO DO SISTEMA")
    print("#"*70)

    # Info básica
    print("\n[BANCO DE DADOS]")
    print(f"  Total de documentos: {collection.count()}")

    try:
        ncm_count = len(collection.get(where={"tipo": "ncm"}, limit=20000)['ids'])
        print(f"  Documentos NCM: {ncm_count}")
    except:
        print(f"  Documentos NCM: erro ao contar")

    try:
        attr_count = len(collection.get(where={"tipo": "atributo"}, limit=100000)['ids'])
        print(f"  Documentos Atributo: {attr_count}")
    except:
        print(f"  Documentos Atributo: erro ao contar")

    # Teste de queries
    sample_queries = ["cafe", "soja", "carne", "telefone"]
    analyze_distance_distribution(collection, sample_queries)

    print("\n" + "#"*70)


def comprehensive_quality_report(collection):
    """Relatório completo de qualidade"""
    print("\n" + "#"*70)
    print("# RELATÓRIO COMPLETO DE QUALIDADE")
    print("#"*70)

    # Diagnóstico básico
    comprehensive_diagnostic(collection)

    # Avaliação com ground truth
    evaluate_known_ncm_queries(collection)

    # Cobertura de atributos
    analyze_attribute_coverage(collection)

    print("\n" + "#"*70)
    print("# RELATÓRIO CONCLUÍDO")
    print("#"*70)
