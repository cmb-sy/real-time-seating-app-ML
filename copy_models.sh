#!/bin/bash
# モデルファイルをAPIディレクトリにコピーするスクリプト

# モデルファイルをAPIディレクトリにコピー
cp -r src/models/*.joblib src/api/

echo "モデルファイルをAPIディレクトリにコピーしました" 