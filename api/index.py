"""
Vercel Serverless Function エントリーポイント
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Vercel Serverless Functions 用のハンドラー
handler = app 