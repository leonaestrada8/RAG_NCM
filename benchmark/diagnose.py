#!/usr/bin/env python3
# diagnose.py
# Ferramentas de diagnóstico para investigar queda de performance

"""
DIAGNÓSTICO COMPLETO DO BENCHMARK

Testa cada hipótese de problema:
1. Cache corrompido
2. Normalização agressiva
3. Ground truth muito difícil

Uso:
    python diagnose.py --all                 # Todos os testes
    python diagnose.py --cache               # Apenas cache
    python diagnose.py --normalization       # Apenas normalização
    python diagnose.py --ground-truth        # Apenas ground truth
"""

import argparse
import json
import sys
from pathlib import Path
import pandas as pd


def check_cache_integrity():
    """
    Verifica integridade do cache

    Problemas detectados:
    - Modelos com nome genérico
    - Embeddings duplicados
    - Tamanho inconsistente
    """
    print("\n" + "="*70)
    print("DIAGNÓSTICO 1: INTEGRIDADE DO CACHE")
    print("="*70)

    cache_dir = Path("cache/embeddings")
    metadata_file = cache_dir / "metadata.json"

    if not metadata_file.exists():
        print("❌ Cache não encontrado ou vazio")
        return {"status": "empty", "issues": []}

    # Carrega metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    entries = metadata.get("entries", {})

    # Análise
    issues = []
    models = {}
    total_size = 0

    print(f"\n📊 Estatísticas do Cache:")
    print(f"  Total de entradas: {len(entries)}")

    for hash_key, meta in entries.items():
        model_name = meta.get("model", "unknown")

        # Conta por modelo
        if model_name not in models:
            models[model_name] = 0
        models[model_name] += 1

        # Verifica arquivo existe
        cache_file = cache_dir / f"{hash_key}.pkl"
        if cache_file.exists():
            total_size += cache_file.stat().st_size
        else:
            issues.append(f"Arquivo faltando: {hash_key}")

    print(f"  Tamanho total: {total_size / (1024**2):.2f} MB")
    print(f"\n📁 Distribuição por Modelo:")

    for model_name, count in sorted(models.items(), key=lambda x: -x[1]):
        print(f"  {model_name}: {count} embeddings")

        # Detecta problemas
        if "SentenceTransformer" in model_name or "unknown" in model_name:
            issues.append(f"⚠️  Modelo com nome genérico: {model_name} ({count} embeddings)")

    # Verifica duplicados
    text_hashes = {}
    for hash_key, meta in entries.items():
        text_len = meta.get("text_length", 0)
        key = f"{meta.get('model')}_{text_len}"

        if key not in text_hashes:
            text_hashes[key] = 0
        text_hashes[key] += 1

    duplicates = {k: v for k, v in text_hashes.items() if v > 100}
    if duplicates:
        issues.append(f"Possíveis duplicados: {len(duplicates)} grupos")

    # Resultado
    print(f"\n🔍 Problemas Detectados: {len(issues)}")
    if issues:
        for issue in issues[:10]:  # Mostra até 10
            print(f"  ❌ {issue}")

        if len(issues) > 10:
            print(f"  ... e mais {len(issues) - 10} problemas")

        print(f"\n⚠️  RECOMENDAÇÃO: Limpar cache com 'python clear_cache.py'")
        return {"status": "corrupted", "issues": issues, "models": models}
    else:
        print("  ✅ Nenhum problema detectado")
        return {"status": "ok", "issues": [], "models": models}


