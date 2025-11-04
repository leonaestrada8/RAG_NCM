#!/bin/bash
# start.sh - Launcher para Sistema RAG NCM

echo "=================================================="
echo "          SISTEMA RAG NCM - LAUNCHER"
echo "=================================================="
echo ""
echo "Escolha o modo de execução:"
echo ""
echo "  1. Menu Principal (Completo)"
echo "  2. Interface Web (Gradio)"
echo "  3. Modo CLI Interativo"
echo "  4. Apenas Setup do Banco"
echo ""
echo "  0. Cancelar"
echo ""

read -p "Opção: " choice

case $choice in
    1)
        echo ""
        echo "Iniciando Menu Principal..."
        python main.py
        ;;
    2)
        echo ""
        echo "Iniciando Interface Web (Gradio)..."
        python run_chatbot.py
        ;;
    3)
        echo ""
        echo "Iniciando Modo CLI Interativo..."
        python main.py --cli
        ;;
    4)
        echo ""
        echo "Executando Setup do Banco..."
        python main.py --setup-only
        ;;
    0)
        echo ""
        echo "Cancelado."
        exit 0
        ;;
    *)
        echo ""
        echo "Opção inválida!"
        exit 1
        ;;
esac
