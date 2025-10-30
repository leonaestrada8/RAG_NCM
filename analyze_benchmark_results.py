# analyze_benchmark_results.py
# Analisa resultados do benchmark e gera recomendacao

import json
import sys
from datetime import datetime

def load_results(filename):
    """Carrega arquivo de resultados JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Arquivo nao encontrado: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao ler JSON: {filename}")
        return None

def analyze_results(results):
    """Analisa resultados e gera insights"""
    if not results:
        return
    
    print("\n" + "="*70)
    print("ANALISE DETALHADA DOS RESULTADOS")
    print("="*70)
    
    # Filtra resultados validos
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        print("\nNenhum resultado valido encontrado")
        return
    
    # Ordena por score
    sorted_results = sorted(valid_results, key=lambda x: x.get('score', 0), reverse=True)
    
    # Analise comparativa
    print("\n1. COMPARACAO DE SCORES")
    print("-" * 70)
    
    for i, result in enumerate(sorted_results, 1):
        model = result['model_name'].split('/')[-1]
        score = result['score']
        acc1 = result['accuracy_top1']
        acc5 = result['accuracy_top5']
        dist = result['mean_distance']
        time = result['elapsed_time']
        
        print(f"\n{i}. {model}")
        print(f"   Score: {score:.1f}/100")
        print(f"   Acuracia: Top1={acc1:.1f}% | Top5={acc5:.1f}%")
        print(f"   Distancia: {dist:.4f}")
        print(f"   Tempo: {time:.1f}s")
    
    # Analise de trade-offs
    print("\n\n2. TRADE-OFFS")
    print("-" * 70)
    
    best_score = sorted_results[0]
    fastest = min(valid_results, key=lambda x: x.get('elapsed_time', float('inf')))
    best_acc = max(valid_results, key=lambda x: x.get('accuracy_top1', 0))
    best_dist = min(valid_results, key=lambda x: x.get('mean_distance', float('inf')))
    
    print(f"\nMelhor Score Geral:")
    print(f"  {best_score['model_name']}")
    print(f"  Score: {best_score['score']:.1f}/100")
    
    print(f"\nMais Rapido:")
    print(f"  {fastest['model_name']}")
    print(f"  Tempo: {fastest['elapsed_time']:.1f}s")
    print(f"  Score: {fastest['score']:.1f}/100")
    
    print(f"\nMelhor Acuracia:")
    print(f"  {best_acc['model_name']}")
    print(f"  Top-1: {best_acc['accuracy_top1']:.1f}%")
    print(f"  Score: {best_acc['score']:.1f}/100")
    
    print(f"\nMelhor Distancia:")
    print(f"  {best_dist['model_name']}")
    print(f"  Media: {best_dist['mean_distance']:.4f}")
    print(f"  Score: {best_dist['score']:.1f}/100")
    
    # Recomendacoes por cenario
    print("\n\n3. RECOMENDACOES POR CENARIO")
    print("-" * 70)
    
    print("\nCenario 1: PRODUCAO (prioridade: qualidade)")
    print(f"  Modelo: {best_score['model_name']}")
    print(f"  Motivo: Melhor score geral ({best_score['score']:.1f}/100)")
    
    print("\nCenario 2: DESENVOLVIMENTO (prioridade: velocidade)")
    if fastest['score'] > 70:
        print(f"  Modelo: {fastest['model_name']}")
        print(f"  Motivo: Rapido ({fastest['elapsed_time']:.1f}s) e score aceitavel ({fastest['score']:.1f}/100)")
    else:
        print(f"  Modelo: {best_score['model_name']}")
        print(f"  Motivo: Modelo rapido tem score baixo, usar melhor geral")
    
    print("\nCenario 3: ALTA PRECISAO (prioridade: acuracia)")
    print(f"  Modelo: {best_acc['model_name']}")
    print(f"  Motivo: Maior acuracia Top-1 ({best_acc['accuracy_top1']:.1f}%)")
    
    # Analise de confianca
    print("\n\n4. NIVEL DE CONFIANCA")
    print("-" * 70)
    
    if len(sorted_results) > 1:
        first = sorted_results[0]
        second = sorted_results[1]
        diff = first['score'] - second['score']
        
        print(f"\n1o lugar: {first['model_name']}")
        print(f"  Score: {first['score']:.1f}")
        
        print(f"\n2o lugar: {second['model_name']}")
        print(f"  Score: {second['score']:.1f}")
        
        print(f"\nDiferenca: {diff:.1f} pontos")
        
        if diff > 10:
            confidence = "ALTA"
            recommendation = f"Use {first['model_name']} sem hesitacao"
        elif diff > 5:
            confidence = "MEDIA"
            recommendation = f"{first['model_name']} e ligeiramente superior"
        else:
            confidence = "BAIXA"
            recommendation = f"Ambos modelos sao similares, teste em producao:\n      - {first['model_name']}\n      - {second['model_name']}"
        
        print(f"\nConfianca: {confidence}")
        print(f"Recomendacao: {recommendation}")
    
    # Codigo de exemplo
    print("\n\n5. CODIGO PARA IMPLEMENTACAO")
    print("-" * 70)
    
    best = sorted_results[0]
    model_name = best['model_name']
    
    print(f"\nPara usar o modelo recomendado, atualize config.py:")
    print("\n```python")
    print("# config.py")
    print(f"EMBEDDING_MODEL = '{model_name}'")
    print("```")
    
    print("\nOu execute:")
    print(f"sed -i 's/^EMBEDDING_MODEL = .*/EMBEDDING_MODEL = \"{model_name}\"/' /mnt/project/config.py")

def generate_summary_table(results):
    """Gera tabela resumo formatada"""
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        return
    
    print("\n\n" + "="*70)
    print("TABELA RESUMO")
    print("="*70)
    
    # Header
    print("\n{:<45} {:>7} {:>7} {:>8}".format(
        "Modelo", "Score", "Top-1%", "Tempo(s)"
    ))
    print("-" * 70)
    
    # Dados
    sorted_results = sorted(valid_results, key=lambda x: x.get('score', 0), reverse=True)
    
    for result in sorted_results:
        model = result['model_name'].split('/')[-1][:44]
        score = result['score']
        acc1 = result['accuracy_top1']
        time = result['elapsed_time']
        
        print("{:<45} {:>7.1f} {:>7.1f} {:>8.1f}".format(
            model, score, acc1, time
        ))

def main():
    """Funcao principal"""
    print("="*70)
    print("ANALISADOR DE RESULTADOS DO BENCHMARK")
    print("="*70)
    
    # Procura arquivo de resultados mais recente
    import glob
    
    files = glob.glob("benchmark_results_*.json")
    
    if not files:
        print("\nNenhum arquivo de resultados encontrado")
        print("Execute primeiro: python benchmark_embeddings.py")
        return 1
    
    # Usa o mais recente
    latest_file = max(files, key=lambda x: x.split('_')[-1])
    
    print(f"\nArquivo: {latest_file}")
    
    results = load_results(latest_file)
    
    if results:
        analyze_results(results)
        generate_summary_table(results)
        
        print("\n\n" + "="*70)
        print("ANALISE CONCLUIDA")
        print("="*70)
        
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())