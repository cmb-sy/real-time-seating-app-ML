"""
ヘルスチェック用の専用Vercelサーバーレス関数
Supabaseデータベース接続テスト付き
"""
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import os

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
        try:
            # Supabase接続テスト
            database_status, database_info = self.test_supabase_connection()
            
            now = datetime.now()
            
            # レスポンスデータ
            response_data = {
                "status": "healthy" if database_status else "unhealthy",
                "timestamp": now.isoformat(),
                "message": "リアルタイム座席予測API が正常に動作しています" if database_status else "データベース接続に問題があります",
                "version": "2.1.0",
                "database": database_info,
                "endpoints": {
                    "health": "/health または /api/health",
                    "predictions_today_tomorrow": "/predictions/today-tomorrow または /api/predictions/today-tomorrow",
                    "predictions_weekly": "/predictions/weekly-average または /api/predictions/weekly-average",
                    "supabase_sync": "/supabase/sync または /api/supabase/sync"
                },
                "data_source": "supabase_only",
                "configuration": {
                    "supabase_url_configured": bool(os.getenv('SUPABASE_URL')),
                    "supabase_key_configured": bool(os.getenv('SUPABASE_ANON_KEY'))
                }
            }
            
            # ステータスコードの決定
            status_code = 200 if database_status else 503
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(f"ヘルスチェック中にエラーが発生しました: {str(e)}")
    
    def send_error_response(self, error_message):
        """エラーレスポンスを送信"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        error_data = {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
            "message": "Supabaseデータベースの設定を確認してください。SUPABASE_SETUP.mdを参照してください。"
        }
        
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def test_supabase_connection(self):
        """Supabaseデータベース接続をテスト"""
        try:
            # 環境変数の確認
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                return False, {
                    "status": "disconnected",
                    "error": "環境変数が設定されていません",
                    "missing_vars": [
                        var for var in ['SUPABASE_URL', 'SUPABASE_ANON_KEY'] 
                        if not os.getenv(var)
                    ]
                }
            
            # Supabase REST API呼び出し（テスト用）
            url = f"{supabase_url}/rest/v1/density_history"
            params = {
                'select': 'count',
                'limit': '1'
            }
            
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            req = urllib.request.Request(full_url)
            req.add_header('apikey', supabase_key)
            req.add_header('Authorization', f'Bearer {supabase_key}')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    # データ件数の取得
                    data_count = self.get_data_count(supabase_url, supabase_key)
                    
                    return True, {
                        "status": "connected",
                        "url": supabase_url,
                        "table": "density_history",
                        "total_records": data_count,
                        "last_checked": datetime.now().isoformat(),
                        "connection_test": "success"
                    }
                else:
                    return False, {
                        "status": "disconnected",
                        "error": f"HTTP {response.status}",
                        "url": supabase_url
                    }
                    
        except Exception as e:
            return False, {
                "status": "disconnected",
                "error": str(e),
                "url": supabase_url if 'supabase_url' in locals() else "未設定"
            }
    
    def get_data_count(self, supabase_url, supabase_key):
        """データ件数を取得"""
        try:
            # 過去30日間のデータ件数を取得
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            url = f"{supabase_url}/rest/v1/density_history"
            params = {
                'select': '*',
                'created_at': f'gte.{thirty_days_ago}',
                'limit': '1000'
            }
            
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            req = urllib.request.Request(full_url)
            req.add_header('apikey', supabase_key)
            req.add_header('Authorization', f'Bearer {supabase_key}')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return len(data) if isinstance(data, list) else 0
                else:
                    return 0
                    
        except Exception:
            return 0 