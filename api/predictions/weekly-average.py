"""
週間平均予測データを提供するVercelサーバーレス関数
"""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """OPTIONSリクエストへの応答"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """GETリクエストへの応答"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        # サンプルデータ
        weekday_predictions = {
            "月曜": {"day_of_week": 0, "weekday_name": "月曜", "predictions": {"density_rate": 0.75, "occupied_seats": 45}},
            "火曜": {"day_of_week": 1, "weekday_name": "火曜", "predictions": {"density_rate": 0.65, "occupied_seats": 39}},
            "水曜": {"day_of_week": 2, "weekday_name": "水曜", "predictions": {"density_rate": 0.80, "occupied_seats": 48}},
            "木曜": {"day_of_week": 3, "weekday_name": "木曜", "predictions": {"density_rate": 0.70, "occupied_seats": 42}},
            "金曜": {"day_of_week": 4, "weekday_name": "金曜", "predictions": {"density_rate": 0.55, "occupied_seats": 33}}
        }
        
        # 週平均
        weekly_average = {
            "average_density_rate": 0.69,
            "average_occupied_seats": 41.4,
            "total_weekdays": 5
        }
        
        # レスポンスデータ
        response_data = {
            "success": True,
            "data": {
                "weekly_average": weekly_average,
                "daily_predictions": weekday_predictions
            },
            "message": "週平均予測データを取得しました (サンプルデータ)"
        }
        
        # JSONレスポンスを返す
        self.wfile.write(json.dumps(response_data).encode('utf-8')) 