def test_normalization_impact():
    """
    Testa impacto da normalização

    Compara resultados com e sem normalização
    """
    print("\n" + "="*70)
    print("DIAGNÓSTICO 2: IMPACTO DA NORMALIZAÇÃO")
    print("="*70)

    # Importa funções
    sys.path.insert(0, '.')
    from data_loader import normalize_text_advanced

    # Casos de teste
    test_cases = [
        "NCM 0901.11.10: Café em grão não descafeinado",
        "Capítulo 09: Café, chá, mate e especiarias",
        "Telefone celular tipo smartphone",
        "Computador portátil (notebook)",
        "Carne bovina congelada, em cortes",
        "Óleo de soja refinado, em recipientes com capacidade inferior ou igual a 5 litros",
    ]

    print("\n📝 Comparação Original vs Normalizado:\n")

    problematic = 0

    for text in test_cases:
        normalized = normalize_text_advanced(text)

        # Calcula perda de informação
        original_words = set(text.lower().split())
        normalized_words = set(normalized.split())
        lost_words = original_words - normalized_words

        print(f"Original:    {text}")
        print(f"Normalizado: {normalized}")

        if lost_words:
            print(f"⚠️  Palavras perdidas: {', '.join(lost_words)}")
            problematic += 1

        print(f"Tamanho: {len(text)} → {len(normalized)} ({(len(normalized)/len(text)*100):.1f}%)")
        print()

    # Análise
    print(f"🔍 Análise:")
    print(f"  Casos testados: {len(test_cases)}")
    print(f"  Com perda de info: {problematic}/{len(test_cases)} ({problematic/len(test_cases)*100:.1f}%)")

    if problematic > len(test_cases) * 0.5:
        print(f"\n⚠️  RECOMENDAÇÃO: Normalização muito agressiva!")
        print(f"     Testar sem normalização: python run_definitive_benchmark.py --no-normalize")
        return {"status": "aggressive", "problematic_pct": problematic/len(test_cases)*100}
    else:
        print(f"\n✅ Normalização parece adequada")
        return {"status": "ok", "problematic_pct": problematic/len(test_cases)*100}


def analyze_ground_truth():
    """
    Analisa dificuldade do ground truth

    Categoriza casos por dificuldade
    """
    print("\n" + "="*70)
    print("DIAGNÓSTICO 3: DIFICULDADE DO GROUND TRUTH")
    print("="*70)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from benchmark.ground_truth_cases import TEST_CASES, EDGE_CASES

    print(f"\n📊 Estatísticas:")
    print(f"  Casos normais: {len(TEST_CASES)}")
    print(f"  Edge cases: {len(EDGE_CASES)}")
    print(f"  Total: {len(TEST_CASES) + len(EDGE_CASES)}")

    # Analisa complexidade
    easy = 0
    medium = 0
    hard = 0

    for query, ncm in TEST_CASES:
        words = query.split()

        # Heurística de dificuldade
        if len(words) <= 2:
            hard += 1  # Muito genérico
        elif len(words) <= 4:
            easy += 1  # Descritivo curto
        else:
            medium += 1  # Descritivo longo

    print(f"\n🎯 Distribuição de Dificuldade (heurística):")
    print(f"  Fáceis:  {easy}/{len(TEST_CASES)} ({easy/len(TEST_CASES)*100:.1f}%)")
    print(f"  Médios:  {medium}/{len(TEST_CASES)} ({medium/len(TEST_CASES)*100:.1f}%)")
    print(f"  Difíceis: {hard}/{len(TEST_CASES)} ({hard/len(TEST_CASES)*100:.1f}%)")

    # Exemplos
    print(f"\n📝 Exemplos de Casos Difíceis:")
    difficult_examples = [q for q, _ in TEST_CASES if len(q.split()) <= 2][:5]
    for ex in difficult_examples:
        print(f"  - '{ex}' (muito genérico)")

    if hard > len(TEST_CASES) * 0.3:
        print(f"\n⚠️  RECOMENDAÇÃO: Ground truth tem muitos casos difíceis!")
        print(f"     Isso explica queda de performance (esperado)")
        return {"status": "difficult", "hard_pct": hard/len(TEST_CASES)*100}
    else:
        print(f"\n✅ Ground truth balanceado")
        return {"status": "balanced", "hard_pct": hard/len(TEST_CASES)*100}


