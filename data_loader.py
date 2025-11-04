# data_loader.py
# Carregamento e normalizacao de dados NCM e atributos

import pandas as pd
import json
import unicodedata
import re
from config import NCM_FILE, ATRIBUTOS_FILE


def normalize_ncm_code(code):
    """
    Normaliza codigo NCM para formato padrao com pontos.

    Transforma codigo de 8 digitos sem formatacao em formato visual
    com pontos separadores. Exemplo: 01012100 -> 0101.21.00

    Remove pontos e hifens existentes antes de reformatar.
    Se codigo nao tiver 8 digitos, retorna sem alteracao.
    """
    if not code or pd.isna(code):
        return ""

    code = str(code).strip().replace('.', '').replace('-', '')

    if len(code) == 8:
        return f"{code[:4]}.{code[4:6]}.{code[6:8]}"

    return code


def normalize_text_advanced(text, keep_stopwords_if_short=True):
    """
    Normalizacao avancada de texto para melhorar busca semantica.

    Processo de normalizacao:
    1. Remove acentos convertendo para ASCII (mantem semantica)
    2. Converte para minusculas
    3. Remove pontuacao extra mantendo espacos e hifens
    4. Remove espacos multiplos
    5. Remove stopwords comuns apenas em textos longos (>3 palavras)

    Stopwords removidas seletivamente: de, da, do, dos, das, em, na, no, para, com, o, a

    Preserva stopwords em textos curtos para nao perder contexto importante.
    Objetivo: melhorar qualidade dos embeddings sem perder semantica.
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
    Preenche codigo NCM para 8 digitos respeitando hierarquia.

    Hierarquia NCM:
    - 2 digitos = Capitulo     -> preenche com 000000 a direita
    - 4 digitos = Posicao      -> preenche com 0000 a direita
    - 6 digitos = Subposicao   -> preenche com 00 a direita
    - 7 digitos = Caso especial-> preenche com 0 a direita
    - 8 digitos = Item         -> retorna sem alteracao

    Essencial para manter consistencia na hierarquia e permitir
    busca e filtragem correta por nivel hierarquico.
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
    """
    Carrega dados NCM do arquivo CSV configurado.

    Tenta multiplos encodings (iso-8859-1, latin-1, cp1252, utf-8) ate
    encontrar um que funcione, pois arquivo pode estar em diferentes encodings.

    Operacoes realizadas:
    - Le apenas colunas 0 (codigo) e 1 (descricao)
    - Renomeia colunas para padrao Codigo/Descricao
    - Remove espacos extras dos dados
    - Filtra registros vazios
    - Aplica padding correto nos codigos (pad_ncm_code)
    - Gera codigo normalizado com pontos (normalize_ncm_code)

    Retorna DataFrame com colunas: Codigo, Descricao, CodigoNormalizado
    """
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

            # Aplica padding baseado no tamanho original
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
    """
    Carrega dados de atributos do arquivo JSON configurado.

    Tenta multiplos encodings ate encontrar um valido.
    JSON contem estrutura com chave 'listaNcm' contendo lista de objetos,
    cada um com 'codigoNcm' e 'listaAtributos'.

    Retorna dicionario com estrutura original do JSON.
    Em caso de erro, retorna dicionario vazio com chave 'listaNcm'.
    """
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
    """
    Detecta nivel hierarquico de um codigo NCM.

    Analisa codigo normalizado e determina nivel baseado no padrao:
    - Capitulo: 2 digitos ou 8 digitos terminando em 000000
    - Posicao: 4 digitos ou 8 digitos terminando em 0000
    - Subposicao: 6 digitos ou 8 digitos terminando em 00
    - Item: 8 digitos completos sem zeros finais

    Retorna string: 'capitulo', 'posicao', 'subposicao', 'item' ou 'desconhecido'
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


def build_ncm_hierarchy(ncm_df):
    """
    Constroi dicionario de hierarquia NCM.

    Para cada codigo NCM, armazena:
    - nivel: capitulo/posicao/subposicao/item
    - capitulo: codigo e titulo do capitulo pai
    - posicao: codigo e titulo da posicao pai

    Percorre DataFrame sequencialmente mantendo contexto do capitulo
    e posicao atual para associar a subitens e items.

    Retorna dicionario indexado por codigo NCM completo.
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
    Cria dicionario de busca rapida de atributos por codigo NCM.

    Extrai 'listaNcm' do JSON e mapeia cada codigoNcm para sua
    listaAtributos correspondente.

    Retorna dicionario: {codigo_ncm: lista_de_atributos}
    """
    atributos_dict = {}
    
    for item in atributos_data.get('listaNcm', []):
        ncm_code = item['codigoNcm']
        atributos_dict[ncm_code] = item['listaAtributos']
    
    return atributos_dict


def create_enriched_ncm_text(row, hierarchy, atributos_dict):
    """
    Cria texto enriquecido para indexacao vetorial de um NCM.

    Combina multiplas informacoes para melhorar qualidade dos embeddings:
    - Codigo NCM normalizado e descricao principal
    - Contexto hierarquico (capitulo e posicao) quando aplicavel
    - Nivel hierarquico (capitulo/posicao/subposicao/item)
    - Indicacao de quantidade de atributos cadastrados

    Estrategia de enriquecimento por nivel:
    - Items e subposicoes: inclui capitulo e posicao pai
    - Posicoes: inclui apenas capitulo pai
    - Capitulos: formato simplificado

    Aplica normalizacao avancada de texto (opcional via env DISABLE_NORMALIZATION)
    para melhorar embeddings removendo acentos, stopwords e pontuacao.

    Retorna string formatada pronta para vetorizacao.
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

    # Aplica normalização avançada para melhorar embeddings (OPCIONAL)
    # Pode ser desabilitada para testes A/B via variável de ambiente
    import os
    USE_NORMALIZATION = os.environ.get('DISABLE_NORMALIZATION', '0') != '1'

    if USE_NORMALIZATION:
        # Normaliza cada linha
        lines = texto.split('\n')
        normalized_lines = [normalize_text_advanced(line, keep_stopwords_if_short=True) for line in lines]
        texto_normalizado = ' | '.join([l for l in normalized_lines if l])
        return texto_normalizado
    else:
        # Retorna SEM normalização (para testes A/B)
        return texto


def create_atributo_description(ncm_code, atributo):
    """
    Cria texto descritivo para indexacao de um atributo NCM.

    Formata informacoes do atributo em texto estruturado:
    - Codigo NCM associado
    - Codigo do atributo
    - Modalidade (Importacao/Exportacao)
    - Se e obrigatorio ou opcional
    - Se e multivalorado
    - Data de inicio de vigencia

    Retorna string formatada multiplas linhas.
    """
    return f"""NCM: {ncm_code}
Código Atributo: {atributo['codigo']}
Modalidade: {atributo['modalidade']}
Obrigatório: {'Sim' if atributo['obrigatorio'] else 'Não'}
Multivalorado: {'Sim' if atributo['multivalorado'] else 'Não'}
Data Início Vigência: {atributo['dataInicioVigencia']}"""



