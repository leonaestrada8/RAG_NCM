#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples das funções de normalização sem dependências
"""

def pad_ncm_code(code):
    """
    Função de padding copiada para teste
    """
    if not code:
        return ''

    code = str(code).strip()

    if len(code) == 2:  # Capítulo
        return code + '000000'
    elif len(code) == 4:  # Posição
        return code + '0000'
    elif len(code) == 6:  # Subposição
        return code + '00'
    elif len(code) == 8:  # Item completo
        return code
    elif len(code) == 7:  # Caso especial 7 dígitos
        return code + '0'
    else:
        # Para códigos com tamanho incomum, preenche à direita
        return code.ljust(8, '0')


def normalize_ncm_code(code):
    """
    Função de normalização copiada para teste
    """
    if not code:
        return ""

    code = str(code).strip().replace('.', '').replace('-', '')

    if len(code) == 8:
        return f"{code[:4]}.{code[4:6]}.{code[6:8]}"

    return code


def detect_ncm_level(codigo_norm):
    """
    Função de detecção de nível copiada para teste
    """
    if not codigo_norm:
        return 'desconhecido'

    code = codigo_norm.replace('.', '')

    if len(code) == 2 or (len(code) == 8 and code[2:] == '000000'):
        return 'capitulo'
    elif len(code) == 4 or (len(code) == 8 and code[4:] == '0000'):
        return 'posicao'
    elif len(code) == 6 or (len(code) == 8 and code[6:] == '00'):
        return 'subposicao'
    elif len(code) == 8:
        return 'item'

    return 'desconhecido'


print("="*60)
print("TESTE DE NORMALIZAÇÃO DE CÓDIGOS NCM")
print("="*60)

# Casos de teste baseados no exemplo real do usuário
test_cases = [
    ("01", "Capítulo 01 - Animais vivos"),
    ("0202", "Posição 0202 - Carnes bovinas congeladas"),
    ("02021000", "Item - Carcaças e meias-carcaças"),
    ("020220", "Subposição - Outras peças não desossadas"),
    ("02022010", "Item - Quartos dianteiros"),
    ("02022020", "Item - Quartos traseiros"),
    ("02022090", "Item - Outras"),
    ("02023000", "Item - Desossadas"),
]

print("\nTESTE 1: Padding correto (SEM zeros à esquerda)")
print("-"*60)

for input_code, description in test_cases:
    padded = pad_ncm_code(input_code)
    normalized = normalize_ncm_code(padded)
    nivel = detect_ncm_level(normalized)

    # Verifica se NÃO está começando com "0000" (erro antigo)
    if normalized.startswith("0000"):
        status = "✗ ERRO"
        error_msg = " <- ERRO! Código inválido com zeros à esquerda"
    else:
        status = "✓ OK"
        error_msg = ""

    print(f"\n{status}")
    print(f"  Input:       {input_code:10s}")
    print(f"  Padded:      {padded}")
    print(f"  Normalizado: {normalized}{error_msg}")
    print(f"  Nível:       {nivel}")
    print(f"  Descrição:   {description}")

print("\n" + "="*60)
print("TESTE 2: Hierarquia 0202 (Carnes bovinas)")
print("="*60)

hierarchy_0202 = [
    ("0202", "posicao", "Carnes de animais da espécie bovina, congeladas"),
    ("02021000", "item", "Carcaças e meias-carcaças"),
    ("020220", "subposicao", "Outras peças não desossadas"),
    ("02022010", "item", "Quartos dianteiros"),
    ("02022020", "item", "Quartos traseiros"),
    ("02022090", "item", "Outras"),
    ("02023000", "item", "Desossadas"),
]

all_correct = True

for code, expected_nivel, desc in hierarchy_0202:
    padded = pad_ncm_code(code)
    normalized = normalize_ncm_code(padded)
    nivel = detect_ncm_level(normalized)

    correct = nivel == expected_nivel
    status = "✓" if correct else "✗"

    if not correct:
        all_correct = False

    print(f"\n{status} {code:10s} -> {normalized:12s} [{nivel:12s}]")
    print(f"  Esperado: {expected_nivel}, Descrição: {desc}")
    if not correct:
        print(f"  *** ERRO: Esperava '{expected_nivel}', obteve '{nivel}'")

print("\n" + "="*60)
if all_correct:
    print("✓ TODOS OS TESTES PASSARAM!")
    print("  - Códigos normalizados corretamente (sem 0000.xx.xx)")
    print("  - Hierarquia preservada")
    print("  - Níveis detectados corretamente")
else:
    print("✗ ALGUNS TESTES FALHARAM")
print("="*60)
