# visualization.py
# Funcoes de visualizacao e diagnostico de dados NCM

import random
from search import find_atributos_by_ncm, find_ncm_by_description


def show_sample_data(collection, n=5):
    """
    Exibe os primeiros N registros NCM do banco com seus detalhes.

    Para cada NCM exibido:
    - Mostra codigo normalizado e descricao
    - Executa busca vetorial usando a propria descricao como query
    - Lista os 3 resultados mais similares com suas distancias
    - Busca e exibe atributos associados (importacao e exportacao)
    - Indica quais atributos sao obrigatorios vs opcionais

    Util para verificar qualidade da indexacao e testar busca vetorial
    com NCMs conhecidos do banco.
    """
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
    """
    Exibe N registros NCM aleatorios do banco para verificacao de qualidade.

    Seleciona aleatoriamente NCMs do banco e para cada um:
    - Mostra codigo normalizado e descricao
    - Executa busca vetorial usando a descricao
    - Lista os 2 resultados mais similares
    - Exibe atributos de importacao e exportacao com seus detalhes

    Util para inspecionar diferentes partes do banco e identificar
    padroes ou problemas de indexacao em registros variados.
    """
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
    """
    Exibe estatisticas gerais do banco vetorial.

    Conta e exibe:
    - Total de documentos indexados no banco
    - Quantidade de documentos do tipo NCM
    - Quantidade de documentos do tipo atributo

    Util para verificacao rapida do estado do banco apos indexacao.
    """
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
