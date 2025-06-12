"""
このファイルはVercelデプロイ時にモデルディレクトリを含めるためのものです。
実際の機能はありません。
"""
# モデルディレクトリのパスを明示的に参照
import os
import sys
from pathlib import Path

# 現在のファイルの絶対パス
current_file = Path(__file__).resolve()

# プロジェクトのルートディレクトリ
project_root = current_file.parent.parent.parent

# モデルディレクトリのパス
models_dir = current_file.parent.parent / "models"

# 確認メッセージ
print(f"モデルディレクトリ: {models_dir}")
print(f"存在する: {os.path.exists(models_dir)}")

# モデルファイルの存在確認
if os.path.exists(models_dir):
    model_files = list(models_dir.glob("*.joblib"))
    print(f"モデルファイル一覧: {[f.name for f in model_files]}")
else:
    print("モデルディレクトリが存在しません。") 