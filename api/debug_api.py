"""
デバッグ版APIサーバー
"""
import sys
import json
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

class DebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            print(f"📥 リクエスト: {self.path}")
            
            if self.path == '/test':
                self.send_test_response()
            elif self.path == '/api/predictions/today-tomorrow':
                self.send_prediction_response()
            else:
                self.send_404_response()
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            traceback.print_exc()
            self.send_error_response(str(e))
    
    def send_test_response(self):
        """テストレスポンス"""
        print("📤 テストレスポンス送信")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        data = {"message": "server is working", "path": self.path}
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        print("✅ テストレスポンス完了")
    
    def send_prediction_response(self):
        """予測レスポンス（簡易版）"""
        print("📤 予測レスポンス送信")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 簡単なダミーデータ
        data = {
            "success": True,
            "data": {
                "today": {"predicted_count": 150, "confidence": 0.85},
                "tomorrow": {"predicted_count": 180, "confidence": 0.82}
            }
        }
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        print("✅ 予測レスポンス完了")
    
    def send_404_response(self):
        """404レスポンス"""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        data = {"error": "Not Found", "path": self.path}
        response_json = json.dumps(data)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, error_msg):
        """エラーレスポンス"""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        data = {"error": error_msg}
        response_json = json.dumps(data)
        self.wfile.write(response_json.encode('utf-8'))

if __name__ == '__main__':
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, DebugHandler)
    print("🚀 デバッグサーバー起動")
    print("📍 テスト: http://localhost:8000/test")
    print("📍 予測API: http://localhost:8000/api/predictions/today-tomorrow")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 サーバー停止")
        httpd.server_close()