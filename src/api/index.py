"""
ルートパス用のVercelサーバーレス関数
"""
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """APIのルートパスにアクセスした際の情報を返す"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 現在の日時
        now = datetime.now()
        
        # APIの基本情報
        response_data = {
            "status": "ok",
            "name": "リアルタイム座席予測API（ML版）",
            "version": "1.0.0",
            "timestamp": now.isoformat(),
            "endpoints": [
                {
                    "path": "/health",
                    "description": "APIの稼働状態を確認"
                },
                {
                    "path": "/api/predictions/today-tomorrow",
                    "description": "今日と明日の座席予測データを取得"
                },
                {
                    "path": "/api/predictions/weekly-average",
                    "description": "曜日ごとの平均予測データを取得"
                },
                {
                    "path": "/ml/predict?day_of_week=X",
                    "description": "特定曜日(0-4)の予測データを取得"
                }
            ],
            "message": "詳細はAPI_ENDPOINTS.mdを参照してください"
        }
        
        # レスポンスを返す
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8')) 