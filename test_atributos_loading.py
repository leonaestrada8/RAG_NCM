"""
Script de teste para validar carregamento de atributos
"""

import os
# Desabilita normalização para ver texto original
os.environ['DISABLE_NORMALIZATION'] = '1'

from data_loader import (
    load_ncm_data,
    load_atributos_data,
    create_atributos_dict,
    build_ncm_hierarchy,
    create_enriched_ncm_text
)

print("="*70)
print("TESTE DE CARREGAMENTO DE ATRIBUTOS")
print("="*70)

# 1. Carrega dados
print("\n1. Carregando NCM...")
ncm_data = load_ncm_data()
print(f"   Total NCMs: {len(ncm_data)}")

print("\n2. Carregando atributos...")
atributos_data = load_atributos_data()
print(f"   Total items no JSON: {len(atributos_data.get('listaNcm', []))}")

print("\n3. Criando dicionário de atributos...")
atributos_dict = create_atributos_dict(atributos_data)
print(f"   Total no dicionário: {len(atributos_dict)}")

if len(atributos_dict) > 0:
    print("\n4. Mostrando 5 primeiros códigos no dicionário:")
    for i, (codigo, attrs) in enumerate(list(atributos_dict.items())[:5]):
        print(f"   {i+1}. Código: '{codigo}' -> {len(attrs)} atributos")

    print("\n5. Testando enriquecimento de documentos...")
    hierarchy = build_ncm_hierarchy(ncm_data)

    # Pega primeiros 20 NCMs para ter mais chances
    enriched_count = 0
    for idx, row in ncm_data.head(20).iterrows():
        codigo_norm = row['CódigoNormalizado']
        tem_atributo = codigo_norm in atributos_dict

        doc = create_enriched_ncm_text(row, hierarchy, atributos_dict)

        print(f"   NCM {codigo_norm}: tem_atributo={tem_atributo}, ", end="")

        if doc and "Atributos:" in doc:
            enriched_count += 1
            print("ENRIQUECIDO OK")
        elif tem_atributo:
            print("TEM atributo mas NAO enriqueceu")
        else:
            print("nao tem atributo (ok)")

    print(f"\n   Total enriquecidos (de 10 testados): {enriched_count}")

    if enriched_count == 0:
        print("\n   [PROBLEMA] Nenhum NCM foi enriquecido com atributos!")
        print("   Investigando mismatch de códigos...")

        # Compara formatos
        print("\n6. Comparando formato de códigos:")
        sample_ncm_codes = ncm_data['CódigoNormalizado'].head(5).tolist()
        sample_attr_codes = list(atributos_dict.keys())[:5]

        print(f"   Códigos NCM (5 primeiros): {sample_ncm_codes}")
        print(f"   Códigos Atributos (5 primeiros): {sample_attr_codes}")

        # Testa se algum match direto
        matches = 0
        for ncm_code in sample_ncm_codes:
            if ncm_code in atributos_dict:
                matches += 1

        print(f"   Matches diretos: {matches}/5")
else:
    print("\n[ERRO] Dicionário de atributos está vazio!")
    print("Verifique se o arquivo ATRIBUTOS_POR_NCM_2025_09_30.json existe e está correto")

print("\n" + "="*70)
print("FIM DO TESTE")
print("="*70)
