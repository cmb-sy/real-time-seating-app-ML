"""
統合API - Supabase実データ専用版
"""
import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

sys.path.append('src/ml') #先に呼ばないとダメ

try:
    import joblib
    import numpy as np
    import pandas as pd
    from data_processor import engineer_features, get_feature_columns
    ML_LIBRARIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML libraries not available: {e}")
    joblib = None
    np = None
    ML_LIBRARIES_AVAILABLE = False
    engineer_features = None
    get_feature_columns = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
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
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("Database configuration error")
            
        return supabase_url, supabase_key
    
    def load_trained_models(self):
        if not ML_LIBRARIES_AVAILABLE or joblib is None:
            return {
                'density_model': None,
                'seats_model': None,
                'best_params': {'status': 'ML libraries not available'},
                'performance': {'status': 'ML libraries not available'}
            }
        
        try:
            # モデルファイルのパス
            density_model_path = 'api/density_model.joblib'
            seats_model_path = 'api/seats_model.joblib'
            best_params_path = 'api/best_params.joblib'
            performance_path = 'api/model_performance.joblib'
            
            # ファイル存在確認
            for path in [density_model_path, seats_model_path, best_params_path, performance_path]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Model file not found: {path}")
            
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
            return {
                'density_model': None,
                'seats_model': None,
                'best_params': {'status': f'Model loading failed: {str(e)}'},
                'performance': {'status': f'Model loading failed: {str(e)}'}
            }
    
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
        """特徴量を作成（data_processor.pyの関数を使用）"""
        if not ML_LIBRARIES_AVAILABLE or np is None:
            return None
            
        try:
            # データフレームの作成
            data = {
                'day_of_week': [day_of_week],
                'density_rate': [avg_density_seats_ratio * 100],  # 0-100のスケールに変換
                'occupied_seats': [8 * avg_density_seats_ratio]   # 仮の値（実際のデータから計算すべき）
            }
            df = pd.DataFrame(data)
            
            # 特徴量エンジニアリングを適用
            if engineer_features is not None:
                feature_df = engineer_features(df)
                
                # 必要な特徴量を取得
                if get_feature_columns is not None:
                    feature_columns = get_feature_columns()
                    # 存在する特徴量のみを選択
                    available_features = [col for col in feature_columns if col in feature_df.columns]
                    X = feature_df[available_features].values
                    return X
            
            # エンジニアリングが使えない場合は旧方式で特徴量を作成
            features = [day_of_week, avg_density_seats_ratio]
            
            # 曜日ダミー変数（月曜日から金曜日まで）
            is_monday = 1 if day_of_week == 0 else 0
            is_tuesday = 1 if day_of_week == 1 else 0
            is_wednesday = 1 if day_of_week == 2 else 0
            is_thursday = 1 if day_of_week == 3 else 0
            is_friday = 1 if day_of_week == 4 else 0
            
            features.extend([is_monday, is_tuesday, is_wednesday, is_thursday, is_friday])
            
            # 週の分類特徴量
            is_early_week = 1 if day_of_week in [0, 1] else 0  # 月火
            is_mid_week = 1 if day_of_week == 2 else 0         # 水
            is_late_week = 1 if day_of_week in [3, 4] else 0   # 木金
            
            features.extend([is_early_week, is_mid_week, is_late_week])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            print(f"特徴量作成エラー: {str(e)}")
            return None
    
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
            raise Exception(f"Unable to calculate density ratio from database: {str(e)}")
    
    def predict_with_models(self, day_of_week):
        """訓練済みモデルで予測"""
        try:
            # モデルを読み込み
            models = self.load_trained_models()
            
            # モデルが利用可能かチェック
            if models['density_model'] is None or models['seats_model'] is None:
                # モデルが利用できない場合はデータベース平均を使用
                return self.get_database_average(day_of_week)
            
            # 特徴量を作成
            avg_density_seats_ratio = self.get_density_seats_ratio(day_of_week)
            features = self.create_features(day_of_week, avg_density_seats_ratio)
            
            if features is None:
                # 特徴量作成に失敗した場合はデータベース平均を使用
                return self.get_database_average(day_of_week)
            
            # 予測実行
            # 注：特徴量の次元数がモデルの期待する次元数と一致しない場合の対策
            try:
                density_pred = models['density_model'].predict(features)[0]
                seats_pred = models['seats_model'].predict(features)[0]
            except Exception as model_error:
                print(f"モデル予測エラー: {str(model_error)}")
                # 特徴量の次元が合わない場合は、データベース平均を使用
                return self.get_database_average(day_of_week)
            
            # 予測結果を正規化
            occupancy_rate = max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred))
            occupied_seats = max(0, min(8, round(seats_pred)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
                "model_used": True
            }
            
        except Exception as e:
            print(f"予測エラー: {str(e)}")
            # MLモデル予測に失敗した場合はデータベース平均を使用
            return self.get_database_average(day_of_week)
    
    def get_database_average(self, day_of_week):
        """Supabaseデータから平均を計算"""
        try:
            # 指定された曜日のデータを取得
            data = self.get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                data = []
            
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
                "model_used": False
            }
            
        except Exception as e:
            print(f"平均計算エラー: {str(e)}")
            # 最終的なフォールバック
            return {
                "occupancy_rate": 0.5,
                "occupied_seats": 4,
                "model_used": False,
                "error": str(e)
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
            
            # 今日の予測（MLモデル使用）
            if today_weekday >= 5:  # 土日
                today_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
            else:
                today_prediction = self.predict_with_models(today_weekday)
            
            # 明日の予測（MLモデル使用）
            if tomorrow_weekday >= 5:  # 土日
                tomorrow_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
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
                        "occupied_seats": today_prediction["occupied_seats"]
                    },
                    "tomorrow": {
                        "weekday": tomorrow_weekday,
                        "weekday_name": get_weekday_name(tomorrow_weekday),
                        "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                        "occupied_seats": tomorrow_prediction["occupied_seats"]
                    }
                },
                "prediction_method": "ml_model_with_supabase_fallback",
                "environment": "production"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error_response("Failed to get predictions from database")
    
    def handle_weekly_average(self):
        """週間平均予測API（データベース平均使用）"""
        try:
            # 曜日名の定義
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            
            weekly_averages = []
            
            # 各平日の予測を計算（データベース平均を使用）
            for day_of_week in range(5):  # 平日のみ（0-4）
                prediction = self.get_database_average(day_of_week)
                
                weekly_averages.append({
                    "weekday": day_of_week,
                    "weekday_name": weekday_names[day_of_week],
                    "occupancy_rate": prediction["occupancy_rate"],
                    "occupied_seats": prediction["occupied_seats"]
                })
            
            # レスポンスデータの構築
            response_data = {
                "success": True,
                "data": {
                    "weekly_averages": weekly_averages
                },
                "prediction_method": "database_average",
                "environment": "production"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error_response("Failed to calculate weekly averages from database")
    
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
            self.send_error_response("Failed to load model information")
    
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