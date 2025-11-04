# main.py
# Sistema RAG NCM com modo interativo de consulta

import argparse
from setup import setup_database
from visualization import show_sample_data, show_random_data, show_statistics
from diagnostico.diagnostics import comprehensive_diagnostic
from config import DEFAULT_MODEL


def interactive_mode(collection, prompt_file="system_prompt.txt"):
    """
    Modo interativo de consulta ao sistema RAG NCM.

    Inicia interface de linha de comando para interacao com o sistema.
    Carrega prompt do sistema do arquivo especificado para guiar respostas do LLM.

    Comandos disponiveis:
    - Texto livre: envia query ao RAG que busca NCMs similares e gera resposta
    - 'consulta <descricao>': busca hierarquica de NCMs por descricao
    - 'atributos <codigo_ncm>': lista atributos de um NCM especifico
    - 'stats': exibe estatisticas do banco de dados
    - 'diagnostico': executa relatorio completo de qualidade
    - 'sample <n>': mostra n primeiros registros do banco
    - 'random <n>': mostra n registros aleatorios
    - 'modelos': lista modelos LLM disponiveis
    - 'modelo <nome>': troca modelo LLM atual
    - 'sair': encerra o programa

    Para queries de texto livre:
    - Utiliza busca hierarquica que prioriza items especificos sobre categorias
    - Combina busca vetorial com contexto de atributos
    - Envia resultados para LLM gerar resposta em linguagem natural
    - Respostas sao baseadas apenas no contexto recuperado (RAG)
    """
    from llm_client import chat, get_models, load_system_prompt
    from search import (
        find_ncm_by_description, find_atributos_by_ncm,
        find_ncm_hierarchical, find_ncm_hierarchical_with_context
    )

    print(f"\nCarregando prompt: {prompt_file}")
    load_system_prompt(prompt_file)

    print("\n" + "="*60)
    print("MODO INTERATIVO - RAG NCM COM BUSCA HIERARQUICA")
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
                    print("\nResultados (priorizando items especificos):")
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
    """
    Funcao principal do sistema RAG NCM.

    Processa argumentos da linha de comando:
    - --prompt: arquivo de prompt do sistema (default: system_prompt.txt)
    - --setup-only: apenas configura banco sem entrar em modo interativo
    - --cli: usa modo interativo CLI (antigo)
    - --menu: usa menu principal completo (default)

    Fluxo de execucao:
    1. Configura e indexa banco vetorial (ou reutiliza existente)
    2. Se --setup-only nao especificado, entra em modo de interface
    3. Modo padrao e o menu principal com todas funcionalidades
    4. Modo CLI mantem compatibilidade com versao anterior
    """
    parser = argparse.ArgumentParser(description='Sistema RAG NCM Aprimorado')
    parser.add_argument('--prompt', type=str, default='system_prompt.txt')
    parser.add_argument('--setup-only', action='store_true',
                        help='Apenas configura banco sem entrar em modo interativo')
    parser.add_argument('--cli', action='store_true',
                        help='Usa modo interativo CLI (modo antigo)')
    parser.add_argument('--menu', action='store_true',
                        help='Usa menu principal completo (default)')

    args = parser.parse_args()

    collection = setup_database()

    if not args.setup_only:
        # Se --cli especificado, usa modo antigo
        if args.cli:
            interactive_mode(collection, prompt_file=args.prompt)
        # Caso contrario, usa menu principal (default)
        else:
            from menu import main_menu
            main_menu(collection)

    return collection


if __name__ == "__main__":
    main()
