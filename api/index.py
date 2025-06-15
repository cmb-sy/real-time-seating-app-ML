"""
統合API - GitHub Workflowで訓練されたモデルとSupabase実データを使用
"""
import os
import json
import joblib
import numpy as np
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # パスを解析してエンドポイントを判定
            path = self.path
            
            if path == '/api/predictions/today-tomorrow':
                self.handle_today_tomorrow()
            elif path == '/api/predictions/weekly-average':
                self.handle_weekly_average()
            elif path == '/api/model-info':
                self.handle_model_info()
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response("Internal server error")
    
    def do_OPTIONS(self):
        """CORS preflight request handling"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_supabase_config(self):
        """Supabase設定を取得"""
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("Database configuration error")
            
        return supabase_url, supabase_key
    
    def load_trained_models(self):
        """GitHub Workflowで訓練されたモデルを読み込み"""
        try:
            # モデルファイルのパス
            density_model_path = 'api/density_model.joblib'
            seats_model_path = 'api/seats_model.joblib'
            best_params_path = 'api/best_params.joblib'
            performance_path = 'api/model_performance.joblib'
            
            # モデルを読み込み
            density_model = joblib.load(density_model_path)
            seats_model = joblib.load(seats_model_path)
            best_params = joblib.load(best_params_path)
            performance = joblib.load(performance_path)
            
            return {
                'density_model': density_model,
                'seats_model': seats_model,
                'best_params': best_params,
                'performance': performance
            }
        except Exception as e:
            raise Exception(f"Failed to load trained models: {str(e)}")
    
    def get_supabase_data(self, query_params=""):
        """Supabaseから実データを取得"""
        try:
            supabase_url, supabase_key = self.get_supabase_config()
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            url = f"{supabase_url}/rest/v1/density_history?{query_params}"
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            return data
            
        except Exception as e:
            raise Exception(f"Failed to fetch Supabase data: {str(e)}")
    
    def create_features(self, day_of_week, avg_density_seats_ratio):
        """特徴量を作成（モデル訓練時と同じ10個の特徴量）"""
        # 基本的な特徴量を作成（10個）
        features = np.zeros((1, 10))
        
        # 1. day_of_week
        features[0, 0] = day_of_week
        
        # 2. density_seats_ratio（実際のデータから計算またはデフォルト値）
        features[0, 1] = avg_density_seats_ratio
        
        # 3-7. 曜日ダミー変数
        features[0, 2] = 1 if day_of_week == 0 else 0  # is_monday
        features[0, 3] = 1 if day_of_week == 1 else 0  # is_tuesday
        features[0, 4] = 1 if day_of_week == 2 else 0  # is_wednesday
        features[0, 5] = 1 if day_of_week == 3 else 0  # is_thursday
        features[0, 6] = 1 if day_of_week == 4 else 0  # is_friday
        
        # 8. is_early_week（月火）
        features[0, 7] = 1 if day_of_week in [0, 1] else 0
        
        # 9. is_mid_week（水）
        features[0, 8] = 1 if day_of_week == 2 else 0
        
        # 10. is_late_week（木金）
        features[0, 9] = 1 if day_of_week in [3, 4] else 0
        
        return features
    
    def get_density_seats_ratio(self, day_of_week):
        """Supabaseから実際のdensity_seats_ratioを取得"""
        try:
            # 指定された曜日のデータを取得
            data = self.get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                # 指定曜日にデータがない場合、全曜日の平均を使用
                all_data = self.get_supabase_data("select=density_rate,occupied_seats")
                if not all_data:
                    raise Exception("No data available in database")
                data = all_data
            
            # 実際のdensity_seats_ratioを計算
            ratios = []
            for record in data:
                density_rate = record.get('density_rate', 0)
                occupied_seats = record.get('occupied_seats', 0)
                if occupied_seats > 0:
                    ratio = (density_rate / 100.0) / (occupied_seats + 1)
                    ratios.append(ratio)
            
            if not ratios:
                raise Exception("No valid ratio data found")
                
            return sum(ratios) / len(ratios)
            
        except Exception as e:
            # 最終フォールバック: 統計的に妥当なデフォルト値
            return 0.15  # 15%の密度比率（平均的な値）
    
    def predict_with_models(self, day_of_week):
        """訓練済みモデルで予測"""
        try:
            models = self.load_trained_models()
            
            # 実際のdensity_seats_ratioを取得
            avg_density_seats_ratio = self.get_density_seats_ratio(day_of_week)
            
            # 特徴量を作成（10個の特徴量）
            features = self.create_features(day_of_week, avg_density_seats_ratio)
            
            # 予測実行
            density_pred = models['density_model'].predict(features)[0]
            seats_pred = models['seats_model'].predict(features)[0]
            
            # 正規化
            occupancy_rate = density_pred / 100.0 if density_pred > 1 else density_pred
            occupancy_rate = min(1.0, max(0.0, occupancy_rate))
            occupied_seats = min(8, max(0, round(seats_pred)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
                "model_prediction": True
            }
            
        except Exception as e:
            # モデル予測に失敗した場合はSupabaseデータの平均を使用
            try:
                return self.get_database_average(day_of_week)
            except Exception as fallback_error:
                # 最終フォールバック: 安全なデフォルト値
                return {
                    "occupancy_rate": 0.3,  # 30%の占有率（平日の平均的な値）
                    "occupied_seats": 2,     # 2席占有（平均的な値）
                    "model_prediction": False
                }
    
    def get_database_average(self, day_of_week):
        """Supabaseデータから平均を計算（フォールバック）"""
        try:
            # 指定された曜日のデータを取得
            data = self.get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                # 指定曜日にデータがない場合、全曜日の平均を使用
                all_data = self.get_supabase_data("select=density_rate,occupied_seats")
                if not all_data:
                    raise Exception("No data available in database")
                data = all_data
            
            # 平均を計算
            total_density = sum(record.get('density_rate', 0) for record in data)
            total_seats = sum(record.get('occupied_seats', 0) for record in data)
            count = len(data)
            
            if count == 0:
                raise Exception("No valid data records found")
            
            avg_density_rate = total_density / count
            avg_occupied_seats = total_seats / count
            
            # 正規化
            occupancy_rate = avg_density_rate / 100.0 if avg_density_rate > 1 else avg_density_rate
            occupancy_rate = min(1.0, max(0.0, occupancy_rate))
            occupied_seats = min(8, max(0, round(avg_occupied_seats)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
                "model_prediction": False
            }
            
        except Exception as e:
            # 最終フォールバック: 統計的に妥当なデフォルト値
            return {
                "occupancy_rate": 0.3,  # 30%の占有率
                "occupied_seats": 2,     # 2席占有
                "model_prediction": False
            }
    
    def handle_today_tomorrow(self):
        """今日・明日予測API"""
        try:
            # 現在の日時を取得
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            today_weekday = today.weekday()
            tomorrow_weekday = tomorrow.weekday()
            
            # 曜日名を取得するヘルパー関数
            def get_weekday_name(weekday):
                weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
                return weekday_names[weekday]
            
            # 今日の予測
            if today_weekday >= 5:  # 土日
                today_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0, "model_prediction": False}
            else:
                today_prediction = self.predict_with_models(today_weekday)
            
            # 明日の予測
            if tomorrow_weekday >= 5:  # 土日
                tomorrow_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0, "model_prediction": False}
            else:
                tomorrow_prediction = self.predict_with_models(tomorrow_weekday)
            
            # レスポンスデータの構築
            response_data = {
                "success": True,
                "data": {
                    "today": {
                        "weekday": today_weekday,
                        "weekday_name": get_weekday_name(today_weekday),
                        "occupancy_rate": today_prediction["occupancy_rate"],
                        "occupied_seats": today_prediction["occupied_seats"],
                        "model_prediction": today_prediction["model_prediction"]
                    },
                    "tomorrow": {
                        "weekday": tomorrow_weekday,
                        "weekday_name": get_weekday_name(tomorrow_weekday),
                        "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                        "occupied_seats": tomorrow_prediction["occupied_seats"],
                        "model_prediction": tomorrow_prediction["model_prediction"]
                    }
                },
                "prediction_method": "trained_model_with_supabase_fallback",
                "environment": "production"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error_response("Internal server error")
    
    def handle_weekly_average(self):
        """週間平均予測API"""
        try:
            # 曜日名の定義
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            
            weekly_averages = []
            
            # 各平日の予測を計算
            for day_of_week in range(5):  # 平日のみ（0-4）
                prediction = self.predict_with_models(day_of_week)
                
                weekly_averages.append({
                    "weekday": day_of_week,
                    "weekday_name": weekday_names[day_of_week],
                    "occupancy_rate": prediction["occupancy_rate"],
                    "occupied_seats": prediction["occupied_seats"],
                    "model_prediction": prediction["model_prediction"]
                })
            
            # レスポンスデータの構築
            response_data = {
                "success": True,
                "data": {
                    "weekly_averages": weekly_averages
                },
                "prediction_method": "trained_model_with_supabase_fallback",
                "environment": "production"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error_response("Internal server error")
    
    def handle_model_info(self):
        """モデル情報API"""
        try:
            models = self.load_trained_models()
            
            response_data = {
                "success": True,
                "data": {
                    "model_parameters": models['best_params'],
                    "model_performance": models['performance'],
                    "model_files": {
                        "density_model": "api/density_model.joblib",
                        "seats_model": "api/seats_model.joblib",
                        "best_params": "api/best_params.joblib",
                        "performance": "api/model_performance.joblib"
                    }
                },
                "environment": "production"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error_response("Internal server error")
    
    def send_json_response(self, data, status_code=200):
        """JSON レスポンスを送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, error_message, status_code=500):
        """エラーレスポンスを送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            "success": False,
            "error": error_message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8')) 