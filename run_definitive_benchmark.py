#!/usr/bin/env python3
# run_definitive_benchmark.py
# Script para execução definitiva do benchmark com todas as melhorias integradas

"""
BENCHMARK DEFINITIVO DE EMBEDDINGS - RAG NCM

Este script executa o benchmark completo com todas as melhorias:
✓ Ground truth expandido (90+ casos)
✓ Cache de embeddings (acelera re-execuções)
✓ Normalização avançada de textos
✓ Validação de modelos antes de testar
✓ Tratamento robusto de erros
✓ Geração automática da configuração ideal

Uso:
    python run_definitive_benchmark.py [opções]

Opções:
    --no-cache          Desabilita cache (força recálculo)
    --quick             Testa apenas modelo base (para validação rápida)
    --all               Inclui modelo rápido para comparação

Resultado:
    - benchmark_results_*.json       : Resultados completos
    - best_model_config.json         : Configuração JSON do melhor modelo
    - best_model_config.py           : Módulo Python para import direto
"""

import sys
import os
import argparse
from datetime import datetime

# Adiciona diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_embeddings import EmbeddingBenchmark, MODELS_TO_TEST


def print_banner():
    """Banner inicial"""
    print("\n" + "="*80)
    print("  BENCHMARK DEFINITIVO DE MODELOS DE EMBEDDING - RAG NCM")
    print("="*80)
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Versão: 2.0 (com melhorias integradas)")
    print("="*80)


def print_improvements():
    """Lista de melhorias implementadas"""
    print("\n📊 MELHORIAS IMPLEMENTADAS:")
    print("  ✓ Ground truth expandido: 90+ casos (vs 8 anteriores)")
    print("  ✓ Cache de embeddings: acelera 80-90% em re-execuções")
    print("  ✓ Normalização avançada: remove ruído dos textos")
    print("  ✓ Validação prévia: evita erros com modelos inválidos")
    print("  ✓ Auto-configuração: gera setup ideal automaticamente")
    print()


def print_models(models, mode="default"):
    """Lista modelos a serem testados"""
    print(f"\n🔬 MODELOS SELECIONADOS ({mode}):")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    print()


def confirm_execution(models, use_cache):
    """Confirma execução do benchmark"""
    print("\n⚙️  CONFIGURAÇÃO:")
    print(f"  Modelos a testar: {len(models)}")
    print(f"  Cache: {'ATIVO ✓' if use_cache else 'DESATIVADO'}")
    print(f"  Ground truth: 90+ casos de teste")
    print(f"  Tempo estimado: {'~20-40 min' if use_cache else '~3-5 horas'}")
    print()

    try:
        response = input("Deseja continuar? [S/n]: ").strip().lower()
        if response and response not in ['s', 'sim', 'y', 'yes']:
            print("\n❌ Benchmark cancelado pelo usuário")
            return False
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark cancelado pelo usuário")
        return False

    return True


def run_benchmark(use_cache=True, models=None):
    """Executa benchmark com configurações especificadas"""
    if models is None:
        models = MODELS_TO_TEST

    print(f"\n{'='*80}")
    print("INICIANDO BENCHMARK")
    print(f"{'='*80}\n")

    try:
        benchmark = EmbeddingBenchmark(use_cache=use_cache)
        benchmark.load_data()

        # Testa cada modelo
        for i, model_name in enumerate(models, 1):
            print(f"\n{'='*80}")
            print(f"PROGRESSO: {i}/{len(models)} modelos")
            print(f"{'='*80}")
            benchmark.test_model(model_name)

        # Gera relatório comparativo
        benchmark.generate_comparative_report()

        print(f"\n{'='*80}")
        print("✓ BENCHMARK CONCLUÍDO COM SUCESSO!")
        print(f"{'='*80}\n")

        print("📁 ARQUIVOS GERADOS:")
        print("  - benchmark_results_*.json    : Resultados detalhados")
        print("  - best_model_config.json      : Configuração ideal (JSON)")
        print("  - best_model_config.py        : Módulo Python para import")
        print()

        print("💡 PRÓXIMOS PASSOS:")
        print("  1. Revisar best_model_config.json")
        print("  2. Se score >= 80: usar modelo em produção")
        print("  3. Se score < 80: implementar re-ranking (ver PLANO_ACAO.md)")
        print("  4. Testar em ambiente real")
        print()

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrompido pelo usuário")
        print("Resultados parciais podem ter sido salvos")
        return False

    except Exception as e:
        print(f"\n\n❌ ERRO durante benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Execução definitiva do benchmark de embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_definitive_benchmark.py
  python run_definitive_benchmark.py --no-cache
  python run_definitive_benchmark.py --quick
  python run_definitive_benchmark.py --all

Para mais informações: README.md ou PLANO_ACAO.md
        """
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Desabilita cache (força recálculo de todos embeddings)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Modo rápido: testa apenas modelo base (para validação)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Testa todos os modelos incluindo o rápido (all-MiniLM-L6-v2)'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Pula confirmação (auto-confirma execução)'
    )

    args = parser.parse_args()

    # Banner
    print_banner()
    print_improvements()

    # Seleciona modelos
    if args.quick:
        models = ['intfloat/multilingual-e5-base']
        mode = "modo rápido"
    elif args.all:
        models = MODELS_TO_TEST + ['sentence-transformers/all-MiniLM-L6-v2']
        mode = "todos os modelos"
    else:
        models = MODELS_TO_TEST
        mode = "padrão"

    print_models(models, mode)

    # Configurações
    use_cache = not args.no_cache

    # Confirma execução
    if not args.yes:
        if not confirm_execution(models, use_cache):
            sys.exit(0)

    # Executa benchmark
    print("\n🚀 Iniciando benchmark...\n")
    success = run_benchmark(use_cache=use_cache, models=models)

    # Status final
    if success:
        print("\n✓ Script finalizado com sucesso!")
        sys.exit(0)
    else:
        print("\n✗ Script finalizado com erros")
        sys.exit(1)


if __name__ == "__main__":
    main()
