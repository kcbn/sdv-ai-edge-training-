import sys
import importlib.util

print("=== 1. Python バージョン確認 ===")
print(f"Python: {sys.version}\n")

print("=== 2. 主要ライブラリのインストール状況 ===")
libraries = [
    "torch", 
    "transformers", 
    "accelerate", 
    "sentence_transformers", 
    "chromadb"
]

for lib in libraries:
    spec = importlib.util.find_spec(lib)
    if spec is not None:
        try:
            module = importlib.import_module(lib)
            version = getattr(module, "__version__", "version unknown")
            print(f"  [〇] {lib}: インストール済み (バージョン: {version})")
        except Exception as e:
            print(f"  [△] {lib}: インストール済みですが、エラー ({e})")
    else:
        print(f"  [×] {lib}: 未インストール")

print("\n=== 3. Apple Silicon (MPS) の利用可否確認 ===")
try:
    import torch
    if torch.backends.mps.is_available():
        print("  [〇] Apple Silicon GPU (MPS) 利用可能")
    else:
        print("  [×] MPS利用不可 (CPUモードで動作します)")
except Exception:
    print("  [×] PyTorchの確認に失敗しました")
