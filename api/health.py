"""
ヘルスチェック用の専用Vercelサーバーレス関数
"""
from http.server import BaseHTTPRequestHandler
from datetime import datetime
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """OPTIONSリクエストへの応答"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """GETリクエストへの応答"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        # レスポンスデータの準備
        response_data = {
            "status": "healthy",
            "database": "simulated",
            "models_loaded": False,
            "available_models": [],
            "environment": "production-lite",
            "message": "簡略化されたAPIが正常に動作しています",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.1"
        }
        
        # JSONレスポンスを返す
        self.wfile.write(json.dumps(response_data).encode('utf-8')) 