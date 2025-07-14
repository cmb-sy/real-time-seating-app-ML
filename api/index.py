"""
APIサーバー
"""

import json
from http.server import BaseHTTPRequestHandler

# JSONファイルのパス
WEEKLY_PREDICTIONS_FILE = "weekly_predictions.json"
WEEKLY_AVERAGES_FILE = "weekly_averages.json"
LAST_UPDATE_FILE = "last_update.json"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストに対応"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            path = self.path
            if path == "/api/predictions/weekly":
                self.handle_weekly_predictions()
            elif path == "/api/predictions/weekly-averages":
                self.handle_weekly_averages()
            elif path == "/api/predictions/update":
                self.handle_update_predictions()
            elif path == "/docs" or path == "/":
                self.handle_docs()
            else:
                self.send_error_response("Endpoint not found", 404)
        except Exception as e:
            self.send_error_response(f"Internal server error: {str(e)}")

    def send_json_response(self, data, status_code=200):
        """JSON レスポンスを送信"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response_json.encode("utf-8"))

    def send_error_response(self, message, status_code=500):
        """エラーレスポンスを送信"""
        error_data = {"success": False, "error": message}
        self.send_json_response(error_data, status_code)

    def handle_docs(self):
        """API ドキュメンテーション"""
        docs_data = {
            "title": "Prediction API",
            "version": "3.0.0",
            "description": "座席占有率予測API - 週間予測と週間平均値を提供",
            "endpoints": [
                {
                    "path": "/api/predictions/weekly",
                    "method": "GET",
                    "description": "今日から1週間分（7日間）の予測データを取得（土日含む、土日は占有率0）",
                },
                {
                    "path": "/api/predictions/weekly-averages",
                    "method": "GET",
                    "description": "平日の曜日別統計平均値を取得",
                },
            ],
        }
        self.send_json_response(docs_data)

    def handle_weekly_predictions(self):
        """週間予測API（7日間、土日含む）"""
        try:
            with open(WEEKLY_PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                predictions = json.load(f)
                self.send_json_response({"success": True, "data": predictions})
        except Exception as e:
            self.send_error_response(f"Failed to get weekly predictions: {str(e)}")

    def handle_weekly_averages(self):
        """週間平均API（平日の統計平均値）"""
        try:
            with open(WEEKLY_AVERAGES_FILE, "r", encoding="utf-8") as f:
                weekly_averages = json.load(f)
                self.send_json_response({"success": True, "data": weekly_averages})
        except Exception as e:
            self.send_error_response(f"Failed to get weekly averages: {str(e)}")

    def handle_update_predictions(self):
        """予測データ更新情報API"""
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                update_info = json.load(f)
                self.send_json_response({"success": True, "data": update_info})
        except Exception as e:
            self.send_error_response(f"Failed to get update info: {str(e)}")
