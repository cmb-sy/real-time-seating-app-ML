"""
API共通レスポンス処理ヘルパー
"""
import json
from http.server import BaseHTTPRequestHandler

def send_cors_headers(handler: BaseHTTPRequestHandler):
    """CORS関連のヘッダーを設定"""
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')

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
    handler.send_header('Access-Control-Max-Age', '86400')
    handler.end_headers() 