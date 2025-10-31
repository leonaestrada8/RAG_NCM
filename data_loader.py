# data_loader_simplified.py
# Versao simplificada com texto focado apenas na descricao do NCM
# Reduz ruido e melhora qualidade das buscas vetoriais

import pandas as pd
import json
import unicodedata
import re
from config import NCM_FILE, ATRIBUTOS_FILE


def normalize_ncm_code(code):
    """
    Normaliza codigo NCM para formato com pontos
    01012100 -> 0101.21.00
    """
    if not code or pd.isna(code):
        return ""

    code = str(code).strip().replace('.', '').replace('-', '')

    if len(code) == 8:
        return f"{code[:4]}.{code[4:6]}.{code[6:8]}"

    return code


def normalize_text_advanced(text, keep_stopwords_if_short=True):
    """
    Normalização avançada de texto para melhorar busca semântica.

    Aplica:
    - Remoção de acentos (mantém semântica)
    - Lowercase
    - Limpeza de pontuação
    - Remoção seletiva de stopwords

    Args:
        text: Texto para normalizar
        keep_stopwords_if_short: Se True, mantém stopwords em textos curtos

    Returns:
        Texto normalizado
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Remove acentos mantendo semântica
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')

    # 2. Lowercase
    text = text.lower()

    # 3. Remove pontuação extra, mantém espaços e hífens
    text = re.sub(r'[^\w\s-]', ' ', text)

    # 4. Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text)

    # 5. Remove stopwords muito comuns (mas não todas)
    # Lista mínima para não perder semântica importante
    minimal_stopwords = {'de', 'da', 'do', 'dos', 'das', 'em', 'na', 'no', 'para', 'com', 'o', 'a'}
    words = text.split()

    # Só remove stopwords se texto tem mais de 3 palavras
    if keep_stopwords_if_short and len(words) > 3:
        words = [w for w in words if w not in minimal_stopwords or len(w) > 2]

    return ' '.join(words).strip()


def pad_ncm_code(code):
    """
    Preenche código NCM corretamente baseado no tamanho original
    Mantém a hierarquia correta sem preencher zeros à esquerda incorretamente

    Exemplos:
    - "01" (capítulo) -> "01000000"
    - "0101" (posição) -> "01010000"
    - "010121" (subposição) -> "01012100"
    - "01012100" (item) -> "01012100"
    """
    if not code or pd.isna(code):
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


def load_ncm_data():
    """Carrega CSV com encoding correto e normaliza codigos"""
    encodings = ['iso-8859-1', 'latin-1', 'cp1252', 'utf-8']

    for encoding in encodings:
        try:
            ncm_df = pd.read_csv(
                NCM_FILE,
                encoding=encoding,
                dtype=str,
                usecols=[0, 1]
            )

            ncm_df.columns = ['Código', 'Descrição']

            ncm_df['Código'] = ncm_df['Código'].fillna('').str.strip()
            ncm_df['Descrição'] = ncm_df['Descrição'].fillna('').str.strip()

            ncm_df = ncm_df[
                (ncm_df['Código'] != '') | (ncm_df['Descrição'] != '')
            ]

            # CORRIGIDO: Aplica padding correto baseado no tamanho original
            mask = ncm_df['Código'] != ''
            ncm_df.loc[mask, 'Código'] = ncm_df.loc[mask, 'Código'].apply(pad_ncm_code)

            ncm_df['CódigoNormalizado'] = ncm_df['Código'].apply(normalize_ncm_code)

            print(f"NCM carregado: {encoding}, {len(ncm_df)} registros")
            return ncm_df

        except Exception as e:
            continue

    print("ERRO: Não foi possível carregar NCM")
    return pd.DataFrame(columns=['Código', 'Descrição', 'CódigoNormalizado'])


def load_atributos_data():
    """Carrega JSON de atributos"""
    encodings = ['utf-8', 'iso-8859-1', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(ATRIBUTOS_FILE, 'r', encoding=encoding) as f:
                data = json.load(f)
            print(f"Atributos carregados: {encoding}, {len(data.get('listaNcm', []))} NCMs")
            return data
        except:
            continue
    
    print("ERRO: Não foi possível carregar atributos")
    return {'listaNcm': []}


def detect_ncm_level(codigo_norm):
    """Detecta nivel hierarquico do NCM"""
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


def build_ncm_hierarchy(ncm_df):
    """
    Constroi hierarquia NCM simplificada
    Mantido para compatibilidade mas nao usado na indexacao
    """
    hierarchy = {}
    
    current_capitulo = None
    current_posicao = None
    
    for _, row in ncm_df.iterrows():
        codigo = row['Código']
        desc = row['Descrição']
        codigo_norm = row['CódigoNormalizado']
        
        if not codigo:
            continue
        
        nivel = detect_ncm_level(codigo_norm)
        
        if nivel == 'capitulo':
            current_capitulo = {'codigo': codigo[:2], 'titulo': desc}
        elif nivel == 'posicao':
            current_posicao = {'codigo': codigo[:4], 'titulo': desc}
        
        hierarchy[codigo] = {
            'nivel': nivel,
            'capitulo': current_capitulo,
            'posicao': current_posicao
        }
    
    return hierarchy


def create_atributos_dict(atributos_data):
    """
    Cria dicionario de atributos por NCM
    """
    atributos_dict = {}
    
    for item in atributos_data.get('listaNcm', []):
        ncm_code = item['codigoNcm']
        atributos_dict[ncm_code] = item['listaAtributos']
    
    return atributos_dict


def create_enriched_ncm_text(row, hierarchy, atributos_dict):
    """
    Cria texto ENRIQUECIDO com hierarquia completa do NCM

    Inclui contexto hierárquico para melhorar precisão das buscas:
    - Descrição do item específico
    - Categoria hierárquica (posição)
    - Capítulo ao qual pertence
    - Nível hierárquico

    Objetivo: Melhorar qualidade dos embeddings através de contexto hierárquico
    """
    codigo = row['Código']
    codigo_norm = row['CódigoNormalizado']
    desc = row['Descrição']

    if not codigo or not desc:
        return None

    nivel = detect_ncm_level(codigo_norm)

    # Base: NCM e descrição principal
    texto = f"NCM {codigo_norm}: {desc}"

    # Adiciona contexto hierárquico baseado no nível
    hier = hierarchy.get(codigo, {})
    capitulo = hier.get('capitulo')
    posicao = hier.get('posicao')

    # Para subitens e itens, adiciona categoria e capítulo para contexto
    if nivel in ['subposicao', 'item']:
        if capitulo:
            texto += f"\nCapítulo: {capitulo['titulo']}"

        if posicao and posicao.get('codigo') != capitulo.get('codigo'):
            texto += f"\nCategoria: {posicao['titulo']}"

    # Para posições, adiciona apenas o capítulo
    elif nivel == 'posicao':
        if capitulo:
            texto += f"\nCapítulo: {capitulo['titulo']}"

    # Para capítulos, mantém simples
    elif nivel == 'capitulo':
        texto = f"Capítulo {codigo_norm[:2]}: {desc}"

    # Adiciona indicador de nível para ajudar no ranking
    texto += f"\nNível: {nivel}"

    # Indica se tem atributos cadastrados
    if codigo_norm in atributos_dict:
        num_attrs = len(atributos_dict[codigo_norm])
        texto += f"\nAtributos: {num_attrs} cadastrados"

    # Aplica normalização avançada para melhorar embeddings
    # Nota: Mantém estrutura multi-linha mas normaliza cada parte
    lines = texto.split('\n')
    normalized_lines = [normalize_text_advanced(line, keep_stopwords_if_short=True) for line in lines]
    texto_normalizado = ' | '.join([l for l in normalized_lines if l])

    return texto_normalizado


def create_atributo_description(ncm_code, atributo):
    """
    Cria texto descritivo para atributo
    Mantido igual
    """
    return f"""NCM: {ncm_code}
