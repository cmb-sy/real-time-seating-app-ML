"""
予測機能のみを分離
"""
import sys
import os
import traceback
from datetime import datetime, timedelta

# 明示的なパス設定（デプロイ環境での確実な動作のため）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # utilsの親ディレクトリ
utils_dir = os.path.join(project_root, 'utils')

# 必要なディレクトリをパスに追加
for path in [utils_dir, current_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

print(f"📁 現在のディレクトリ: {current_dir}")
print(f"📁 プロジェクトルート: {project_root}")
print(f"📁 utilsディレクトリ: {utils_dir}")

from supabase_access import get_supabase_data

try:
    import joblib
    import pandas as pd
    from data_processor import engineer_features, get_feature_columns
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    DEPENDENCIES_AVAILABLE = False

class PredictionService:
    def __init__(self):
        # 初期化時にモデルを読み込む
        self.models = self._load_trained_models()
    
    def _load_trained_models(self):
        """訓練済みモデルを読み込む"""
        try:
            # 現在のファイルの場所から相対的にパスを構築
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # utils/ -> project_root -> api/
            if current_dir.endswith('utils'):
                project_root = os.path.dirname(current_dir)
                api_dir = os.path.join(project_root, 'api')
            else:
                # 実行環境によってはパスが異なる場合の対応
                api_dir = os.path.join(current_dir, '..', 'api')
                api_dir = os.path.abspath(api_dir)
            
            model_files = {
                'density_model': os.path.join(api_dir, 'density_model.joblib'),
                'seats_model': os.path.join(api_dir, 'seats_model.joblib'),
                'best_params': os.path.join(api_dir, 'best_params.joblib'),
                'performance': os.path.join(api_dir, 'model_performance.joblib')
            }

            print(f"モデル検索ディレクトリ: {api_dir}")
        
            # ファイルの存在確認
            for name, path in model_files.items():
                exists = os.path.exists(path)
                print(f"📁 {name}: {path} - {'存在' if exists else '不存在'}")
                if not exists:
                    print(f"Warning: Model file not found: {path}")
        
            models = {}
            for name, path in model_files.items():
                try:
                    if os.path.exists(path):
                        models[name] = joblib.load(path)
                        print(f"✅ {name} 読み込み成功")
                    else:
                        models[name] = None
                        print(f"⚠️ {name} ファイルが見つかりません")
                except Exception as e:
                    print(f"❌ {name} 読み込みエラー: {str(e)}")
                    models[name] = None
            
            return models
            
        except Exception as e:
            print(f"モデル読み込み全体エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
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
                print("依存関係が利用できません")
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
                print("利用可能な特徴量がありません")
                return None
                
            X = feature_df[available_features].values
            return X
            
        except Exception as e:
            print(f"特徴量作成エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            return None
    
    def get_density_seats_ratio(self, day_of_week):
        """density_seats_ratioを取得"""
        try:
            # Supabaseからデータを取得（共通関数を使用）
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                print(f"曜日{day_of_week}のデータが見つかりません")
                return 0.5  # デフォルト値
            
            ratios = []
            for record in data:
                density_rate = record.get('density_rate', 0)
                occupied_seats = record.get('occupied_seats', 0)
                if occupied_seats > 0:
                    ratio = (density_rate / 100.0) / (occupied_seats + 1)
                    ratios.append(ratio)
            
            if not ratios:
                print(f"曜日{day_of_week}の有効な比率データがありません")
                return 0.5  # デフォルト値
            
            avg_ratio = sum(ratios) / len(ratios)
            return avg_ratio
            
        except Exception as e:
            print(f"density_seats_ratio取得エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            return 0.5  # デフォルト値
    
    def predict_with_models(self, day_of_week):
        """訓練済みモデルで予測"""
        try:
            # モデルの存在確認
            if (not self.models or 
                self.models.get('density_model') is None or 
                self.models.get('seats_model') is None):
                print("モデルが利用できないため、データベース平均を使用します。")
                return self.get_database_average(day_of_week)
            
            # 特徴量取得
            avg_density_seats_ratio = self.get_density_seats_ratio(day_of_week)
            features = self.create_features(day_of_week, avg_density_seats_ratio)
            
            if features is None:
                print("特徴量作成に失敗したため、データベース平均を使用します。")
                return self.get_database_average(day_of_week)
            
            # モデル予測実行
            try:
                print("機械学習モデルを使用して予測します。")
                density_pred = self.models['density_model'].predict(features)[0]
                seats_pred = self.models['seats_model'].predict(features)[0]
                
                # 予測結果の正規化
                occupancy_rate = max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred))
                occupied_seats = max(0, min(8, round(seats_pred)))
                
                return {
                    "occupancy_rate": round(occupancy_rate, 2),
                    "occupied_seats": occupied_seats,
                }
                
            except Exception as model_error:
                print(f"モデル予測エラー: {str(model_error)}")
                print(f"エラー詳細: {traceback.format_exc()}")
                return self.get_database_average(day_of_week)
            
        except Exception as e:
            print(f"予測全体エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            return self.get_database_average(day_of_week)
    
    def get_database_average(self, day_of_week):
        """データベースから平均値を計算"""
        try:
            print(f"曜日{day_of_week}のデータベース平均を計算します")
            # 共通関数を使用してデータを取得
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                print(f"曜日{day_of_week}のデータが見つかりません。デフォルト値を使用します。")
                return {
                    "occupancy_rate": 0.5,
                    "occupied_seats": 4,
                }
            
            total_density = sum(record.get('density_rate', 0) for record in data)
            total_seats = sum(record.get('occupied_seats', 0) for record in data)
            count = len(data)
            
            if count == 0:
                print("データ件数が0です。デフォルト値を使用します。")
                return {
                    "occupancy_rate": 0.5,
                    "occupied_seats": 4,
                }
            
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
            
        except Exception as e:
            print(f"データベース平均計算エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # 最終的なフォールバック
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
            
            def get_weekday_name(weekday):
                weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
                return weekday_names[weekday]
            
            print(f"今日の曜日: {today_weekday} ({get_weekday_name(today_weekday)})")
            print(f"明日の曜日: {tomorrow_weekday} ({get_weekday_name(tomorrow_weekday)})")
            
            # 土日の場合は空席
            if today_weekday >= 5:
                today_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
                print("今日は土日のため空席")
            else:
                print("今日の予測を実行中...")
                today_prediction = self.predict_with_models(today_weekday)
            
            if tomorrow_weekday >= 5:
                tomorrow_prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
                print("明日は土日のため空席")
            else:
                print("明日の予測を実行中...")
                tomorrow_prediction = self.predict_with_models(tomorrow_weekday)
            
            result = {
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
            
            print("今日・明日の予測完了")
            return result
            
        except Exception as e:
            print(f"今日・明日予測エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # エラー時のフォールバック
            return {
                "today": {
                    "weekday": 0,
                    "weekday_name": "エラー",
                    "occupancy_rate": 0.5,
                    "occupied_seats": 4
                },
                "tomorrow": {
                    "weekday": 1,
                    "weekday_name": "エラー",
                    "occupancy_rate": 0.5,
                    "occupied_seats": 4
                }
            }
    
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
                except Exception as day_error:
                    print(f"曜日{day_of_week}の予測エラー: {str(day_error)}")
                    # 個別の曜日でエラーが発生してもスキップ
                    weekly_averages.append({
                        "weekday": day_of_week,
                        "weekday_name": weekday_names[day_of_week],
                        "occupancy_rate": 0.5,
                        "occupied_seats": 4
                    })
            
            return {"weekly_averages": weekly_averages}
            
        except Exception as e:
            print(f"週間平均予測エラー: {str(e)}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # エラー時のフォールバック
            return {
                "weekly_averages": [
                    {"weekday": i, "weekday_name": f"曜日{i}", "occupancy_rate": 0.5, "occupied_seats": 4}
                    for i in range(5)
                ]
            }

if __name__ == "__main__":
    try:
        service = PredictionService()
        
        print("\n1. 今日・明日予測テスト")
        today_tomorrow = service.predict_today_tomorrow()
        print(f"今日: {today_tomorrow['today']}")
        print(f"明日: {today_tomorrow['tomorrow']}")
        
        print("\n2. 週間平均予測テスト")
        weekly = service.predict_weekly_average()
        for day_data in weekly['weekly_averages']:
            print(f"{day_data['weekday_name']}: 占有率{day_data['occupancy_rate']}, 席数{day_data['occupied_seats']}")
        
        print("\nテスト完了！")
        
    except Exception as e:
        print(f"メイン実行エラー: {str(e)}")
        print(f"エラー詳細: {traceback.format_exc()}")