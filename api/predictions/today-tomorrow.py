"""
今日と明日の予測データを提供するVercelサーバーレス関数
"""
from http.server import BaseHTTPRequestHandler
from datetime import datetime
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
        
        # 現在の曜日を取得（0=月曜日）
        today_weekday = datetime.now().weekday()
        tomorrow_weekday = (today_weekday + 1) % 7
        
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜", 5: "土曜", 6: "日曜"}
        
        # サンプルデータ
        sample_predictions = {
            0: {"density_rate": 0.75, "occupied_seats": 45},
            1: {"density_rate": 0.65, "occupied_seats": 39},
            2: {"density_rate": 0.80, "occupied_seats": 48},
            3: {"density_rate": 0.70, "occupied_seats": 42},
            4: {"density_rate": 0.55, "occupied_seats": 33},
        }
        
        # 平日のみ予測可能
        predictions = {}
        
        if today_weekday <= 4:  # 月-金
            predictions["today"] = {
                "day_of_week": today_weekday,
                "weekday_name": weekday_names[today_weekday],
                "predictions": sample_predictions.get(today_weekday, {"density_rate": 0.65, "occupied_seats": 39})
            }
        else:
            predictions["today"] = {
                "day_of_week": today_weekday,
                "weekday_name": weekday_names[today_weekday],
                "predictions": None,
                "message": "土日は予測データがありません"
            }
        
        if tomorrow_weekday <= 4:  # 月-金
            predictions["tomorrow"] = {
                "day_of_week": tomorrow_weekday,
                "weekday_name": weekday_names[tomorrow_weekday],
                "predictions": sample_predictions.get(tomorrow_weekday, {"density_rate": 0.65, "occupied_seats": 39})
            }
        else:
            predictions["tomorrow"] = {
                "day_of_week": tomorrow_weekday,
                "weekday_name": weekday_names[tomorrow_weekday],
                "predictions": None,
                "message": "土日は予測データがありません"
            }
        
        # レスポンスデータ
        response_data = {
            "success": True,
            "data": predictions,
            "message": "今日と明日の予測データを取得しました (サンプルデータ)"
        }
        
        # JSONレスポンスを返す
        self.wfile.write(json.dumps(response_data).encode('utf-8')) 