from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS プリフライトリクエストの処理"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        """GET リクエストの処理"""
        try:
            path = urlparse(self.path).path
            
            # CORS ヘッダーを設定
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
            self.send_header("Access-Control-Max-Age", "86400")
            self.end_headers()

            # パスに応じてレスポンスを生成
            if path in ["/api/predictions/today-tomorrow", "/predictions/today-tomorrow"]:
                response_data = self.handle_today_tomorrow()
            elif path in ["/api/predictions/weekly-average", "/predictions/weekly-average"]:
                response_data = self.handle_weekly_average()
            elif path in ["/", ""]:
                response_data = self.handle_root()
            else:
                response_data = {
                    "success": False,
                    "error": f"エンドポイントが見つかりません: {path}",
                    "available_endpoints": [
                        "/api/predictions/today-tomorrow",
                        "/api/predictions/weekly-average"
                    ]
                }

            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            # エラー時もCORSヘッダーを設定
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            
            error_response = {
                "success": False,
                "error": f"本番APIサーバーエラー: {str(e)}",
                "environment": "production",
                "debug_info": {
                    "error_type": type(e).__name__,
                    "path": getattr(self, "path", "unknown")
                }
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8"))

    def get_ml_prediction(self, day_of_week):
        """機械学習予測（本番用 - モデルファイル対応）"""
        try:
            # 土日は0を返す
            if day_of_week >= 5:
                return {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0,
                    "prediction_method": "weekend_rule"
                }

            # フォールバック値（モデルが読み込めない場合）
            weekday_averages = {
                0: {"occupancy_rate": 0.65, "occupied_seats": 5},  # 月曜日
                1: {"occupancy_rate": 0.75, "occupied_seats": 6},  # 火曜日
                2: {"occupancy_rate": 0.70, "occupied_seats": 6},  # 水曜日
                3: {"occupancy_rate": 0.80, "occupied_seats": 6},  # 木曜日
                4: {"occupancy_rate": 0.60, "occupied_seats": 5},  # 金曜日
            }
            
            fallback_prediction = weekday_averages.get(day_of_week, {"occupancy_rate": 0.5, "occupied_seats": 4})

            try:
                # 機械学習モデルの読み込みを試行
                import joblib
                import numpy as np
                
                density_model = joblib.load("density_model.joblib")
                seats_model = joblib.load("seats_model.joblib")
                
                # 10個の特徴量を作成
                features = np.zeros((1, 10))
                features[0, 0] = day_of_week
                features[0, 1] = 0.1  # density_seats_ratio
                if day_of_week < 5:  # 平日のみ
                    features[0, 2 + day_of_week] = 1  # 曜日ダミー変数
                features[0, 7] = 1 if day_of_week in [0, 1] else 0  # is_early_week
                features[0, 8] = 1 if day_of_week == 2 else 0       # is_mid_week
                features[0, 9] = 1 if day_of_week in [3, 4] else 0  # is_late_week
                
                # 予測実行
                density_pred = density_model.predict(features)[0]
                seats_pred = seats_model.predict(features)[0]
                
                # 予測値を正規化
                occupancy_rate = max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred))
                occupied_seats = max(0, min(8, int(round(seats_pred))))
                
                return {
                    "occupancy_rate": round(occupancy_rate, 2),
                    "occupied_seats": occupied_seats,
                    "prediction_method": "ml_model"
                }
                
            except Exception as model_error:
                # モデル読み込み失敗時はフォールバック値を使用
                fallback_prediction["prediction_method"] = "fallback"
                fallback_prediction["model_error"] = str(model_error)
                return fallback_prediction

        except Exception as e:
            return {
                "occupancy_rate": 0.0,
                "occupied_seats": 0,
                "prediction_method": "error",
                "error": str(e)
            }

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
                "environment": "production",
                "server_type": "vercel_serverless",
                "data": {
                    "today": {
                        "weekday": today.weekday(),
                        "weekday_name": weekday_names[today.weekday()],
                        "occupancy_rate": today_prediction["occupancy_rate"],
                        "occupied_seats": today_prediction["occupied_seats"],
                        "prediction_method": today_prediction.get("prediction_method", "unknown")
                    },
                    "tomorrow": {
                        "weekday": tomorrow.weekday(),
                        "weekday_name": weekday_names[tomorrow.weekday()],
                        "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                        "occupied_seats": tomorrow_prediction["occupied_seats"],
                        "prediction_method": tomorrow_prediction.get("prediction_method", "unknown")
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": f"今日・明日予測エラー: {str(e)}", "environment": "production"}

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
                    "occupied_seats": prediction["occupied_seats"],
                    "prediction_method": prediction.get("prediction_method", "unknown")
                })

            return {
                "success": True,
                "environment": "production",
                "server_type": "vercel_serverless",
                "data": {
                    "weekly_averages": weekly_averages
                }
            }
        except Exception as e:
            return {"success": False, "error": f"週間平均予測エラー: {str(e)}", "environment": "production"}

    def handle_root(self):
        """ルートパスでのAPI情報表示"""
        try:
            # モデルファイルの存在確認
            model_files = ["density_model.joblib", "seats_model.joblib", "best_params.joblib", "model_performance.joblib"]
            model_status = {}
            for model_file in model_files:
                try:
                    model_status[model_file] = os.path.exists(model_file)
                except:
                    model_status[model_file] = False
            
            return {
                "success": True,
                "message": "リアルタイム座席予測API（本番環境）",
                "version": "1.0.0",
                "environment": "production",
                "server_type": "vercel_serverless",
                "endpoints": {
                    "today_tomorrow": "/api/predictions/today-tomorrow",
                    "weekly_average": "/api/predictions/weekly-average"
                },
                "model_status": model_status,
                "status": "運用中"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API情報取得エラー: {str(e)}",
                "environment": "production"
            }
