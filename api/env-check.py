"""
環境変数確認用エンドポイント
"""
import os
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 環境変数の詳細確認
            env_check = {
                "success": True,
                "message": "環境変数確認エンドポイント",
                "environment_variables": {
                    # Supabase関連の環境変数
                    "NEXT_PUBLIC_SUPABASE_URL": {
                        "exists": bool(os.environ.get('NEXT_PUBLIC_SUPABASE_URL')),
                        "value_preview": os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'NOT_SET')[:50] + "..." if os.environ.get('NEXT_PUBLIC_SUPABASE_URL') else "NOT_SET",
                        "length": len(os.environ.get('NEXT_PUBLIC_SUPABASE_URL', ''))
                    },
                    "SUPABASE_SERVICE_ROLE_KEY": {
                        "exists": bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY')),
                        "value_preview": os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'NOT_SET')[:50] + "..." if os.environ.get('SUPABASE_SERVICE_ROLE_KEY') else "NOT_SET",
                        "length": len(os.environ.get('SUPABASE_SERVICE_ROLE_KEY', ''))
                    },
                    "NEXT_PUBLIC_SUPABASE_ANON_KEY": {
                        "exists": bool(os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')),
                        "value_preview": os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'NOT_SET')[:50] + "..." if os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') else "NOT_SET",
                        "length": len(os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', ''))
                    },
                    # Vercel関連の環境変数
                    "VERCEL": os.environ.get('VERCEL', 'NOT_SET'),
                    "VERCEL_ENV": os.environ.get('VERCEL_ENV', 'NOT_SET'),
                    "VERCEL_URL": os.environ.get('VERCEL_URL', 'NOT_SET'),
                },
                "all_env_keys": [key for key in os.environ.keys() if 'SUPABASE' in key.upper()],
                "total_env_count": len(os.environ)
            }
            
            # Supabaseライブラリのインポートテスト
            try:
                from supabase import create_client, Client
                env_check["supabase_library"] = {
                    "status": "✅ インポート成功",
                    "version": "確認中..."
                }
                
                # 実際の接続テスト（環境変数が存在する場合のみ）
                supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
                supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
                
                if supabase_url and supabase_key:
                    try:
                        supabase = create_client(supabase_url, supabase_key)
                        env_check["connection_test"] = "✅ クライアント作成成功"
                        
                        # 簡単なクエリテスト
                        response = supabase.table('density_history').select('*').limit(1).execute()
                        env_check["database_test"] = {
                            "status": "✅ データベース接続成功",
                            "data_count": len(response.data) if response.data else 0
                        }
                    except Exception as conn_error:
                        env_check["connection_test"] = f"❌ 接続エラー: {str(conn_error)}"
                else:
                    env_check["connection_test"] = "❌ 必要な環境変数が不足"
                    
            except ImportError as import_error:
                env_check["supabase_library"] = {
                    "status": f"❌ インポートエラー: {str(import_error)}",
                    "suggestion": "requirements-vercel.txtを確認してください"
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(env_check, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"環境変数確認でエラーが発生しました: {str(e)}",
                "error_type": type(e).__name__
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8')) 