def compare_with_baseline():
    """
    Compara com resultados do baseline

    Lê resultados anteriores e compara
    """
    print("\n" + "="*70)
    print("DIAGNÓSTICO 4: COMPARAÇÃO COM BASELINE")
    print("="*70)

    # Procura resultados anteriores
    result_files = list(Path(".").glob("benchmark_results_*.json"))

    if not result_files:
        print("❌ Nenhum resultado anterior encontrado")
        return {"status": "no_baseline"}

    # Carrega resultados
    results = []
    for file in sorted(result_files, reverse=True)[:5]:  # Últimos 5
        with open(file, 'r') as f:
            data = json.load(f)
            for model_result in data:
                if model_result.get('model_name') == 'intfloat/multilingual-e5-base':
                    results.append({
                        'file': file.name,
                        'timestamp': model_result.get('timestamp'),
                        'score': model_result.get('score'),
                        'accuracy_top5': model_result.get('accuracy_top5'),
                        'accuracy_top1': model_result.get('accuracy_top1'),
                    })

    if not results:
        print("❌ Nenhum resultado para intfloat/multilingual-e5-base encontrado")
        return {"status": "no_data"}

    # Cria DataFrame
    df = pd.DataFrame(results)

    print(f"\n📊 Histórico de Performance (intfloat/multilingual-e5-base):\n")
    print(df.to_string(index=False))

    # Análise de tendência
    if len(results) >= 2:
        latest = results[0]
        previous = results[1]

        score_change = latest['score'] - previous['score']

        print(f"\n📈 Mudança mais recente:")
        print(f"  Score: {previous['score']:.1f} → {latest['score']:.1f} ({score_change:+.1f})")
        print(f"  Top-5: {previous['accuracy_top5']:.1f}% → {latest['accuracy_top5']:.1f}% ({latest['accuracy_top5'] - previous['accuracy_top5']:+.1f}%)")
        print(f"  Top-1: {previous['accuracy_top1']:.1f}% → {latest['accuracy_top1']:.1f}% ({latest['accuracy_top1'] - previous['accuracy_top1']:+.1f}%)")

        if score_change < -10:
            print(f"\n⚠️  REGRESSÃO DETECTADA: Score caiu {abs(score_change):.1f} pontos!")
            return {"status": "regression", "change": score_change}
        elif score_change > 10:
            print(f"\n✅ MELHORIA DETECTADA: Score subiu {score_change:.1f} pontos!")
            return {"status": "improvement", "change": score_change}
        else:
            print(f"\n✅ Performance estável")
            return {"status": "stable", "change": score_change}

    return {"status": "ok"}


def run_all_diagnostics():
    """Executa todos os diagnósticos"""
    print("\n" + "#"*70)
    print("# DIAGNÓSTICO COMPLETO DO BENCHMARK")
    print("#"*70)

    results = {}

    # 1. Cache
    results['cache'] = check_cache_integrity()

    # 2. Normalização
    results['normalization'] = test_normalization_impact()

    # 3. Ground Truth
    results['ground_truth'] = analyze_ground_truth()

    # 4. Baseline
    results['baseline'] = compare_with_baseline()

    # Resumo final
    print("\n" + "="*70)
    print("RESUMO DO DIAGNÓSTICO")
    print("="*70)

    issues_found = []

    if results['cache']['status'] == 'corrupted':
        issues_found.append("⚠️  Cache corrompido")

    if results['normalization']['status'] == 'aggressive':
        issues_found.append("⚠️  Normalização muito agressiva")

    if results['ground_truth']['status'] == 'difficult':
        issues_found.append("ℹ️  Ground truth difícil (esperado)")

    if results['baseline'].get('status') == 'regression':
        issues_found.append("⚠️  Regressão de performance detectada")

    if issues_found:
        print(f"\n🔍 Problemas Identificados ({len(issues_found)}):")
        for issue in issues_found:
            print(f"  {issue}")

        print(f"\n📋 AÇÕES RECOMENDADAS:")

        if results['cache']['status'] == 'corrupted':
            print(f"  1. Limpar cache: python clear_cache.py")

        if results['normalization']['status'] == 'aggressive':
            print(f"  2. Testar sem normalização: editar data_loader.py")

        if results['baseline'].get('status') == 'regression':
            print(f"  3. Re-executar benchmark após correções")
    else:
        print(f"\n✅ Nenhum problema detectado!")
        print(f"   Performance dentro do esperado.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnóstico completo do benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--all', action='store_true', help='Todos os testes')
    parser.add_argument('--cache', action='store_true', help='Apenas cache')
    parser.add_argument('--normalization', action='store_true', help='Apenas normalização')
    parser.add_argument('--ground-truth', action='store_true', help='Apenas ground truth')
    parser.add_argument('--baseline', action='store_true', help='Apenas baseline')

    args = parser.parse_args()

    # Se nenhum argumento, executa tudo
    if not any([args.all, args.cache, args.normalization, args.ground_truth, args.baseline]):
        args.all = True

    if args.all:
        run_all_diagnostics()
    else:
        if args.cache:
            check_cache_integrity()
        if args.normalization:
            test_normalization_impact()
        if args.ground_truth:
            analyze_ground_truth()
        if args.baseline:
            compare_with_baseline()
