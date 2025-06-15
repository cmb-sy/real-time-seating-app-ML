"""
Vercel用統合API - 単一ファイルで全機能を提供
依存関係を最小限に抑えたスタンドアロン版
"""
import os
import json
import joblib
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timedelta

# 環境変数の取得
NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class VercelHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """GETリクエスト処理"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # CORS ヘッダーを設定
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.end_headers()
            
            if path == "/api/predictions/today-tomorrow":
                response = self.handle_today_tomorrow()
            elif path == "/api/predictions/weekly-average":
                response = self.handle_weekly_average()
            else:
                response = {"success": False, "error": f"エンドポイントが見つかりません: {path}"}
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def handle_today_tomorrow(self):
        """今日・明日の予測"""
        try:
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            
            today_prediction = self.get_ml_prediction(today.weekday())
            tomorrow_prediction = self.get_ml_prediction(tomorrow.weekday())
            
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            
            return {
                "success": True,
                "data": {
                    "today": {
                        "weekday": today.weekday(),
                        "weekday_name": weekday_names[today.weekday()],
                        "occupancy_rate": today_prediction["occupancy_rate"],
                        "occupied_seats": today_prediction["occupied_seats"]
                    },
                    "tomorrow": {
                        "weekday": tomorrow.weekday(),
                        "weekday_name": weekday_names[tomorrow.weekday()],
                        "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                        "occupied_seats": tomorrow_prediction["occupied_seats"]
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": f"今日・明日予測エラー: {str(e)}"}
    
    def handle_weekly_average(self):
        """週間平均予測"""
        try:
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            weekly_averages = []
            
            for day in range(5):  # 平日のみ
                prediction = self.get_ml_prediction(day)
                weekly_averages.append({
                    "weekday": day,
                    "weekday_name": weekday_names[day],
                    "occupancy_rate": prediction["occupancy_rate"],
                    "occupied_seats": prediction["occupied_seats"]
                })
            
            return {
                "success": True,
                "data": {
                    "weekly_averages": weekly_averages
                }
            }
        except Exception as e:
            return {"success": False, "error": f"週間平均予測エラー: {str(e)}"}
    
    def get_ml_prediction(self, day_of_week):
        """機械学習予測（簡易版）"""
        try:
            # 土日は0を返す
            if day_of_week >= 5:
                return {"occupancy_rate": 0.0, "occupied_seats": 0}
            
            # 簡易的な予測値（実際のモデルファイルが読み込めない場合のフォールバック）
            # 曜日別の平均的な値を使用
            weekday_averages = {
                0: {"occupancy_rate": 0.65, "occupied_seats": 5},  # 月曜日
                1: {"occupancy_rate": 0.75, "occupied_seats": 6},  # 火曜日
                2: {"occupancy_rate": 0.70, "occupied_seats": 6},  # 水曜日
                3: {"occupancy_rate": 0.80, "occupied_seats": 6},  # 木曜日
                4: {"occupancy_rate": 0.60, "occupied_seats": 5},  # 金曜日
            }
            
            try:
                # モデルファイルの読み込みを試行
                density_model = joblib.load('density_model.joblib')
                seats_model = joblib.load('seats_model.joblib')
                
                # 10個の特徴量を作成
                features = np.zeros((1, 10))
                features[0, 0] = day_of_week
                features[0, 1] = 0.1  # density_seats_ratio
                features[0, 2 + day_of_week] = 1  # 曜日ダミー変数
                features[0, 7] = 1 if day_of_week in [0, 1] else 0  # is_early_week
                features[0, 8] = 1 if day_of_week == 2 else 0       # is_mid_week
                features[0, 9] = 1 if day_of_week in [3, 4] else 0  # is_late_week
                
                # 予測実行
                density_pred = density_model.predict(features)[0]
                seats_pred = seats_model.predict(features)[0]
                
                return {
                    "occupancy_rate": max(0.0, min(1.0, density_pred)),
                    "occupied_seats": max(0, int(round(seats_pred)))
                }
                
            except Exception:
                # モデルファイルが読み込めない場合は平均値を使用
                return weekday_averages.get(day_of_week, {"occupancy_rate": 0.5, "occupied_seats": 4})
                
        except Exception as e:
            return {"occupancy_rate": 0.0, "occupied_seats": 0}

# Vercel用のハンドラー関数
def handler(request, response):
    """Vercel用のメインハンドラー"""
    # HTTPリクエストを処理
    handler_instance = VercelHandler()
    handler_instance.path = request.url
    handler_instance.command = request.method
    
    if request.method == 'OPTIONS':
        handler_instance.do_OPTIONS()
    elif request.method == 'GET':
        handler_instance.do_GET()
    
    return response 