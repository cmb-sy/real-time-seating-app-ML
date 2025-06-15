"""
APIルーター - ポート8000で両方のAPIエンドポイントを提供
直接処理方式で高速化
"""
import sys
import joblib
import numpy as np
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.utils.database import get_supabase_client
from src.utils.response_helper import (
    send_success_response, 
    send_error_response, 
    send_options_response,
    send_head_response,
    run_server,
    parse_port_arg
)

class APIRouter(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        send_options_response(self)
    
    def do_HEAD(self):
        """HEADリクエストへの対応"""
        send_head_response(self)
    
    def do_GET(self):
        """リクエストパスに応じてAPIを振り分け"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == "/api/predictions/today-tomorrow":
                self.handle_today_tomorrow_direct()
            elif path == "/api/predictions/weekly-average":
                self.handle_weekly_average_direct()
            elif path == "/":
                self.handle_root()
            else:
                send_error_response(self, f"エンドポイントが見つかりません: {path}")
                
        except Exception as e:
            send_error_response(self, f"リクエスト処理中にエラーが発生しました: {str(e)}")
    
    def handle_today_tomorrow_direct(self):
        """今日・明日予測API処理"""
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
            
            # 平日がある場合のみモデルをロード
            model_data = None
            if today_weekday < 5 or tomorrow_weekday < 5:
                model_data = self.load_ml_models()
                if not model_data:
                    send_error_response(self, "ML予測モデルをロードできませんでした。")
                    return
            
            # 今日の予測
            if today_weekday >= 5:
                today_prediction = {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0
                }
            else:
                today_prediction = self.generate_prediction_with_ml(model_data, today_weekday)
            
            # 明日の予測
            if tomorrow_weekday >= 5:
                tomorrow_prediction = {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0
                }
            else:
                tomorrow_prediction = self.generate_prediction_with_ml(model_data, tomorrow_weekday)
            
            # フロントエンドの型定義に合わせたレスポンス形式
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
                }
            }
            
            send_success_response(self, response_data)
            
        except Exception as e:
            send_error_response(self, f"今日・明日予測APIでエラーが発生しました: {str(e)}")
    
    def handle_weekly_average_direct(self):
        """週間平均予測APIの直接処理"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                raise Exception("Supabaseクライアントの初期化に失敗しました")
                
            # density_historyテーブルから過去のデータを取得
            response = supabase.table('density_history').select('*').execute()
            data = response.data
            
            if not data or len(data) == 0:
                raise Exception("データベースにデータが存在しません")
                
            # 曜日別に集計（0-4: 月-金のみ、土日は除外）
            day_of_week_data = {i: [] for i in range(5)}  # 平日のみ（0-4）
            
            for record in data:
                day_of_week = record.get('day_of_week')
                density_rate = record.get('density_rate', 0)
                occupied_seats = record.get('occupied_seats', 0)
                
                # 土日（5, 6）のデータは除外し、平日（0-4）のみ処理
                if day_of_week is not None and 0 <= day_of_week <= 4:
                    occupancy_rate = density_rate / 100.0 if density_rate > 1 else density_rate
                    day_of_week_data[day_of_week].append({
                        'occupancy_rate': occupancy_rate,
                        'occupied_seats': occupied_seats
                    })
            
            # 曜日名の定義
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            
            weekly_averages = {
                "success": True,
                "data": {
                    "weekly_averages": []
                }
            }
            
            # 平日（0-4）のみ処理
            for day in range(5):  # 0-4の平日のみ
                values = day_of_week_data[day]
                if values:
                    avg_occupancy = sum(v['occupancy_rate'] for v in values) / len(values)
                    avg_occupied_seats = sum(v['occupied_seats'] for v in values) / len(values)
                    
                    final_occupied_seats = min(8, max(0, round(avg_occupied_seats)))
                    final_occupancy_rate = min(1.0, max(0.0, avg_occupancy))
                    
                    weekly_averages["data"]["weekly_averages"].append({
                        "weekday": day,
                        "weekday_name": weekday_names[day],
                        "occupancy_rate": round(final_occupancy_rate, 2),
                        "occupied_seats": final_occupied_seats,
                    })
                else:
                    weekly_averages["data"]["weekly_averages"].append({
                        "weekday": day,
                        "weekday_name": weekday_names[day],
                        "occupancy_rate": 0.0,
                        "occupied_seats": 0,
                    })
            
            send_success_response(self, weekly_averages)
            
        except Exception as e:
            send_error_response(self, f"週間平均予測APIでエラーが発生しました: {str(e)}")
    
    def load_ml_models(self):
        """機械学習モデルをロード"""
        try:
            current_dir = Path(__file__).resolve().parent
            
            density_model_path = current_dir / "density_model.joblib"
            seats_model_path = current_dir / "seats_model.joblib"
            best_params_path = current_dir / "best_params.joblib"
            model_performance_path = current_dir / "model_performance.joblib"
            
            if not all([
                density_model_path.exists(),
                seats_model_path.exists(),
                best_params_path.exists(),
                model_performance_path.exists()
            ]):
                return None
            
            density_model = joblib.load(density_model_path)
            seats_model = joblib.load(seats_model_path)
            best_params = joblib.load(best_params_path)
            model_performance = joblib.load(model_performance_path)
            
            return {
                "density_model": density_model,
                "seats_model": seats_model,
                "best_params": best_params,
                "model_performance": model_performance,
                "version": "1.0.0"
            }
        except Exception as e:
            print(f"モデルロードエラー: {str(e)}")
            return None
    
    def generate_prediction_with_ml(self, model_data, day_of_week):
        """曜日別の予測を生成（簡素化された特徴量エンジニアリング対応）"""
        if day_of_week < 0 or day_of_week > 6:
            raise Exception(f"サポートされていない曜日です: {day_of_week}")
        
        if day_of_week >= 5:
            raise Exception(f"土日（曜日: {day_of_week}）は予測データがありません")
        
        # データベースから実際のdensity_seats_ratioの平均値を取得
        try:
            supabase = get_supabase_client()
            if supabase:
                response = supabase.table('density_history').select('density_rate, occupied_seats').eq('day_of_week', day_of_week).execute()
                data = response.data
                
                if data and len(data) > 0:
                    # 実際のdensity_seats_ratioを計算
                    ratios = []
                    for record in data:
                        density_rate = record.get('density_rate', 0)
                        occupied_seats = record.get('occupied_seats', 0)
                        if occupied_seats > 0:
                            ratio = (density_rate / 100.0) / (occupied_seats + 1)
                            ratios.append(ratio)
                    
                    avg_density_seats_ratio = sum(ratios) / len(ratios) if ratios else 0.1
                else:
                    avg_density_seats_ratio = 0.1  # データがない場合のみフォールバック
            else:
                avg_density_seats_ratio = 0.1  # DB接続失敗時のフォールバック
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            avg_density_seats_ratio = 0.1  # エラー時のフォールバック
        
        # 簡素化された特徴量を手動で作成（10個の特徴量）
        try:
            # 基本的な特徴量を作成
            features = np.zeros((1, 10))  # 10個の特徴量
            
            # 1. day_of_week
            features[0, 0] = day_of_week
            
            # 2. density_seats_ratio（実際のデータから計算）
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
            
        except Exception as e:
            print(f"特徴量作成でエラー: {e}")
            # フォールバック: 10個の特徴量でデフォルト値を使用
            features = np.zeros((1, 10))
            features[0, 0] = day_of_week  # 最低限day_of_weekは設定
            features[0, 1] = avg_density_seats_ratio
        
        density_model = model_data.get("density_model")
        seats_model = model_data.get("seats_model")
            
        if density_model and seats_model:
            try:
                density_pred = density_model.predict(features)[0]
                seats_pred = seats_model.predict(features)[0]
                
                density_pred = max(0, min(100, density_pred))
                seats_pred = max(0, min(int(seats_pred), 8))
                
                base_prediction = {
                    "density_rate": round(density_pred, 2),
                    "occupied_seats": int(seats_pred)
                }
            except Exception as e:
                print(f"予測エラー: {e}")
                raise Exception(f"予測処理でエラーが発生しました: {str(e)}")
        else:
            raise Exception("予測モデルがエラーを返しました")
        
        density_rate = base_prediction["density_rate"]
        occupancy_rate = density_rate / 100.0
        actual_occupied_seats = min(8, max(0, round(occupancy_rate * 8)))
        
        return {
            "occupancy_rate": round(occupancy_rate, 2),
            "occupied_seats": actual_occupied_seats
        }
    
    def handle_root(self):
        """ルートパスでのAPI情報表示"""
        api_info = {
            "success": True,
            "message": "リアルタイム座席予測API",
            "version": "1.0.0",
            "endpoints": {
                "today_tomorrow": "/api/predictions/today-tomorrow",
                "weekly_average": "/api/predictions/weekly-average"
            },
            "status": "運用中"
        }
        send_success_response(self, api_info)

if __name__ == "__main__":
    # lsof -ti:8000 | xargs kill -9 で停止
    # curl http://localhost:8000/api/predictions/today-tomorrow
    # curl http://localhost:8000/api/predictions/weekly-average
    port = parse_port_arg(description='APIルーターサーバーを起動します', default_port=8000)
    run_server(APIRouter, port, server_name="APIルーター") 