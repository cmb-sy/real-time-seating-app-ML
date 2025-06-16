"""
予測機能のみを分離
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 現在のファイルのディレクトリを取得してパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # 同じ階層を最優先に

# utilsディレクトリもパスに追加
utils_dir = os.path.join(current_dir, 'utils')
if os.path.exists(utils_dir):
    sys.path.insert(0, utils_dir)

# 共通のSupabaseアクセスモジュールをインポート
from supabase_access import get_supabase_data

try:
    import joblib
    import pandas as pd
    from data_processor import engineer_features, get_feature_columns
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML libraries not available: {e}")
    joblib = None
    pd = None
    engineer_features = None
    get_feature_columns = None
    ML_AVAILABLE = False

class PredictionService:
    def __init__(self):
        self.models = self._load_trained_models()
    
    def _load_trained_models(self):
        try:
            model_files = {
                'density_model': 'api/density_model.joblib',
                'seats_model': 'api/seats_model.joblib',
                'best_params': 'api/best_params.joblib',
                'performance': 'api/model_performance.joblib'
            }
            models = {}
            for name, path in model_files.items():
                try:
                    models[name] = joblib.load(path)
                except Exception as e:
                    print(f"Model loading failed for {name}: {str(e)}")
                    models[name] = None
            return models
        except Exception as e:
            print(f"Model loading failed: {str(e)}")
            return {
                'density_model': None,
                'seats_model': None,
                'best_params': None,
                'performance': None
            }
    
    def create_features(self, day_of_week, avg_density_seats_ratio):
        """特徴量を作成"""
        try:
            data = {
                'day_of_week': [day_of_week],
                'density_rate': [avg_density_seats_ratio * 100],
                'occupied_seats': [8 * avg_density_seats_ratio]
            }
            df = pd.DataFrame(data)
            
            feature_df = engineer_features(df)
            feature_columns = get_feature_columns()
            available_features = [col for col in feature_columns if col in feature_df.columns]
            X = feature_df[available_features].values
            return X
            
        except Exception as e:
            print(f"特徴量作成エラー: {str(e)}")
            return None
    
    def get_density_seats_ratio(self, day_of_week):
        """density_seats_ratioを取得"""
        try:
            # Supabaseからデータを取得（共通関数を使用）
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            ratios = []
            for record in data:
                density_rate = record.get('density_rate', 0)
                occupied_seats = record.get('occupied_seats', 0)
                if occupied_seats > 0:
                    ratio = (density_rate / 100.0) / (occupied_seats + 1)
                    ratios.append(ratio)
            
            if not ratios:
                raise Exception("No valid ratio data found")
            
            avg_ratio = sum(ratios) / len(ratios)
            print(f"Calculated density_seats_ratio for day {day_of_week}: {avg_ratio:.4f}")
            return avg_ratio
            
        except Exception as e:
            print(f"Error calculating density_seats_ratio: {e}")
            # フォールバック値
            fallback = 0.1 + (day_of_week * 0.02)
            print(f"Using fallback ratio: {fallback}")
            return fallback
    
    def predict_with_models(self, day_of_week):
        """訓練済みモデルで予測"""
        try:
            print(f"day_of_weekの確認: {day_of_week}")
            
            if self.models['density_model'] is None or self.models['seats_model'] is None:
                print("モデルが利用できないため、モックデータを使用")
                return self.get_database_average(day_of_week)
            
            avg_density_seats_ratio = self.get_density_seats_ratio(day_of_week)
            features = self.create_features(day_of_week, avg_density_seats_ratio)
            
            if features is None:
                print("featuresがNoneのため、モックデータを使用")
                return self.get_database_average(day_of_week)
            try:
                density_pred = self.models['density_model'].predict(features)[0]
                seats_pred = self.models['seats_model'].predict(features)[0]
            except Exception as model_error:
                print(f"モデル予測エラー: {str(model_error)}")
                return self.get_database_average(day_of_week)
            
            occupancy_rate = max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred))
            occupied_seats = max(0, min(8, round(seats_pred)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
                "model_used": True
            }
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return self.get_database_average(day_of_week)
    
    def get_database_average(self, day_of_week):
        """平均値を計算"""
        try:
            print(f"Calculating database average for day {day_of_week}")
            # 共通関数を使用してデータを取得
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                raise Exception("No data found")
            
            total_density = sum(record.get('density_rate', 0) for record in data)
            total_seats = sum(record.get('occupied_seats', 0) for record in data)
            count = len(data)
            
            avg_density_rate = total_density / count
            avg_occupied_seats = total_seats / count
            
            occupancy_rate = avg_density_rate / 100.0 if avg_density_rate > 1 else avg_density_rate
            occupancy_rate = min(1.0, max(0.0, occupancy_rate))
            occupied_seats = min(8, max(0, round(avg_occupied_seats)))
            
            return {
                "occupancy_rate": round(occupancy_rate, 2),
                "occupied_seats": occupied_seats,
                "model_used": False
            }
            
        except Exception as e:
            print(f"Database average calculation error: {e}")
            # フォールバック値
            return {
                "occupancy_rate": 0.5,
                "occupied_seats": 4,
                "model_used": False
            }

    def predict_today_tomorrow(self):
        """今日・明日の予測"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        today_weekday = today.weekday()
        tomorrow_weekday = tomorrow.weekday()
        
        def get_weekday_name(weekday):
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            return weekday_names[weekday]
        
        print(f"Predicting for today ({today_weekday}) and tomorrow ({tomorrow_weekday})")
        
        # 土日の場合は空席
        if today_weekday >= 5:
            today_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
        else:
            today_prediction = self.predict_with_models(today_weekday)
        
        if tomorrow_weekday >= 5:
            tomorrow_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
        else:
            tomorrow_prediction = self.predict_with_models(tomorrow_weekday)
        
        return {
            "today": {
                "weekday": today_weekday,
                "weekday_name": get_weekday_name(today_weekday),
                **today_prediction
            },
            "tomorrow": {
                "weekday": tomorrow_weekday,
                "weekday_name": get_weekday_name(tomorrow_weekday),
                **tomorrow_prediction
            }
        }
    
    def predict_weekly_average(self):
        """週間平均予測"""
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        weekly_averages = []
        
        for day_of_week in range(5):  # 平日のみ
            prediction = self.get_database_average(day_of_week)
            
            weekly_averages.append({
                "weekday": day_of_week,
                "weekday_name": weekday_names[day_of_week],
                **prediction
            })
        return {"weekly_averages": weekly_averages}

if __name__ == "__main__":
    print("=== 予測機能テスト ===")
    
    service = PredictionService()
    
    print("\n1. 今日・明日予測テスト")
    today_tomorrow = service.predict_today_tomorrow()
    print(f"今日: {today_tomorrow['today']}")
    print(f"明日: {today_tomorrow['tomorrow']}")
    
    print("\n2. 週間平均予測テスト")
    weekly = service.predict_weekly_average()
    for day_data in weekly['weekly_averages']:
        print(f"{day_data['weekday_name']}: 占有率{day_data['occupancy_rate']}, 席数{day_data['occupied_seats']}")
    
    print("\n3. モデル状態確認")
    print(f"Density Model: {'利用可能' if service.models['density_model'] is not None else '利用不可'}")
    print(f"Seats Model: {'利用可能' if service.models['seats_model'] is not None else '利用不可'}")
    print(f"Best Params: {service.models['best_params']}")
    
    print("\nテスト完了！")