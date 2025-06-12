"""
今日と明日の予測データを提供するVercelサーバーレス関数
"""
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """今日・明日の座席予測データを返す"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        # 現在の日時を取得
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        current_hour = now.hour
        
        # 今日の予測データ（現在時刻以降のみ）
        today_predictions = []
        for hour in range(max(9, current_hour), 19):  # 9時から18時まで、現在時刻以降
            # 時間帯に応じた占有率の計算（リアルなパターン）
            if hour < 11:
                base_rate = 0.2 + (hour - 9) * 0.1  # 朝は徐々に増加
            elif hour < 13:
                base_rate = 0.7 + (hour - 11) * 0.1  # 昼前後はピーク
            elif hour < 15:
                base_rate = 0.8 - (hour - 13) * 0.1  # 午後は減少
            else:
                base_rate = 0.6 + (hour - 15) * 0.05  # 夕方は再び増加
            
            # 曜日による調整
            weekday = today.weekday()
            if weekday >= 5:  # 土日
                base_rate *= 0.6
            elif weekday == 4:  # 金曜日
                base_rate *= 1.1
            
            # 占有率を0-1の範囲に制限
            occupancy_rate = min(max(base_rate, 0.05), 0.98)
            available_seats = int(100 * (1 - occupancy_rate))
            
            today_predictions.append({
                "hour": hour,
                "occupancy_rate": round(occupancy_rate, 2),
                "available_seats": available_seats,
                "status": "busy" if occupancy_rate > 0.8 else "moderate" if occupancy_rate > 0.5 else "available"
            })
        
        # 明日の予測データ（全時間帯）
        tomorrow_predictions = []
        tomorrow_weekday = tomorrow.weekday()
        
        for hour in range(9, 19):  # 9時から18時まで
            # 時間帯に応じた占有率の計算
            if hour < 11:
                base_rate = 0.25 + (hour - 9) * 0.12
            elif hour < 13:
                base_rate = 0.75 + (hour - 11) * 0.1
            elif hour < 15:
                base_rate = 0.85 - (hour - 13) * 0.15
            else:
                base_rate = 0.55 + (hour - 15) * 0.08
            
            # 曜日による調整
            if tomorrow_weekday >= 5:  # 土日
                base_rate *= 0.5
            elif tomorrow_weekday == 4:  # 金曜日
                base_rate *= 1.15
            elif tomorrow_weekday == 0:  # 月曜日
                base_rate *= 1.05
            
            # 占有率を0-1の範囲に制限
            occupancy_rate = min(max(base_rate, 0.05), 0.98)
            available_seats = int(100 * (1 - occupancy_rate))
            
            tomorrow_predictions.append({
                "hour": hour,
                "occupancy_rate": round(occupancy_rate, 2),
                "available_seats": available_seats,
                "status": "busy" if occupancy_rate > 0.8 else "moderate" if occupancy_rate > 0.5 else "available"
            })
        
        # レスポンスデータ
        response_data = {
            "success": True,
            "timestamp": now.isoformat(),
            "data": {
                "today": {
                    "date": today.isoformat(),
                    "day_of_week": ["月", "火", "水", "木", "金", "土", "日"][today.weekday()],
                    "predictions": today_predictions,
                    "total_hours": len(today_predictions)
                },
                "tomorrow": {
                    "date": tomorrow.isoformat(),
                    "day_of_week": ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()],
                    "predictions": tomorrow_predictions,
                    "total_hours": len(tomorrow_predictions)
                }
            },
            "metadata": {
                "model_version": "2.0.0",
                "last_updated": now.isoformat(),
                "confidence": "high",
                "data_source": "historical_patterns"
            }
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8')) 