# menu.py
# Menu principal - orquestra funcionalidades existentes

import sys
import os


def clear_screen():
    """Limpa tela"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu():
    """Exibe menu"""
    print("\n" + "="*70)
    print(" "*20 + "SISTEMA RAG NCM - MENU PRINCIPAL")
    print("="*70)
    print("\n[INTERFACES]")
    print("  1. Interface Web (Gradio)")
    print("  2. Modo Interativo CLI")
    print("\n[VISUALIZAÇÃO]")
    print("  3. Primeiros N Registros    4. Registros Aleatórios")
    print("  5. Estatísticas do Banco")
    print("\n[DIAGNÓSTICOS]")
    print("  6. Diagnóstico Básico       7. Relatório Completo")
    print("  8. Análise Distâncias       9. Análise Cobertura")
    print(" 10. Ground Truth            11. Qualidade Embeddings")
    print(" 12. Qualidade Textos")
    print("\n[BENCHMARKS]")
    print(" 13. Benchmark Completo      14. Analisar Resultados")
    print(" 15. Benchmark Rápido")
    print("\n[CONFIGURAÇÃO]")
    print(" 16. Reconfigurar Banco      17. Limpar Cache")
    print(" 18. Limpar Cache Parcial    19. Info Sistema")
    print("\n[CONSULTAS]")
    print(" 20. Consulta NCM            21. Consulta Atributos")
    print(" 22. Busca com LLM")
    print("\n  0. Sair")
    print("="*70)
    print("\n💡 DICA: Digite número, 'consulta <texto>' ou texto livre para busca LLM")


def pause():
    """Pausa"""
    input("\nPressione ENTER...")


def get_int(prompt, default):
    """Input inteiro"""
    try:
        v = input(prompt).strip()
        return int(v) if v else default
    except:
        return default


# === HANDLERS ===

def option_1(c):
    from run_chatbot import launch_ui
    print("\nIniciando Interface Web...")
    launch_ui(c, share=False)


def option_2(c):
    from main import interactive_mode
    interactive_mode(c)


def option_3(c):
    from visualization import show_sample_data
    show_sample_data(c, get_int("Quantos? [5]: ", 5))
    pause()


def option_4(c):
    from visualization import show_random_data
    show_random_data(c, get_int("Quantos? [5]: ", 5))
    pause()


def option_5(c):
    from visualization import show_statistics
    show_statistics(c)
    pause()


def option_6(c):
    from benchmark.diagnostics import comprehensive_diagnostic
    comprehensive_diagnostic(c)
    pause()


def option_7(c):
    from benchmark.diagnostics import comprehensive_quality_report
    print("\n⏱️  Alguns minutos...")
    comprehensive_quality_report(c)
    pause()


def option_8(c):
    from benchmark.diagnostics import analyze_distance_distribution
    queries = ["cafe", "soja", "carne", "acucar", "telefone", "arroz"]
    analyze_distance_distribution(c, queries)
    pause()


def option_9(c):
    from benchmark.diagnostics import analyze_attribute_coverage
    analyze_attribute_coverage(c)
    pause()


def option_10(c):
    from benchmark.diagnostics import evaluate_known_ncm_queries
    evaluate_known_ncm_queries(c)
    pause()


def option_11(c):
    from benchmark.diagnostics import analyze_embedding_quality
    analyze_embedding_quality(c)
    pause()


def option_12(c):
    from benchmark.diagnostics import analyze_indexed_text_quality
    analyze_indexed_text_quality(c, get_int("Quantos docs? [10]: ", 10))
    pause()


def option_13(c):
    if input("\n⚠️  Leva HORAS. Continuar? [s/N]: ").lower() not in ['s', 'sim', 'y', 'yes']:
        return
    from benchmark.benchmark_embeddings import EmbeddingBenchmark
    EmbeddingBenchmark().run_benchmark()
    pause()


def option_14(c):
    import subprocess
    subprocess.run([sys.executable, "benchmark/analyze_benchmark_results.py"])
    pause()


def option_15(c):
    if input("\n⚠️  30-60 min. Continuar? [s/N]: ").lower() not in ['s', 'sim', 'y', 'yes']:
        return
    from benchmark.benchmark_embeddings import EmbeddingBenchmark, MODELS_TO_TEST
    b = EmbeddingBenchmark()
    b.load_data()
    for m in MODELS_TO_TEST[:3]:
        b.test_model(m)
    b.generate_comparative_report()
    pause()


def option_16(c):
    if input("\n⚠️  APAGA banco. Continuar? [s/N]: ").lower() not in ['s', 'sim', 'y', 'yes']:
        return
    import config
    orig = config.CLEAR_DB
    config.CLEAR_DB = True
    from setup import setup_database
    new_c = setup_database()
    config.CLEAR_DB = orig
    pause()
    return new_c


def option_17(c):
    import subprocess
    subprocess.run([sys.executable, "benchmark/clear_cache.py"])
    pause()


def option_18(c):
    m = input("\nModelo (ex: 'e5'): ").strip()
    if m:
        import subprocess
        subprocess.run([sys.executable, "benchmark/clear_cache.py", "--model", m])
    pause()


def option_19(c):
    from config import EMBEDDING_MODEL, DEFAULT_MODEL, NCM_FILE, ATRIBUTOS_FILE
    print("\n" + "="*70)
    print("INFORMAÇÕES DO SISTEMA")
    print("="*70)
    print(f"\n[CONFIG]")
    print(f"  Embedding: {EMBEDDING_MODEL}")
    print(f"  LLM: {DEFAULT_MODEL}")
    print(f"  NCM: {NCM_FILE}")
    print(f"  Atributos: {ATRIBUTOS_FILE}")
    print(f"\n[BANCO]")
    print(f"  Total: {c.count()} docs")
    try:
        print(f"  NCMs: {len(c.get(where={'tipo': 'ncm'}, limit=20000)['ids'])}")
    except:
        pass
    try:
        print(f"  Atributos: {len(c.get(where={'tipo': 'atributo'}, limit=60000)['ids'])}")
    except:
        pass
    pause()


def option_20(c):
    from search import find_ncm_hierarchical
    desc = input("\nDescrição: ").strip()
    if not desc:
        return
    results = find_ncm_hierarchical(c, desc, k=get_int("Resultados [5]: ", 5), prefer_items=True)
    if results:
        print(f"\n{len(results)} resultados:\n")
        for i, r in enumerate(results, 1):
            cod = r.get('codigo_normalizado') or r.get('codigo')
            print(f"{i}. NCM {cod} [{r.get('nivel', '?')}]")
            print(f"   {r['descricao'][:60]}")
            print(f"   Dist: {r['distance']:.4f}\n")
    else:
        print("\nNenhum resultado.")
    pause()


def option_21(c):
    from search import find_atributos_by_ncm
    ncm = input("\nCódigo NCM: ").strip()
    if not ncm:
        return
    results = find_atributos_by_ncm(c, ncm, k=50)
    if results:
        imp = [r for r in results if r['modalidade'] == 'Importacao']
        exp = [r for r in results if r['modalidade'] == 'Exportacao']
        print(f"\nTotal: {len(results)} atributos")
        if imp:
            print(f"\n[IMPORTAÇÃO] {len(imp)}:")
            for r in imp[:10]:
                print(f"  {'[OBRIG]' if r['obrigatorio'] else '[OPC]'} {r['atributo_codigo']}")
        if exp:
            print(f"\n[EXPORTAÇÃO] {len(exp)}:")
            for r in exp[:10]:
                print(f"  {'[OBRIG]' if r['obrigatorio'] else '[OPC]'} {r['atributo_codigo']}")
    else:
        print("\nNenhum atributo.")
    pause()


def option_22(c):
    from llm_client import chat, get_models
    from search import find_ncm_hierarchical_with_context
    from config import DEFAULT_MODEL
    models = get_models()
    model = DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else DEFAULT_MODEL)
    print(f"\nModelo: {model}")
    query = input("Pergunta: ").strip()
    if not query:
        return
    print("\nGerando...\n")
    result = ""
    for chunk in chat(c, query, model, find_ncm_hierarchical_with_context):
        result = chunk
    print(f"\n{result}\n")
    pause()


# === BUSCA INTELIGENTE ===

def handle_consulta(c, descricao):
    """Busca vetorial rápida via 'consulta <texto>'"""
    from search import find_ncm_hierarchical
    print(f"\n{'='*70}")
    print(f"BUSCA VETORIAL: {descricao}")
    print(f"{'='*70}")
    results = find_ncm_hierarchical(c, descricao, k=5, prefer_items=True)
    if results:
        print(f"\n{len(results)} resultados:\n")
        for i, r in enumerate(results, 1):
            cod = r.get('codigo_normalizado') or r.get('codigo')
            print(f"{i}. NCM {cod} [{r.get('nivel', '?')}]")
            print(f"   {r['descricao']}")
            print(f"   Dist: {r['distance']:.4f}\n")
    else:
        print("\nNenhum resultado.")
    pause()


def handle_text_search(c, query):
    """Busca com LLM via texto livre"""
    from llm_client import chat, get_models
    from search import find_ncm_hierarchical_with_context
    from config import DEFAULT_MODEL
    models = get_models()
    model = DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else DEFAULT_MODEL)
    print(f"\n{'='*70}")
    print("BUSCA COM LLM")
    print(f"{'='*70}")
    print(f"Query: {query}")
    print(f"Modelo: {model}")
    print(f"{'='*70}\n")
    result = ""
    for chunk in chat(c, query, model, find_ncm_hierarchical_with_context):
        result = chunk
    print(f"\n{result}\n")
    pause()


# === MAIN ===

def main_menu(collection=None):
    """Menu principal com busca inteligente"""
    if collection is None:
        print("Carregando banco...")
        from setup import setup_database
        collection = setup_database()

    handlers = {
        '1': option_1, '2': option_2, '3': option_3, '4': option_4,
        '5': option_5, '6': option_6, '7': option_7, '8': option_8,
        '9': option_9, '10': option_10, '11': option_11, '12': option_12,
        '13': option_13, '14': option_14, '15': option_15, '16': option_16,
        '17': option_17, '18': option_18, '19': option_19, '20': option_20,
        '21': option_21, '22': option_22
    }

    while True:
        clear_screen()
        print_menu()
        choice = input("\nOpção: ").strip()

        if not choice:
            continue

        if choice == '0':
            print("\nEncerrando...")
            sys.exit(0)

        # Busca inteligente: detecta "consulta <texto>"
        if choice.lower().startswith('consulta '):
            descricao = choice[9:].strip()
            if descricao:
                try:
                    handle_consulta(collection, descricao)
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
                    import traceback
                    traceback.print_exc()
                    pause()
            continue

        # Handler de menu numérico
        if choice in handlers:
            try:
                result = handlers[choice](collection)
                if result is not None:
                    collection = result
            except KeyboardInterrupt:
                print("\n\nCancelado.")
                pause()
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                import traceback
                traceback.print_exc()
                pause()
        # Busca inteligente: texto livre vira busca com LLM
        elif not choice.isdigit():
            try:
                handle_text_search(collection, choice)
            except KeyboardInterrupt:
                print("\n\nCancelado.")
                pause()
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                import traceback
                traceback.print_exc()
                pause()
        else:
            print(f"\n❌ Opção inválida: {choice}")
            pause()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nEncerrando...")
        sys.exit(0)
