#!/usr/bin/env python3
# clear_cache.py
# Script para limpar cache de embeddings corrompido

"""
LIMPA CACHE DE EMBEDDINGS

Use este script quando:
- Cache está corrompido
- Modelos foram salvos com nome errado
- Quer forçar recálculo completo

Uso:
    python clear_cache.py              # Limpa todo o cache
    python clear_cache.py --model e5   # Limpa apenas modelos com 'e5' no nome
"""

import os
import shutil
import argparse
from pathlib import Path


def clear_cache(cache_dir="cache/embeddings", model_filter=None):
    """
    Limpa cache de embeddings

    Args:
        cache_dir: Diretório do cache
        model_filter: Se fornecido, limpa apenas modelos que contêm este texto
    """
    cache_path = Path(cache_dir)

    if not cache_path.exists():
        print(f"❌ Cache não encontrado em: {cache_path}")
        return

    # Conta arquivos antes
    pkl_files = list(cache_path.glob("*.pkl"))
    json_files = list(cache_path.glob("*.json"))

    total_files = len(pkl_files) + len(json_files)
    cache_size_mb = sum(f.stat().st_size for f in pkl_files + json_files) / (1024 * 1024)

    print("\n" + "="*60)
    print("LIMPEZA DE CACHE DE EMBEDDINGS")
    print("="*60)
    print(f"Diretório: {cache_path.absolute()}")
    print(f"Arquivos: {total_files} ({len(pkl_files)} embeddings + {len(json_files)} metadata)")
    print(f"Tamanho: {cache_size_mb:.2f} MB")

    if model_filter:
        print(f"Filtro: apenas modelos contendo '{model_filter}'")

    # Confirma
    response = input("\n⚠️  Deseja limpar o cache? [s/N]: ").strip().lower()
    if response not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada")
        return

    # Remove
    if model_filter:
        # Limpeza parcial (baseada em metadata)
        import json
        metadata_file = cache_path / "metadata.json"

        if not metadata_file.exists():
            print("❌ metadata.json não encontrado. Use limpeza completa (sem --model)")
            return

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        entries_to_remove = []
        for hash_key, meta in metadata.get("entries", {}).items():
            if model_filter.lower() in meta.get("model", "").lower():
                entries_to_remove.append(hash_key)

        print(f"\n🗑️  Removendo {len(entries_to_remove)} entradas...")

        removed = 0
        for hash_key in entries_to_remove:
            cache_file = cache_path / f"{hash_key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
                removed += 1
            del metadata["entries"][hash_key]

        # Salva metadata atualizado
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Removidos {removed} arquivos")

    else:
        # Limpeza completa
        print(f"\n🗑️  Removendo todo o cache...")
        shutil.rmtree(cache_path)
        cache_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Cache limpo completamente")

    print("\n✅ Limpeza concluída!")
    print("\nPróximo benchmark irá recalcular todos os embeddings.")
    print(f"Tempo estimado: ~2-4 horas (primeira execução)\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Limpa cache de embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--model',
        type=str,
        help='Limpa apenas modelos contendo este texto (ex: "e5", "bge")'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        default='cache/embeddings',
        help='Diretório do cache (padrão: cache/embeddings)'
    )

    args = parser.parse_args()

    clear_cache(cache_dir=args.cache_dir, model_filter=args.model)
