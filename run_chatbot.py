# run_chatbot.py
# Script para executar interface de chatbot

from main import setup_database
from ui import launch_ui

if __name__ == "__main__":
    print("Configurando sistema RAG")
    collection = setup_database()
    
    print("Iniciando interface Gradio")
    launch_ui(collection, share=False)