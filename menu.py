# menu.py
# Menu principal unificado com todas funcionalidades do sistema RAG NCM

import sys
import os
from typing import Optional


def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Imprime cabeçalho do menu"""
    print("\n" + "="*70)
    print(" "*20 + "SISTEMA RAG NCM")
    print(" "*15 + "Menu Principal de Funcionalidades")
    print("="*70)


def print_menu():
    """Exibe menu principal com todas funcionalidades"""
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│                      INTERFACES DE USUÁRIO                          │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│  1. Interface Web (Gradio) - Chat interativo visual                │")
    print("│  2. Modo Interativo CLI - Chat via linha de comando                │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                      VISUALIZAÇÃO DE DADOS                          │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│  3. Mostrar Primeiros N Registros - Amostra de dados indexados     │")
    print("│  4. Mostrar Registros Aleatórios - Inspeção randômica              │")
    print("│  5. Estatísticas do Banco - Contagem e métricas gerais             │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                   DIAGNÓSTICOS E QUALIDADE                          │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│  6. Diagnóstico Básico - Verificação rápida do sistema             │")
    print("│  7. Relatório Completo de Qualidade - Análise detalhada RAG        │")
    print("│  8. Análise de Distâncias - Distribuição de similaridade           │")
    print("│  9. Análise de Cobertura - Estatísticas de atributos NCM           │")
    print("│ 10. Avaliar Ground Truth - Teste com casos conhecidos              │")
    print("│ 11. Qualidade de Embeddings - Análise do modelo atual              │")
    print("│ 12. Qualidade de Textos - Inspeção de documentos indexados         │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                         BENCHMARKS                                  │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│ 13. Executar Benchmark de Embeddings - Testar múltiplos modelos    │")
    print("│ 14. Analisar Resultados de Benchmark - Comparar modelos testados   │")
    print("│ 15. Benchmark Rápido - Teste com poucos modelos (mais rápido)      │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                    CONFIGURAÇÃO E MANUTENÇÃO                        │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│ 16. Reconfigurar Banco de Dados - Reindexar tudo do zero           │")
    print("│ 17. Limpar Cache de Embeddings - Remover cache corrompido          │")
    print("│ 18. Limpar Cache (Parcial) - Remover cache de modelo específico    │")
    print("│ 19. Informações do Sistema - Config, modelos, arquivos             │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                           CONSULTAS                                 │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│ 20. Consulta Rápida NCM - Busca por descrição (hierárquica)        │")
    print("│ 21. Consulta Atributos - Busca atributos de um código NCM          │")
    print("│ 22. Busca com LLM - Query completa com resposta gerada             │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│                            SAIR                                     │")
    print("├─────────────────────────────────────────────────────────────────────┤")
    print("│  0. Sair do Sistema                                                 │")
    print("└─────────────────────────────────────────────────────────────────────┘")


def launch_gradio_interface(collection):
    """Lança interface Gradio"""
    try:
        from run_chatbot import launch_ui
        print("\n" + "="*70)
        print("INICIANDO INTERFACE WEB (GRADIO)")
        print("="*70)
        print("\nAguarde enquanto a interface é carregada...")
        print("Uma URL será exibida abaixo. Abra-a no navegador.\n")
        launch_ui(collection, share=False)
    except Exception as e:
        print(f"\nErro ao iniciar interface Gradio: {e}")
        print("Verifique se o Gradio está instalado: pip install gradio")
        input("\nPressione ENTER para continuar...")


def launch_interactive_cli(collection):
    """Lança modo interativo CLI"""
    try:
        from main import interactive_mode
        print("\n" + "="*70)
        print("INICIANDO MODO INTERATIVO CLI")
        print("="*70)
        interactive_mode(collection)
    except Exception as e:
        print(f"\nErro ao iniciar modo interativo: {e}")
        input("\nPressione ENTER para continuar...")


def show_sample(collection):
    """Mostra primeiros N registros"""
    try:
        from visualization import show_sample_data
        n = input("\nQuantos registros mostrar? [padrão: 5]: ").strip()
        n = int(n) if n else 5
        show_sample_data(collection, n)
    except ValueError:
        print("Número inválido. Usando padrão (5)")
        show_sample_data(collection, 5)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def show_random(collection):
    """Mostra registros aleatórios"""
    try:
        from visualization import show_random_data
        n = input("\nQuantos registros aleatórios? [padrão: 5]: ").strip()
        n = int(n) if n else 5
        show_random_data(collection, n)
    except ValueError:
        print("Número inválido. Usando padrão (5)")
        show_random_data(collection, 5)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def show_stats(collection):
    """Mostra estatísticas do banco"""
    try:
        from visualization import show_statistics
        show_statistics(collection)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def run_basic_diagnostic(collection):
    """Executa diagnóstico básico"""
    try:
        from benchmark.diagnostics import comprehensive_diagnostic
        comprehensive_diagnostic(collection)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def run_quality_report(collection):
    """Executa relatório completo de qualidade"""
    try:
        from benchmark.diagnostics import comprehensive_quality_report
        print("\n" + "="*70)
        print("Este relatório pode levar alguns minutos...")
        print("="*70)
        comprehensive_quality_report(collection)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def analyze_distances(collection):
    """Analisa distribuição de distâncias"""
    try:
        from benchmark.diagnostics import analyze_distance_distribution

        sample_queries = [
            "cafe torrado", "soja", "carne bovina", "acucar",
            "telefone celular", "arroz", "leite", "computador"
        ]

        print("\n" + "="*70)
        print("Analisando distribuição de distâncias...")
        print("="*70)

        distances, query_results = analyze_distance_distribution(collection, sample_queries)

        if not distances:
            print("\nNenhum resultado obtido.")
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def analyze_coverage(collection):
    """Analisa cobertura de atributos"""
    try:
        from benchmark.diagnostics import analyze_attribute_coverage
        analyze_attribute_coverage(collection)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def evaluate_ground_truth(collection):
    """Avalia queries com ground truth"""
    try:
        from benchmark.diagnostics import evaluate_known_ncm_queries
        print("\n" + "="*70)
        print("Avaliando com casos de ground truth...")
        print("="*70)
        accuracy, top1_acc, results = evaluate_known_ncm_queries(collection)
        print(f"\n\nRESUMO:")
        print(f"  Acurácia Top-5: {accuracy:.1f}%")
        print(f"  Acurácia Top-1: {top1_acc:.1f}%")
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def analyze_embeddings_quality(collection):
    """Analisa qualidade dos embeddings"""
    try:
        from benchmark.diagnostics import analyze_embedding_quality
        analyze_embedding_quality(collection)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def analyze_text_quality(collection):
    """Analisa qualidade dos textos indexados"""
    try:
        from benchmark.diagnostics import analyze_indexed_text_quality
        n = input("\nQuantos documentos analisar? [padrão: 10]: ").strip()
        n = int(n) if n else 10
        analyze_indexed_text_quality(collection, n_samples=n)
    except ValueError:
        print("Número inválido. Usando padrão (10)")
        analyze_indexed_text_quality(collection, 10)
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def run_embedding_benchmark():
    """Executa benchmark de embeddings"""
    try:
        print("\n" + "="*70)
        print("BENCHMARK DE MODELOS DE EMBEDDING")
        print("="*70)
        print("\n⚠️  ATENÇÃO: Este processo pode levar VÁRIAS HORAS!")
        print("    - Testará múltiplos modelos de embedding")
        print("    - Cada modelo leva 5-15 minutos")
        print("    - Resultados serão salvos em arquivos JSON")

        confirm = input("\nDeseja continuar? [s/N]: ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return

        from benchmark.benchmark_embeddings import EmbeddingBenchmark
        benchmark = EmbeddingBenchmark()
        benchmark.run_benchmark()

        print("\n" + "="*70)
        print("BENCHMARK CONCLUÍDO!")
        print("="*70)
        print("\nResultados salvos. Use a opção 14 para analisar.")

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def analyze_benchmark_results():
    """Analisa resultados de benchmark"""
    try:
        import subprocess
        print("\n" + "="*70)
        print("ANÁLISE DE RESULTADOS DE BENCHMARK")
        print("="*70)
        subprocess.run([sys.executable, "benchmark/analyze_benchmark_results.py"])
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def run_quick_benchmark():
    """Executa benchmark rápido com poucos modelos"""
    try:
        print("\n" + "="*70)
        print("BENCHMARK RÁPIDO")
        print("="*70)
        print("\nEste modo testa apenas 2-3 modelos selecionados.")
        print("Tempo estimado: 30-60 minutos")

        confirm = input("\nDeseja continuar? [s/N]: ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return

        from benchmark.benchmark_embeddings import EmbeddingBenchmark, MODELS_TO_TEST

        # Seleciona apenas os 3 primeiros modelos
        quick_models = MODELS_TO_TEST[:3]

        print(f"\nModelos a serem testados:")
        for i, model in enumerate(quick_models, 1):
            print(f"  {i}. {model}")

        benchmark = EmbeddingBenchmark()
        benchmark.load_data()

        # Sobrescreve lista de modelos
        original_models = MODELS_TO_TEST.copy()
        MODELS_TO_TEST.clear()
        MODELS_TO_TEST.extend(quick_models)

        for model in quick_models:
            benchmark.test_model(model)

        benchmark.generate_comparative_report()

        # Restaura lista original
        MODELS_TO_TEST.clear()
        MODELS_TO_TEST.extend(original_models)

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def reconfigure_database():
    """Reconfigura banco de dados"""
    try:
        print("\n" + "="*70)
        print("RECONFIGURAR BANCO DE DADOS")
        print("="*70)
        print("\n⚠️  ATENÇÃO: Esta operação irá:")
        print("    - Apagar o banco de dados atual")
        print("    - Reindexar todos os documentos")
        print("    - Pode levar vários minutos")

        confirm = input("\nDeseja continuar? [s/N]: ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return

        # Atualiza config temporariamente
        import config
        original_clear_db = config.CLEAR_DB
        config.CLEAR_DB = True

        from setup import setup_database
        collection = setup_database()

        # Restaura config
        config.CLEAR_DB = original_clear_db

        print("\n" + "="*70)
        print("RECONFIGURAÇÃO CONCLUÍDA!")
        print("="*70)

        return collection

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def clear_embeddings_cache():
    """Limpa cache de embeddings"""
    try:
        import subprocess
        print("\n" + "="*70)
        print("LIMPAR CACHE DE EMBEDDINGS")
        print("="*70)
        subprocess.run([sys.executable, "benchmark/clear_cache.py"])
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def clear_embeddings_cache_partial():
    """Limpa cache parcial (por modelo)"""
    try:
        model_filter = input("\nNome do modelo a remover (ex: 'e5', 'bge'): ").strip()
        if not model_filter:
            print("Nome inválido. Operação cancelada.")
            return

        import subprocess
        subprocess.run([sys.executable, "benchmark/clear_cache.py", "--model", model_filter])
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def show_system_info(collection):
    """Mostra informações do sistema"""
    try:
        from config import (
            EMBEDDING_MODEL, DEFAULT_MODEL, NCM_FILE,
            ATRIBUTOS_FILE, BATCH_SIZE, INDEX_ONLY_ITEMS
        )

        print("\n" + "="*70)
        print("INFORMAÇÕES DO SISTEMA")
        print("="*70)

        print("\n[CONFIGURAÇÕES]")
        print(f"  Modelo de Embedding: {EMBEDDING_MODEL}")
        print(f"  Modelo LLM Padrão: {DEFAULT_MODEL}")
        print(f"  Arquivo NCM: {NCM_FILE}")
        print(f"  Arquivo Atributos: {ATRIBUTOS_FILE}")
        print(f"  Batch Size: {BATCH_SIZE}")
        print(f"  Indexar Apenas Items: {INDEX_ONLY_ITEMS}")

        print("\n[BANCO DE DADOS]")
        print(f"  Total de Documentos: {collection.count()}")

        try:
            ncm_count = len(collection.get(where={"tipo": "ncm"}, limit=20000)['ids'])
            print(f"  Documentos NCM: {ncm_count}")
        except:
            print(f"  Documentos NCM: N/A")

        try:
            attr_count = len(collection.get(where={"tipo": "atributo"}, limit=60000)['ids'])
            print(f"  Documentos Atributo: {attr_count}")
        except:
            print(f"  Documentos Atributo: N/A")

        print("\n[ARQUIVOS]")
        print(f"  NCM existe: {'Sim' if os.path.exists(NCM_FILE) else 'Não'}")
        print(f"  Atributos existe: {'Sim' if os.path.exists(ATRIBUTOS_FILE) else 'Não'}")

        # Verifica cache
        cache_dir = "cache/embeddings"
        if os.path.exists(cache_dir):
            import glob
            pkl_files = glob.glob(f"{cache_dir}/*.pkl")
            print(f"\n[CACHE]")
            print(f"  Arquivos em cache: {len(pkl_files)}")

            if pkl_files:
                cache_size = sum(os.path.getsize(f) for f in pkl_files)
                print(f"  Tamanho total: {cache_size / (1024*1024):.2f} MB")

    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def quick_ncm_query(collection):
    """Consulta rápida de NCM"""
    try:
        from search import find_ncm_hierarchical

        descricao = input("\nDescrição do produto: ").strip()
        if not descricao:
            print("Descrição vazia. Operação cancelada.")
            return

        k = input("Quantos resultados? [padrão: 5]: ").strip()
        k = int(k) if k else 5

        print(f"\n{'='*70}")
        print("BUSCANDO...")
        print(f"{'='*70}")

        results = find_ncm_hierarchical(collection, descricao, k=k, prefer_items=True)

        if results:
            print(f"\nEncontrados {len(results)} resultados:\n")
            for i, r in enumerate(results, 1):
                cod = r.get('codigo_normalizado') or r.get('codigo')
                desc = r['descricao']
                dist = r['distance']
                nivel = r.get('nivel', 'desconhecido')
                print(f"{i}. NCM {cod} [{nivel}]")
                print(f"   Distância: {dist:.4f}")
                print(f"   Descrição: {desc}")
                print()
        else:
            print("\nNenhum resultado encontrado.")

    except ValueError:
        print("Número inválido.")
    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def quick_attributes_query(collection):
    """Consulta atributos de NCM"""
    try:
        from search import find_atributos_by_ncm

        ncm_code = input("\nCódigo NCM: ").strip()
        if not ncm_code:
            print("Código vazio. Operação cancelada.")
            return

        print(f"\n{'='*70}")
        print(f"BUSCANDO ATRIBUTOS: {ncm_code}")
        print(f"{'='*70}")

        results = find_atributos_by_ncm(collection, ncm_code, k=50)

        if results:
            imp = [r for r in results if r['modalidade'] == 'Importacao']
            exp = [r for r in results if r['modalidade'] == 'Exportacao']

            print(f"\nTotal: {len(results)} atributos")

            if imp:
                obr_count = sum(1 for a in imp if a['obrigatorio'])
                print(f"\n[IMPORTAÇÃO] ({len(imp)} atributos, {obr_count} obrigatórios)")
                for r in imp[:10]:
                    obr = "[OBRIG]" if r['obrigatorio'] else "[OPC]  "
                    print(f"  {obr} {r['atributo_codigo']}")
                if len(imp) > 10:
                    print(f"  ... e mais {len(imp)-10}")

            if exp:
                obr_count = sum(1 for a in exp if a['obrigatorio'])
                print(f"\n[EXPORTAÇÃO] ({len(exp)} atributos, {obr_count} obrigatórios)")
                for r in exp[:10]:
                    obr = "[OBRIG]" if r['obrigatorio'] else "[OPC]  "
                    print(f"  {obr} {r['atributo_codigo']}")
                if len(exp) > 10:
                    print(f"  ... e mais {len(exp)-10}")
        else:
            print("\nNenhum atributo encontrado.")

    except Exception as e:
        print(f"\nErro: {e}")
    finally:
        input("\nPressione ENTER para continuar...")


def llm_query(collection):
    """Consulta com resposta do LLM"""
    try:
        from llm_client import chat, get_models
        from search import find_ncm_hierarchical_with_context
        from config import DEFAULT_MODEL

        models = get_models()
        current_model = DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else DEFAULT_MODEL)

        print(f"\n{'='*70}")
        print("CONSULTA COM LLM")
        print(f"{'='*70}")
        print(f"\nModelo atual: {current_model}")

        change = input("Trocar modelo? [s/N]: ").strip().lower()
        if change in ['s', 'sim', 'y', 'yes']:
            print("\nModelos disponíveis:")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")

            choice = input("\nEscolha (número): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    current_model = models[idx]
                    print(f"Modelo alterado para: {current_model}")
            except:
                print("Escolha inválida. Mantendo modelo atual.")

        query = input("\nSua pergunta: ").strip()
        if not query:
            print("Pergunta vazia. Operação cancelada.")
            return

        print(f"\n{'='*70}")
        print("GERANDO RESPOSTA...")
        print(f"{'='*70}\n")

        result = ""
        for chunk in chat(collection, query, current_model, find_ncm_hierarchical_with_context):
            result = chunk

        print(f"[RESPOSTA]\n{result}\n")

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def perform_quick_search(collection, descricao):
    """Executa busca vetorial rápida a partir do menu principal"""
    try:
        from search import find_ncm_hierarchical

        print(f"\n{'='*70}")
        print(f"BUSCA VETORIAL: {descricao}")
        print(f"{'='*70}")

        results = find_ncm_hierarchical(collection, descricao, k=5, prefer_items=True)

        if results:
            print(f"\nEncontrados {len(results)} resultados:\n")
            for i, r in enumerate(results, 1):
                cod = r.get('codigo_normalizado') or r.get('codigo')
                desc = r['descricao']
                dist = r['distance']
                nivel = r.get('nivel', 'desconhecido')
                print(f"{i}. NCM {cod} [{nivel}]")
                print(f"   Distância: {dist:.4f}")
                print(f"   Descrição: {desc}")
                print()
        else:
            print("\nNenhum resultado encontrado.")

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def perform_llm_search(collection, query):
    """Executa busca com LLM a partir do menu principal"""
    try:
        from llm_client import chat, get_models
        from search import find_ncm_hierarchical_with_context
        from config import DEFAULT_MODEL

        models = get_models()
        current_model = DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else DEFAULT_MODEL)

        print(f"\n{'='*70}")
        print("BUSCA COM LLM")
        print(f"{'='*70}")
        print(f"Query: {query}")
        print(f"Modelo: {current_model}")
        print(f"{'='*70}\n")

        result = ""
        for chunk in chat(collection, query, current_model, find_ncm_hierarchical_with_context):
            result = chunk

        print(f"[RESPOSTA]\n{result}\n")

    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione ENTER para continuar...")


def main_menu(collection: Optional = None):
    """Menu principal com busca inteligente"""

    # Se collection não foi fornecida, carrega
    if collection is None:
        print("Carregando banco de dados...")
        from setup import setup_database
        collection = setup_database()

    while True:
        clear_screen()
        print_header()
        print_menu()

        print("\n💡 DICA: Você pode digitar:")
        print("   - Um número (0-22) para acessar uma opção do menu")
        print("   - 'consulta <descrição>' para busca vetorial rápida")
        print("   - Qualquer texto para busca com LLM")

        choice = input("\nEscolha uma opção ou digite sua consulta: ").strip()

        if not choice:
            continue

        # Verifica se é um número (opção de menu)
        if choice.isdigit():
            menu_option = choice

            if menu_option == "0":
                print("\n" + "="*70)
                print("Encerrando sistema...")
                print("="*70)
                sys.exit(0)

            elif menu_option == "1":
                launch_gradio_interface(collection)

            elif menu_option == "2":
                launch_interactive_cli(collection)

            elif menu_option == "3":
                show_sample(collection)

            elif menu_option == "4":
                show_random(collection)

            elif menu_option == "5":
                show_stats(collection)

            elif menu_option == "6":
                run_basic_diagnostic(collection)

            elif menu_option == "7":
                run_quality_report(collection)

            elif menu_option == "8":
                analyze_distances(collection)

            elif menu_option == "9":
                analyze_coverage(collection)

            elif menu_option == "10":
                evaluate_ground_truth(collection)

            elif menu_option == "11":
                analyze_embeddings_quality(collection)

            elif menu_option == "12":
                analyze_text_quality(collection)

            elif menu_option == "13":
                run_embedding_benchmark()

            elif menu_option == "14":
                analyze_benchmark_results()

            elif menu_option == "15":
                run_quick_benchmark()

            elif menu_option == "16":
                new_collection = reconfigure_database()
                if new_collection:
                    collection = new_collection

            elif menu_option == "17":
                clear_embeddings_cache()

            elif menu_option == "18":
                clear_embeddings_cache_partial()

            elif menu_option == "19":
                show_system_info(collection)

            elif menu_option == "20":
                quick_ncm_query(collection)

            elif menu_option == "21":
                quick_attributes_query(collection)

            elif menu_option == "22":
                llm_query(collection)

            else:
                print("\n❌ Opção inválida! Escolha um número entre 0 e 22.")
                input("\nPressione ENTER para continuar...")

        # Verifica se é uma consulta vetorial
        elif choice.lower().startswith('consulta '):
            descricao = choice[9:].strip()
            if descricao:
                perform_quick_search(collection, descricao)
            else:
                print("\n❌ Descrição vazia após 'consulta'.")
                input("\nPressione ENTER para continuar...")

        # Caso contrário, é uma busca com LLM
        else:
            perform_llm_search(collection, choice)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nEncerrando sistema...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
