"""
APIサーバー
"""

import os
import json
from http.server import BaseHTTPRequestHandler


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
            elif path == "/docs" or path == "/" or path == "/api":
                self.handle_docs()
            else:
                self.send_error_response("Endpoint not found", 404)
        except Exception as e:
            self.send_error_response(f"Internal server error: {str(e)}")

    def get_file_path(self, filename):
        """ファイルパスを取得（複数の場所を試行）"""
        # 現在のディレクトリ
        if os.path.exists(filename):
            return filename

        # apiディレクトリ内
        api_path = os.path.join("api", filename)
        if os.path.exists(api_path):
            return api_path

        # 親ディレクトリのapiフォルダ
        parent_api_path = os.path.join("..", "api", filename)
        if os.path.exists(parent_api_path):
            return parent_api_path

        # プロジェクトルートのapiフォルダ
        root_api_path = os.path.join("/tmp", "api", filename)
        if os.path.exists(root_api_path):
            return root_api_path

        return None

    def send_json_response(self, data, status_code=200):
        """JSON レスポンスを送信"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode("utf-8"))

    def send_error_response(self, message, status_code=500):
        """エラーレスポンスを送信"""
        error_data = {
            "success": False,
            "error": message,
            "debug_info": {
                "working_directory": os.getcwd(),
                "files_in_current_dir": os.listdir("."),
                "environment": "vercel" if os.environ.get("VERCEL") else "local",
            },
        }
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
                    "description": "今日から1週間分（7日間）の予測データを取得",
                },
                {
                    "path": "/api/predictions/weekly-averages",
                    "method": "GET",
                    "description": "平日の曜日別統計平均値を取得",
                },
                {
                    "path": "/api/predictions/update",
                    "method": "GET",
                    "description": "最終更新時刻を取得",
                },
            ],
            "debug_info": {
                "working_directory": os.getcwd(),
                "files_available": os.listdir("."),
                "environment": "vercel" if os.environ.get("VERCEL") else "local",
            },
        }
        self.send_json_response(docs_data)

    def handle_weekly_predictions(self):
        """週間予測API（7日間、土日含む）"""
        try:
            file_path = self.get_file_path("weekly_predictions.json")
            if not file_path:
                self.send_error_response(
                    "weekly_predictions.json が見つかりません", 404
                )
                return

            with open(file_path, "r", encoding="utf-8") as f:
                predictions = json.load(f)
                self.send_json_response({"success": True, "data": predictions})
        except Exception as e:
            self.send_error_response(f"Failed to get weekly predictions: {str(e)}")

    def handle_weekly_averages(self):
        """週間平均API（平日の統計平均値）"""
        try:
            file_path = self.get_file_path("weekly_averages.json")
            if not file_path:
                self.send_error_response("weekly_averages.json が見つかりません", 404)
                return

            with open(file_path, "r", encoding="utf-8") as f:
                weekly_averages = json.load(f)
                self.send_json_response({"success": True, "data": weekly_averages})
        except Exception as e:
            self.send_error_response(f"Failed to get weekly averages: {str(e)}")

    def handle_update_predictions(self):
        """予測データ更新情報API"""
        try:
            file_path = self.get_file_path("last_update.json")
            if not file_path:
                self.send_error_response("last_update.json が見つかりません", 404)
                return

            with open(file_path, "r", encoding="utf-8") as f:
                update_info = json.load(f)
                self.send_json_response({"success": True, "data": update_info})
        except Exception as e:
            self.send_error_response(f"Failed to get update info: {str(e)}")
