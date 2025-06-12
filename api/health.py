"""
ヘルスチェック用の専用Vercelサーバーレス関数
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
        """ヘルスチェックエンドポイント"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        # レスポンスデータ
        response_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "リアルタイム座席予測API が正常に動作しています",
            "version": "2.0.0",
            "endpoints": {
                "health": "/api/health",
                "predictions_today_tomorrow": "/api/predictions-today-tomorrow",
                "predictions_weekly": "/api/predictions-weekly-average"
            }
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8')) 