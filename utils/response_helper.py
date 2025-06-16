"""
API共通レスポンス処理ヘルパー
"""
import json
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Type

def send_json_response(handler: BaseHTTPRequestHandler, data: dict, status_code: int = 200):
    """JSON レスポンスを送信"""
    try:
        # 1. ステータスコードを送信
        handler.send_response(status_code)
        
        # 2. ヘッダーを送信
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin, Accept, X-Requested-With')
        handler.send_header('Access-Control-Max-Age', '86400')
        
        # 3. ヘッダー終了
        handler.end_headers()
        
        # 4. ボディを送信
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        handler.wfile.write(response_json.encode('utf-8'))
        
    except Exception as e:
        print(f"レスポンス送信エラー: {e}")
        raise

def send_error_response(handler: BaseHTTPRequestHandler, error_message: str, status_code: int = 500):
    """エラーレスポンスを送信"""
    error_data = {
        "success": False,
        "error": error_message,
        "status_code": status_code
    }
    send_json_response(handler, error_data, status_code)

def send_options_response(handler: BaseHTTPRequestHandler):
    """プリフライトリクエストへの対応"""
    handler.send_response(200)
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin, Accept, X-Requested-With')
    handler.send_header('Access-Control-Max-Age', '86400')
    handler.end_headers()

def run_server(handler_class: Type[BaseHTTPRequestHandler], port=8000, server_name="API"):
    """HTTPサーバーを起動する汎用関数"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler_class)
    print(f"🚀 {server_name}サーバーを起動しました。http://localhost:{port}/ でアクセスできます。")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\nCtrl+Cが押されました。{server_name}サーバーを停止します。")
    finally:
        httpd.server_close()
        print(f"{server_name}サーバーは停止しました。")