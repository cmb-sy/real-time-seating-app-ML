#!/bin/bash
# シンプルなインストールスクリプト

# 必要なディレクトリを作成
mkdir -p .vercel/output/functions
mkdir -p .vercel/output/static

# APIファイルをコピー
cp -r src/api/*.py .vercel/output/functions/

# モデルファイルをAPIディレクトリにコピー
cp -r src/models/*.joblib .vercel/output/functions/

# 必要最小限のパッケージをインストール
pip install joblib==1.3.2 numpy==1.26.0 --target .vercel/output/functions --no-deps

# 権限を設定
chmod -R 755 .vercel/output/functions

echo "インストール完了" 