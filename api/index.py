"""
APIサーバー
"""
import sys
import os
import json
sys.path.append('utils')

from http.server import BaseHTTPRequestHandler
from response_helper import send_json_response, send_error_response, send_options_response, run_server

# データディレクトリのパス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
data_dir = os.path.join(project_root, 'api')

# JSONファイルのパス
TODAY_TOMORROW_FILE = os.path.join(data_dir, 'today_tomorrow_predictions.json')
WEEKLY_AVERAGES_FILE = os.path.join(data_dir, 'weekly_averages_predictions.json')
LAST_UPDATE_FILE = os.path.join(data_dir, 'last_update.json')

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストに対応"""
        send_options_response(self)
    
    def do_GET(self):
        try:
            path = self.path
            if path == '/api/predictions/today-tomorrow':
                self.handle_today_tomorrow()
            elif path == '/api/predictions/weekly-average':
                self.handle_weekly_average()
            elif path == '/api/predictions/update':
                self.handle_update_predictions()
            elif path == '/docs' or path == '/':
                self.handle_docs()
            else:
                send_error_response(self, "Endpoint not found", 404)
        except Exception as e:
            send_error_response(self, f"Internal server error: {str(e)}")
    
    def handle_docs(self):
        """API ドキュメンテーション"""
        try:
            docs_data = {
                "title": "Prediction API",
                "version": "1.0.0",
                "endpoints": [
                    {
                        "path": "/api/predictions/today-tomorrow",
                        "method": "GET",
                        "description": "今日・明日の予測データを取得"
                    },
                    {
                        "path": "/api/predictions/weekly-average",
                        "method": "GET", 
                        "description": "週間平均予測データを取得"
                    },
                    {
                        "path": "/api/predictions/update",
                        "method": "GET",
                        "description": "予測データを更新"
                    }
                ]
            }
            send_json_response(self, docs_data)
        except Exception as e:
            send_error_response(self, f"Failed to load docs: {str(e)}")
         
    def handle_today_tomorrow(self):
        """今日・明日予測API"""
        try:
            # JSONファイルからデータを読み込む
            with open(TODAY_TOMORROW_FILE, 'r', encoding='utf-8') as f:
                predictions = json.load(f)     
                response_data = {
                    "success": True,
                    "data": predictions,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to get predictions: {str(e)}")
    
    def handle_weekly_average(self):
        """週間平均予測API"""
        try:
            # JSONファイルからデータを読み込む
            with open(WEEKLY_AVERAGES_FILE, 'r', encoding='utf-8') as f:
                weekly_predictions = json.load(f)
                    
                response_data = {
                    "success": True,
                    "data": weekly_predictions,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to calculate weekly averages: {str(e)}")

if __name__ == '__main__':
    run_server(handler, 8000, "Prediction API")