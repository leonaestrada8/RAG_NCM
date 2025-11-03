import os
import subprocess
import sys
import shutil

print("==========================================")
print("BENCHMARK DE MODELOS DE EMBEDDING")
print("==========================================\n")

# 1️⃣ Verifica dependências
print("Verificando dependências...")

try:
    import chromadb
    import sentence_transformers
    from tqdm import tqdm
    print("Dependências OK\n")
except ImportError:
    print("Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chromadb", "sentence-transformers", "tqdm", "--break-system-packages"])
        print("Dependências instaladas com sucesso\n")
    except subprocess.CalledProcessError:
        print("ERRO: Falha ao instalar dependências")
        print("\nExecute manualmente:")
        print("  pip install chromadb sentence-transformers tqdm --break-system-packages")
        sys.exit(1)

# 2️⃣ Copia o arquivo benchmark_embeddings.py, se necessário
if not os.path.isfile("benchmark_embeddings.py"):
    origem = "/home/claude/benchmark_embeddings.py"
    if os.path.isfile(origem):
        shutil.copy(origem, ".")
        print("Arquivo benchmark_embeddings.py copiado para o diretório atual\n")

# 3️⃣ Executa o benchmark
print("Iniciando benchmark...")
print("ATENÇÃO: Processo pode levar vários minutos (5-15 min por modelo)\n")

subprocess.run([sys.executable, "benchmark_embeddings.py"])

print("\n==========================================")
print("BENCHMARK CONCLUÍDO")
print("==========================================\n")
print("Resultados salvos em: benchmark_results_*.json\n")
