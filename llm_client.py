# llm_client.py
# Integracao com LLM via API usando protocolo OpenAI

import requests
import openai
from openai import OpenAI
from config import PLIN_URL, CLIENT_ID, CLIENT_SECRET

_system_prompt = None


def get_token():
    """
    Obtem token de autenticacao OAuth2 para API do LLM.

    Usa credenciais CLIENT_ID e CLIENT_SECRET para autenticar
    via grant_type client_credentials.

    Retorna access_token valido para chamadas a API.
    """
    result = requests.post(
        f"{PLIN_URL}/oauth2/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    if result.ok:
        return result.json()['access_token']
    result.raise_for_status()


def get_models():
    """
    Lista modelos LLM disponiveis na API.

    Autentica com token e consulta endpoint /models usando
    cliente OpenAI compativel.

    Retorna lista ordenada de IDs de modelos disponiveis.
    """
    token = get_token()
    llm = OpenAI(base_url=f"{PLIN_URL}/gateway/v1", api_key=token)
    models = sorted([model.id for model in llm.models.list()])
    return models


def load_system_prompt(prompt_file):
    """
    Carrega prompt do sistema de arquivo texto.

    Prompt do sistema instrui LLM sobre como se comportar e responder.
    Define papel do assistente, tom, formato de resposta e restricoes.

    Se arquivo nao encontrado, usa prompt padrao basico.
    Prompt carregado fica em variavel global para reuso.
    """
    global _system_prompt
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            _system_prompt = f.read().strip()
        print(f"Prompt carregado: {len(_system_prompt)} caracteres")
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {prompt_file}, usando prompt padrão")
        _system_prompt = """Você é um assistente especializado em NCM (Nomenclatura Comum do Mercosul) e atributos de importação/exportação.
Use apenas as informações fornecidas no contexto. Seja preciso e responda em português do Brasil.
Se não encontrar informações relevantes, informe que não há dados disponíveis."""


def make_context(hits):
    """
    Formata resultados da busca vetorial em contexto textual para LLM.

    Converte lista de documentos encontrados em texto estruturado
    mostrando apenas top 5 resultados mais relevantes.

    Para NCMs: mostra codigo e descricao
    Para atributos: mostra codigo atributo, NCM, modalidade, obrigatoriedade

    Retorna string formatada pronta para incluir na mensagem ao LLM.
    """
    if not hits:
        return "Nenhuma informação relevante encontrada na base de dados."

    message = "Informações encontradas na base de dados:\n\n"
    for hit in hits[:5]:
        if hit.get('tipo') == 'ncm':
            message += f"NCM: {hit.get('codigo', 'N/A')}\n"
            message += f"Descrição: {hit.get('descricao', 'N/A')}\n\n"
        elif hit.get('tipo') == 'atributo':
            message += f"Atributo: {hit.get('atributo_codigo', 'N/A')}\n"
            message += f"NCM: {hit.get('ncm_codigo', 'N/A')}\n"
            message += f"Modalidade: {hit.get('modalidade', 'N/A')}\n"
            message += f"Obrigatório: {hit.get('obrigatorio', 'N/A')}\n\n"

    return message


def messages_for(prompt, hits):
    """
    Cria array de mensagens no formato esperado pela API OpenAI.

    Estrutura de mensagens:
    1. System message: instrucoes de comportamento do assistente
    2. User message: contexto RAG + pergunta do usuario

    Combina contexto recuperado da busca vetorial com pergunta original
    do usuario para fornecer informacao relevante ao LLM.
    """
    global _system_prompt

    if _system_prompt is None:
        load_system_prompt('system_prompt.txt')

    context = make_context(hits)
    user_message = f"{context}\n\nPergunta do usuário: {prompt}"

    return [
        {"role": "system", "content": _system_prompt},
        {"role": "user", "content": user_message}
    ]


def chat(collection, prompt, model, find_similars_func):
    """
    Processa consulta usando arquitetura RAG (Retrieval Augmented Generation).

    Fluxo RAG:
    1. Busca documentos similares usando find_similars_func
    2. Formata contexto com resultados encontrados
    3. Envia prompt + contexto para LLM
    4. Retorna resposta gerada em streaming

    Usa streaming para mostrar resposta progressivamente conforme
    LLM gera tokens.

    Trata erros de API (conexao, rate limit, etc) retornando
    resultado parcial + mensagem de erro.

    Retorna generator que yielda resultado acumulado a cada chunk.
    """
    result = ""
    try:
        token = get_token()
        llm = OpenAI(base_url=f"{PLIN_URL}/gateway/v1", api_key=token)
        hits = find_similars_func(collection, prompt)

        stream = llm.chat.completions.create(
            model=model,
            messages=messages_for(prompt, hits),
            stream=True
        )

        for chunk in stream:
            result += chunk.choices[0].delta.content or ""
            yield result

    except IndexError:
        yield result
    except openai.APIError as e:
        yield result + f"\n\nErro na API: {e}"
    except openai.APIConnectionError as e:
        yield result + f"\n\nErro de conexão: {e}"
    except openai.RateLimitError as e:
        yield result + f"\n\nLimite de taxa excedido: {e}"
    except Exception as e:
        yield result + f"\n\nErro: {e}"