Código Atributo: {atributo['codigo']}
Modalidade: {atributo['modalidade']}
Obrigatório: {'Sim' if atributo['obrigatorio'] else 'Não'}
Multivalorado: {'Sim' if atributo['multivalorado'] else 'Não'}
Data Início Vigência: {atributo['dataInicioVigencia']}"""


# ============================================================
# COMPARACAO DE ABORDAGENS
# ============================================================

def create_enriched_ncm_text_ORIGINAL(row, hierarchy, atributos_dict):
    """
    VERSAO ORIGINAL (PARA REFERENCIA)
    Texto muito longo com multiplos niveis
    
    Exemplo de output:
    NCM: 0901.11.10
    Capítulo 09: Café, chá, mate e especiarias
    Posição 0901: Café, mesmo torrado ou descafeinado
    Subposição 09011: Café não torrado
    Descrição: Café em grão não descafeinado
    Atributos Importação: 8 (2 obrigatórios)
    Códigos: ATT_123, ATT_456, ...
    """
    pass


def create_enriched_ncm_text_SIMPLIFICADO(row, hierarchy, atributos_dict):
    """
    VERSAO SIMPLIFICADA (IMPLEMENTADA)
    Texto curto focado na descricao
    
    Exemplo de output:
    NCM 0901.11.10: Café em grão não descafeinado
    
    Vantagens:
    - Embeddings mais precisos
    - Menos ruído nos vetores
    - Buscas mais relevantes
    - Distâncias menores
    """
    pass

