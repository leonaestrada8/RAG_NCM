#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar melhorias no RAG NCM
"""

import sys
import os

# Adiciona o diretório raiz do projeto ao path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import pad_ncm_code, normalize_ncm_code, detect_ncm_level

def test_pad_ncm_code():
    """Testa a função de padding corrigida"""
    print("="*60)
    print("TESTE 1: Padding de Códigos NCM")
    print("="*60)

    test_cases = [
        ("01", "01000000", "Capítulo"),
        ("0101", "01010000", "Posição"),
        ("010121", "01012100", "Subposição"),
        ("01012100", "01012100", "Item completo"),
        ("0202", "02020000", "Posição - Carnes bovinas"),
        ("020220", "02022000", "Subposição - Outras peças"),
        ("02022010", "02022010", "Item - Quartos dianteiros"),
    ]

    passed = 0
    failed = 0

    for input_code, expected, description in test_cases:
        result = pad_ncm_code(input_code)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"  Entrada: {input_code:10s} ({description})")
        print(f"  Esperado: {expected}")
        print(f"  Obtido:   {result}")
        print(f"  Normalizado: {normalize_ncm_code(result)}")

    print(f"\n{'='*60}")
    print(f"Resultado: {passed} passaram, {failed} falharam")
    print(f"{'='*60}\n")

    return failed == 0


def test_ncm_hierarchy():
    """Testa a detecção de níveis hierárquicos"""
    print("="*60)
    print("TESTE 2: Detecção de Níveis Hierárquicos")
    print("="*60)

    test_cases = [
        ("01.00.00.00", "capitulo"),
        ("01.01.00.00", "posicao"),
        ("01.01.21.00", "subposicao"),
        ("01.01.21.10", "item"),
        ("02.02.00.00", "posicao"),
        ("02.02.20.00", "subposicao"),
        ("02.02.20.10", "item"),
    ]

    passed = 0
    failed = 0

    for codigo_norm, expected_nivel in test_cases:
        result = detect_ncm_level(codigo_norm)
        status = "✓ PASS" if result == expected_nivel else "✗ FAIL"

        if result == expected_nivel:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"  Código: {codigo_norm}")
        print(f"  Esperado: {expected_nivel}")
        print(f"  Obtido:   {result}")

    print(f"\n{'='*60}")
    print(f"Resultado: {passed} passaram, {failed} falharam")
    print(f"{'='*60}\n")

    return failed == 0


def test_import_modules():
    """Testa importação dos módulos atualizados"""
    print("="*60)
    print("TESTE 3: Importação de Módulos")
    print("="*60)

    modules_to_test = [
        ("search", ["find_ncm_hierarchical", "find_ncm_hierarchical_with_context"]),
        ("indexer", ["prepare_ncm_documents"]),
        ("config", ["INDEX_ONLY_ITEMS"]),
    ]

    passed = 0
    failed = 0

    for module_name, functions in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"\n✓ Módulo '{module_name}' importado com sucesso")

            for func_name in functions:
                if hasattr(module, func_name):
                    print(f"  ✓ Função/variável '{func_name}' encontrada")
                    passed += 1
                else:
                    print(f"  ✗ Função/variável '{func_name}' NÃO encontrada")
                    failed += 1
        except Exception as e:
            print(f"\n✗ Erro ao importar módulo '{module_name}': {e}")
            failed += len(functions)

    print(f"\n{'='*60}")
    print(f"Resultado: {passed} passaram, {failed} falharam")
    print(f"{'='*60}\n")

    return failed == 0


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("SUITE DE TESTES - MELHORIAS RAG NCM")
    print("="*60 + "\n")

    results = []

    # Executa testes
    results.append(("Padding de Códigos NCM", test_pad_ncm_code()))
    results.append(("Detecção de Níveis Hierárquicos", test_ncm_hierarchy()))
    results.append(("Importação de Módulos", test_import_modules()))

    # Sumário
    print("\n" + "="*60)
    print("SUMÁRIO DOS TESTES")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{status:10s} - {test_name}")

    all_passed = all(result for _, result in results)

    print("="*60)
    if all_passed:
        print("✓ TODOS OS TESTES PASSARAM!")
    else:
        print("✗ ALGUNS TESTES FALHARAM")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
