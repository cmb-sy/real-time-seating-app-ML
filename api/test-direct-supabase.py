"""
Supabaseライブラリを使わない直接HTTP接続テスト
"""
import os
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 環境変数の取得
            supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                raise Exception("環境変数が設定されていません")
            
            # Supabase REST APIエンドポイント
            api_url = f"{supabase_url}/rest/v1/density_history"
            
            # HTTPリクエストヘッダー
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            # HTTPリクエストの作成
            req = urllib.request.Request(
                url=f"{api_url}?select=*&limit=3",
                headers=headers,
                method='GET'
            )
            
            # リクエストの実行
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                result = {
                    "success": True,
                    "message": "Supabase直接接続テストに成功しました",
                    "connection_method": "HTTP直接接続（supabaseライブラリなし）",
                    "data_count": len(data),
                    "sample_data": data[:2] if data else [],
                    "supabase_url": supabase_url,
                    "api_endpoint": api_url
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"Supabase直接接続テストでエラーが発生しました: {str(e)}",
                "error_type": type(e).__name__,
                "supabase_url": os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'NOT_SET'),
                "has_key": bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY'))
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8')) 