from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
            self.send_header("Access-Control-Max-Age", "86400")
            self.end_headers()
            if path in ["/api/predictions/today-tomorrow", "/predictions/today-tomorrow"]:
                response_data = self.handle_today_tomorrow()
            elif path in ["/api/predictions/weekly-average", "/predictions/weekly-average"]:
                response_data = self.handle_weekly_average()
            elif path in ["/", ""]:
                response_data = self.handle_root()
            else:
                response_data = {"success": False, "error": f"エンドポイントが見つかりません: {path}"}
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            error_response = {"success": False, "error": f"サーバーエラー: {str(e)}"}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8"))

    def get_ml_prediction(self, day_of_week):
        if day_of_week >= 5:
            return {"occupancy_rate": 0.0, "occupied_seats": 0}
        weekday_averages = {0: {"occupancy_rate": 0.65, "occupied_seats": 5}, 1: {"occupancy_rate": 0.75, "occupied_seats": 6}, 2: {"occupancy_rate": 0.70, "occupied_seats": 6}, 3: {"occupancy_rate": 0.80, "occupied_seats": 6}, 4: {"occupancy_rate": 0.60, "occupied_seats": 5}}
        return weekday_averages.get(day_of_week, {"occupancy_rate": 0.5, "occupied_seats": 4})

    def handle_today_tomorrow(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        return {"success": True, "data": {"today": {"weekday": today.weekday(), "weekday_name": weekday_names[today.weekday()], **self.get_ml_prediction(today.weekday())}, "tomorrow": {"weekday": tomorrow.weekday(), "weekday_name": weekday_names[tomorrow.weekday()], **self.get_ml_prediction(tomorrow.weekday())}}}

    def handle_weekly_average(self):
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        weekly_averages = []
        for day in range(5):
            prediction = self.get_ml_prediction(day)
            weekly_averages.append({"weekday": day, "weekday_name": weekday_names[day], **prediction})
        return {"success": True, "data": {"weekly_averages": weekly_averages}}

    def handle_root(self):
        return {"success": True, "message": "リアルタイム座席予測API", "version": "1.0.0", "endpoints": {"today_tomorrow": "/api/predictions/today-tomorrow", "weekly_average": "/api/predictions/weekly-average"}, "status": "運用中", "environment": "production"}
