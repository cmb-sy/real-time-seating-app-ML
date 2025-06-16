"""
API共通レスポンス処理ヘルパー
"""
import json
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Type

def send_cors_headers(handler: BaseHTTPRequestHandler):
    """CORS関連のヘッダーを設定"""
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin, Accept, X-Requested-With')
    handler.send_header('Access-Control-Max-Age', '86400')  # 24時間キャッシュ

def send_success_response(handler: BaseHTTPRequestHandler, data: dict):
    """成功レスポンスを送信"""
    handler.send_response(200)
    handler.send_header('Content-type', 'application/json')
    send_cors_headers(handler)
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def send_error_response(handler: BaseHTTPRequestHandler, error_message: str):
    """エラーレスポンスを送信"""
    handler.send_response(500)
    handler.send_header('Content-type', 'application/json')
    send_cors_headers(handler)
    handler.end_headers()
    
    error_data = {
        "success": False,
        "error": error_message
    }
    
    handler.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))

def send_options_response(handler: BaseHTTPRequestHandler):
    """プリフライトリクエストへの対応"""
    handler.send_response(200)
    send_cors_headers(handler)
    handler.end_headers()

def send_head_response(handler: BaseHTTPRequestHandler):
    """HEADリクエストへの対応"""
    handler.send_response(200)
    handler.send_header('Content-type', 'application/json')
    send_cors_headers(handler)
    handler.end_headers()

def run_server(handler_class: Type[BaseHTTPRequestHandler], port=8000, server_name="API"):
    """
    HTTPサーバーを起動する汎用関数
    
    Args:
        handler_class: リクエストを処理するハンドラークラス
        port (int): サーバーのポート番号
        server_name (str): サーバーの名前（ログ表示用）
    """
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

def parse_port_arg(description="APIサーバーを起動します", default_port=8000):
    """
    コマンドライン引数からポート番号を解析する関数
    
    Args:
        description (str): コマンドの説明
        default_port (int): デフォルトのポート番号
    
    Returns:
        int: ポート番号
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--port', type=int, default=default_port, 
                       help=f'サーバーのポート番号（デフォルト: {default_port}）')
    args = parser.parse_args()
    return args.port 