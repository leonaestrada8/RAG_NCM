# run_chatbot.py
# Interface Gradio para chatbot RAG

from main import setup_database
import gradio as gr
from llm_client import chat, get_models
from search import find_similars, find_ncm_hierarchical_with_context, find_ncm_hierarchical
from config import DEFAULT_MODEL

force_dark_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

def create_chat_interface(collection):
    """Cria interface Gradio para chat com opção de tipo de busca"""

    def chat_wrapper(prompt, model, search_type):
        """Wrapper que consome generator e retorna string final ou resultados de busca"""

        if search_type == "Busca Vetorial (sem LLM)":
            # Busca vetorial hierárquica sem geração de resposta
            results = find_ncm_hierarchical(collection, prompt, k=10, prefer_items=True)

            if not results:
                return "Nenhum resultado encontrado."

            # Formata resultados em markdown
            output = "## Resultados da Busca Vetorial\n\n"
            for i, r in enumerate(results, 1):
                cod = r.get('codigo_normalizado') or r.get('codigo')
                desc = r['descricao']
                dist = r['distance']
                nivel = r.get('nivel', 'desconhecido')
                score = r.get('score', 1 - dist)

                output += f"### {i}. NCM {cod} [{nivel}]\n"
                output += f"**Similaridade:** {score:.2%} (distância: {dist:.4f})\n"
                output += f"**Descrição:** {desc}\n\n"

            return output

        else:
            # Busca com LLM (modo padrão)
            result = ""
            for chunk in chat(collection, prompt, model, find_ncm_hierarchical_with_context):
                result = chunk
            return result

    view = gr.Interface(
        fn=chat_wrapper,
        title="Catálogo NCM",
        description="Faça uma pergunta sobre o catálogo de produtos. Escolha entre busca vetorial pura ou busca com resposta gerada pelo LLM.",
        inputs=[
            gr.Textbox(label="Sua pergunta:", lines=6),
            gr.Dropdown(get_models(), label="Selecione o modelo:", value=DEFAULT_MODEL),
            gr.Radio(
                choices=["Busca com LLM (resposta gerada)", "Busca Vetorial (sem LLM)"],
                label="Tipo de busca:",
                value="Busca com LLM (resposta gerada)"
            )
        ],
        outputs=[gr.Markdown(label="Resposta:")],
        submit_btn="Enviar",
        clear_btn="Apagar",
        flagging_mode="never",
        js=force_dark_mode
    )

    return view

def launch_ui(collection, share=False):
    """Lança interface Gradio"""
    view = create_chat_interface(collection)
    view.launch(share=share)


if __name__ == "__main__":
    print("Configurando sistema RAG")
    collection = setup_database()
    
    print("Iniciando interface Gradio")
    launch_ui(collection, share=False)