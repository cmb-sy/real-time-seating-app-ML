"""
FastAPIサーバー起動スクリプト
"""

import uvicorn

if __name__ == "__main__":
    # FastAPIサーバーを起動
    uvicorn.run(
        "main:app",           # メインアプリケーション
        host="0.0.0.0",       # 全てのIPアドレスからアクセス可能
        port=8000,            # ポート番号
        reload=True,          # ファイル変更時の自動リロード
        log_level="info"      # ログレベル
    ) 