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
WEEKLY_PREDICTIONS_FILE = os.path.join(data_dir, 'weekly_predictions.json')
WEEKLY_AVERAGES_FILE = os.path.join(data_dir, 'weekly_averages.json')
LAST_UPDATE_FILE = os.path.join(data_dir, 'last_update.json')
MODEL_INFO_FILE = os.path.join(data_dir, 'model_info.json')

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストに対応"""
        send_options_response(self)
    
    def do_GET(self):
        try:
            path = self.path
            if path == '/api/predictions/weekly':
                self.handle_weekly_predictions()
            elif path == '/api/predictions/weekly-averages':
                self.handle_weekly_averages()
            elif path == '/api/predictions/update':
                self.handle_update_predictions()
            elif path == '/api/model/info':
                self.handle_model_info()
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
                "version": "3.0.0",
                "description": "座席占有率予測API - 週間予測と週間平均値を提供",
                "endpoints": [
                    {
                        "path": "/api/predictions/weekly",
                        "method": "GET",
                        "description": "今日から1週間分（7日間）の予測データを取得（土日含む、土日は占有率0）"
                    },
                    {
                        "path": "/api/predictions/weekly-averages",
                        "method": "GET", 
                        "description": "平日の曜日別統計平均値を取得"
                    },
                    {
                        "path": "/api/model/info",
                        "method": "GET",
                        "description": "アンサンブルモデルの詳細情報を取得"
                    }
                ],
                "data_types": {
                    "weekly_predictions": "機械学習モデルによる予測値またはデータベース平均値",
                    "weekly_averages": "データベースから計算された統計平均値"
                }
            }
            send_json_response(self, docs_data)
        except Exception as e:
            send_error_response(self, f"Failed to load docs: {str(e)}")
         
    def handle_weekly_predictions(self):
        """週間予測API（7日間、土日含む）"""
        try:
            # JSONファイルからデータを読み込む
            with open(WEEKLY_PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
                predictions = json.load(f)     
                response_data = {
                    "success": True,
                    "data": predictions,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to get weekly predictions: {str(e)}")
    
    def handle_weekly_averages(self):
        """週間平均API（平日の統計平均値）"""
        try:
            # JSONファイルからデータを読み込む
            with open(WEEKLY_AVERAGES_FILE, 'r', encoding='utf-8') as f:
                weekly_averages = json.load(f)
                    
                response_data = {
                    "success": True,
                    "data": weekly_averages,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to get weekly averages: {str(e)}")
    
    def handle_update_predictions(self):
        """予測データ更新情報API"""
        try:
            # 更新情報JSONファイルからデータを読み込む
            with open(LAST_UPDATE_FILE, 'r', encoding='utf-8') as f:
                update_info = json.load(f)
                    
                response_data = {
                    "success": True,
                    "data": update_info,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to get update info: {str(e)}")
    
    def handle_model_info(self):
        """モデル情報API"""
        try:
            # モデル情報JSONファイルからデータを読み込む
            if not os.path.exists(MODEL_INFO_FILE):
                send_error_response(self, "Model info not available. Please run 'python utils/train.py --mode export' first.", 404)
                return
                
            with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
                model_info = json.load(f)
                    
                response_data = {
                    "success": True,
                    "data": model_info,
                }
                send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to get model info: {str(e)}")

if __name__ == '__main__':
    run_server(handler, 8000, "Prediction API")