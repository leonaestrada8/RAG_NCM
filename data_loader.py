# data_loader_simplified.py
# Versao simplificada com texto focado apenas na descricao do NCM
# Reduz ruido e melhora qualidade das buscas vetoriais

import pandas as pd
import json
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
            
            mask = ncm_df['Código'] != ''
            ncm_df.loc[mask, 'Código'] = ncm_df.loc[mask, 'Código'].str.zfill(8)
            
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
    Cria texto SIMPLIFICADO focado apenas na descricao do NCM
    
    ANTES: Texto longo com capitulo, posicao, subposicao, atributos
    DEPOIS: Texto curto focado apenas no NCM especifico
    
    Objetivo: Reduzir ruido e melhorar qualidade dos embeddings
    """
    codigo = row['Código']
    codigo_norm = row['CódigoNormalizado']
    desc = row['Descrição']
    
    if not codigo or not desc:
        return None
    
    nivel = detect_ncm_level(codigo_norm)
    
    # VERSAO SIMPLIFICADA - Apenas NCM e descricao
    texto = f"NCM {codigo_norm}: {desc}"
    
    # Adiciona contexto minimo apenas para niveis inferiores
    if nivel in ['capitulo', 'posicao']:
        hier = hierarchy.get(codigo, {})
        cap = hier.get('capitulo')
        
        if nivel == 'capitulo' and cap:
            texto = f"Capítulo {cap['codigo']} - {desc}"
        elif nivel == 'posicao' and cap:
            texto = f"{desc} (Cap {cap['codigo']})"
    
    return texto


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

