"""
予測機能のみを分離
"""
import sys
import os
import json
from datetime import datetime, timedelta

# 明示的なパス設定（デプロイ環境での確実な動作のため）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # utilsの親ディレクトリ
utils_dir = os.path.join(project_root, 'utils')

# 必要なディレクトリをパスに追加
for path in [utils_dir, current_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from supabase_access import get_supabase_data

try:
    import joblib
    import pandas as pd
    from data_processor import engineer_features, get_feature_columns
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

class PredictionService:
    def __init__(self):
        # 初期化時にモデルを読み込む
        self.models = self._load_trained_models()
        # JSONファイルの保存先
        self.today_tomorrow_file = os.path.join(project_root, 'api/today_tomorrow_predictions.json')
        self.weekly_averages_file = os.path.join(project_root, 'api/weekly_averages_predictions.json')
    
    def _load_trained_models(self):
        """訓練済みモデルを読み込む"""
        try:
            # 現在のファイルの場所から相対的にパスを構築
            current_dir = os.path.dirname(os.path.abspath(__file__))            
            model_files = {
                'density_model': os.path.join(current_dir, 'joblib/density_model.joblib'),
                'seats_model': os.path.join(current_dir, 'joblib/seats_model.joblib'),
                'best_params': os.path.join(current_dir, 'joblib/best_params.joblib'),
                'performance': os.path.join(current_dir, 'joblib/model_performance.joblib')
            }
        
            models = {}
            for name, path in model_files.items():
                try:
                    if os.path.exists(path):
                        models[name] = joblib.load(path)
                    else:
                        models[name] = None
                except Exception:
                    models[name] = None
            
            return models
            
        except Exception:
            return {
                'density_model': None,
                'seats_model': None,
                'best_params': None,
                'performance': None
            }

    def create_features(self, day_of_week, avg_density_seats_ratio):
        """特徴量を作成"""
        try:
            if not DEPENDENCIES_AVAILABLE:
                return None
                
            data = {
                'day_of_week': [day_of_week],
                'density_rate': [avg_density_seats_ratio * 100],
                'occupied_seats': [8 * avg_density_seats_ratio]
            }
            df = pd.DataFrame(data)
            
            feature_df = engineer_features(df)
            feature_columns = get_feature_columns()
            available_features = [col for col in feature_columns if col in feature_df.columns]
            
            if not available_features:
                return None
                
            X = feature_df[available_features].values
            return X
            
        except Exception:
            return None
    
    def get_density_seats_ratio(self, day_of_week):
        """density_seats_ratioを取得"""
        try:
            # Supabaseからデータを取得
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            ratios = []
            for record in data:
                density_rate = record.get('density_rate', 0)
                occupied_seats = record.get('occupied_seats', 0)
                if occupied_seats > 0:
                    ratio = (density_rate / 100.0) / (occupied_seats + 1)
                    ratios.append(ratio)
            
            if not ratios:
                return 0.5  # デフォルト値
            
            avg_ratio = sum(ratios) / len(ratios)
            return avg_ratio
            
        except Exception:
            return 0.5
    
    def predict_with_models(self, day_of_week):
        """訓練済みモデルで予測"""
        try:
            # モデルの存在確認
            if (not self.models or 
                self.models.get('density_model') is None or 
                self.models.get('seats_model') is None):
                return self.get_database_average(day_of_week)
            
            # 特徴量取得
            avg_density_seats_ratio = self.get_density_seats_ratio(day_of_week)
            features = self.create_features(day_of_week, avg_density_seats_ratio)
            
            if features is None:
                return self.get_database_average(day_of_week)
            
            # モデル予測実行
            try:
                density_pred = self.models['density_model'].predict(features)[0]
                seats_pred = self.models['seats_model'].predict(features)[0]
                
                # 予測結果の正規化
                occupancy_rate = max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred))
                occupied_seats = max(0, min(8, round(seats_pred)))
                
                return {
                    "occupancy_rate": round(occupancy_rate, 2),
                    "occupied_seats": occupied_seats,
                }
                
            except Exception:
                return self.get_database_average(day_of_week)
            
        except Exception:
            return self.get_database_average(day_of_week)
    
    def get_database_average(self, day_of_week):
        """データベースから平均値を計算"""
        try:
            # データを取得
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                return {
                    "occupancy_rate": 0.5,
                    "occupied_seats": 4,
                }
            
            total_density = sum(record.get('density_rate', 0) for record in data)
            total_seats = sum(record.get('occupied_seats', 0) for record in data)
            count = len(data)
            
            avg_density_rate = total_density / count
            avg_occupied_seats = total_seats / count
            
            # 正規化
            occupancy_rate = avg_density_rate / 100.0 if avg_density_rate > 1 else avg_density_rate
            occupancy_rate = min(1.0, max(0.0, occupancy_rate))
            occupied_seats = min(8, max(0, round(avg_occupied_seats)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
            }
            
        except Exception:
            return {
                "occupancy_rate": 0.5,
                "occupied_seats": 4,
            }

    def predict_today_tomorrow(self):
        """今日・明日の予測"""
        try:
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            today_weekday = today.weekday()
            tomorrow_weekday = tomorrow.weekday()
            
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            
            # 土日の場合は空席
            if today_weekday >= 5:
                today_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
            else:
                today_prediction = self.predict_with_models(today_weekday)
            
            if tomorrow_weekday >= 5:
                tomorrow_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
            else:
                tomorrow_prediction = self.predict_with_models(tomorrow_weekday)
            
            result = {
                "today": {
                    "weekday": today_weekday,
                    "weekday_name": weekday_names[today_weekday],
                    **today_prediction
                },
                "tomorrow": {
                    "weekday": tomorrow_weekday,
                    "weekday_name": weekday_names[tomorrow_weekday],
                    **tomorrow_prediction
                }
            }
            
            return result
            
        except Exception as e:
            raise e
    
    def predict_weekly_average(self):
        """週間平均予測"""
        try:
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            weekly_averages = []
            
            for day_of_week in range(5):  # 平日のみ
                try:
                    prediction = self.get_database_average(day_of_week)
                    weekly_averages.append({
                        "weekday": day_of_week,
                        "weekday_name": weekday_names[day_of_week],
                        **prediction
                    })
                except Exception:
                    # 個別の曜日でエラーが発生してもスキップ
                    weekly_averages.append({
                        "weekday": day_of_week,
                        "weekday_name": weekday_names[day_of_week],
                        "occupancy_rate": 0.5,
                        "occupied_seats": 4
                    })
            
            return {"weekly_averages": weekly_averages}
            
        except Exception as e:
            raise e

    def save_predictions_to_json(self):
        """予測結果をJSONファイルに保存する"""
        try:
            # 今日・明日の予測を取得してJSONに保存
            today_tomorrow_data = self.predict_today_tomorrow()
            with open(self.today_tomorrow_file, 'w', encoding='utf-8') as f:
                json.dump(today_tomorrow_data, f, ensure_ascii=False, indent=2)
            
            # 週間平均予測を取得してJSONに保存
            weekly_averages_data = self.predict_weekly_average()
            with open(self.weekly_averages_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_averages_data, f, ensure_ascii=False, indent=2)
            
            # 保存した時間を記録
            timestamp_file = os.path.join(project_root, 'api/last_update.json')
            timestamp_data = {
                "last_update": datetime.now().isoformat(),
                "today_tomorrow_file": "today_tomorrow_predictions.json",
                "weekly_averages_file": "weekly_averages_predictions.json"
            }
            with open(timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "files": {
                    "today_tomorrow": self.today_tomorrow_file,
                    "weekly_averages": self.weekly_averages_file,
                    "last_update": timestamp_file
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    try:
        service = PredictionService()
        result = service.save_predictions_to_json()
        
        if result["success"]:
            print("✅ 予測データが正常に保存されました")
            for name, file_path in result["files"].items():
                print(f"- {name}: {file_path}")
        else:
            print(f"❌ 予測データの保存に失敗しました: {result['error']}")
            
    except Exception as e:
        print(f"実行エラー: {str(e)}")