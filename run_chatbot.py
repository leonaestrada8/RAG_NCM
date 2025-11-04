# run_chatbot.py
# Interface Gradio para chatbot RAG

from main import setup_database
import gradio as gr
from llm_client import chat, get_models
from search import find_similars
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
    """Cria interface Gradio para chat"""
    
    def chat_wrapper(prompt, model):
        """Wrapper que consome generator e retorna string final"""
        result = ""
        for chunk in chat(collection, prompt, model, find_similars):
            result = chunk
        return result
    
    view = gr.Interface(
        fn=chat_wrapper,
        title="Catálogo NCM",
        description="Faça uma pergunta sobre o catálogo de produtos",
        inputs=[
            gr.Textbox(label="Sua pergunta:", lines=6),
            gr.Dropdown(get_models(), label="Selecione o modelo:", value=DEFAULT_MODEL)
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