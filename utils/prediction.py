"""
予測機能の統一化モジュール
models.pyのアンサンブルモデルを活用
"""
import sys
import os
import json
from datetime import datetime, timedelta

# 明示的なパス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
utils_dir = os.path.join(project_root, 'utils')

for path in [utils_dir, current_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from supabase_access import get_supabase_data

try:
    import joblib
    import pandas as pd
    import numpy as np
    from data_processor import engineer_features, get_feature_columns
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

class PredictionService:
    """統一予測"""
    
    def __init__(self):
        self.ensemble_models = self._load_ensemble_models()
        
        # JSONファイルの保存先
        self.weekly_averages_file = os.path.join(project_root, 'api/weekly_averages_predictions.json')
    
    def _load_ensemble_models(self):
        """アンサンブルモデルを読み込む"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))            
            model_files = {
                'density_model': os.path.join(current_dir, 'joblib/density_model.joblib'),
                'seats_model': os.path.join(current_dir, 'joblib/seats_model.joblib')
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
            return {'density_model': None, 'seats_model': None}

    def create_features(self, day_of_week):
        """特徴量を作成（Supabaseデータから平均値を使用）"""
        try:
            # Supabaseから該当曜日の実データを取得して平均値を計算
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                raise ValueError(f"曜日{day_of_week}のデータがSupabaseに存在しません")
            
            # 実データから平均値を計算
            avg_density_rate = sum(record.get('density_rate', 0) for record in data) / len(data)
            avg_occupied_seats = sum(record.get('occupied_seats', 0) for record in data) / len(data)
            
            # データプロセッサと同じ10個の特徴量を作成
            features = np.zeros((1, 10))
            
            # 1. day_of_week
            features[0, 0] = day_of_week
            
            # 2. density_seats_ratio（実データから計算）
            features[0, 1] = avg_density_rate / (avg_occupied_seats + 1)
            
            # 3-7. 曜日ダミー変数
            if day_of_week == 0:  # 月曜日
                features[0, 2] = 1
            elif day_of_week == 1:  # 火曜日
                features[0, 3] = 1
            elif day_of_week == 2:  # 水曜日
                features[0, 4] = 1
            elif day_of_week == 3:  # 木曜日
                features[0, 5] = 1
            elif day_of_week == 4:  # 金曜日
                features[0, 6] = 1
            
            # 8-10. 週の時期フラグ
            if day_of_week in [0, 1]:  # 月火（早い週）
                features[0, 7] = 1
            elif day_of_week == 2:  # 水（中間週）
                features[0, 8] = 1
            elif day_of_week in [3, 4]:  # 木金（遅い週）
                features[0, 9] = 1
            
            return features
            
        except Exception as e:
            raise Exception(f"特徴量作成エラー (曜日{day_of_week}): {str(e)}")
    

    
    def predict_with_models(self, day_of_week):
        """アンサンブルモデルで予測"""
        try:
            # モデルの存在確認
            if (not self.ensemble_models or 
                self.ensemble_models.get('density_model') is None or 
                self.ensemble_models.get('seats_model') is None):
                return self.get_database_average(day_of_week)
            
            # 特徴量作成
            features = self.create_features(day_of_week)
            
            if features is None:
                return self.get_database_average(day_of_week)
            
            # アンサンブルモデルで予測実行
            try:
                density_pred = self.ensemble_models['density_model'].predict(features)[0]
                seats_pred = self.ensemble_models['seats_model'].predict(features)[0]
                
                # 予測結果の正規化（アンサンブルモデルからの出力を適切に処理）
                if density_pred > 1:  # パーセンテージ形式の場合
                    occupancy_rate = max(0.0, min(1.0, density_pred / 100.0))
                else:  # 0-1の範囲の場合
                    occupancy_rate = max(0.0, min(1.0, density_pred))
                
                occupied_seats = max(0, min(8, round(seats_pred)))
                
                # デバッグ用ログ（本番では削除可能）
                print(f"[ML予測] 曜日{day_of_week}: 占有率={round(occupancy_rate, 2)}, 座席数={occupied_seats} (Raw: density={density_pred:.4f}, seats={seats_pred:.4f})")
                
                return {
                    "occupancy_rate": round(occupancy_rate, 2),
                    "occupied_seats": occupied_seats,
                }
                
            except Exception as e:
                raise Exception(f"アンサンブルモデル予測エラー (曜日{day_of_week}): {str(e)}")
            
        except Exception as e:
            raise Exception(f"予測処理エラー (曜日{day_of_week}): {str(e)}")
    
    def get_database_average(self, day_of_week):
        """データベースから平均値を計算"""
        try:
            data = get_supabase_data(f"day_of_week=eq.{day_of_week}&select=density_rate,occupied_seats")
            
            if not data:
                raise ValueError(f"曜日{day_of_week}のデータがSupabaseに存在しません")
            
            total_density = sum(record.get('density_rate', 0) for record in data)
            total_seats = sum(record.get('occupied_seats', 0) for record in data)
            count = len(data)
            
            if count == 0:
                raise ValueError(f"曜日{day_of_week}の有効なデータが見つかりません")
            
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
            raise Exception(f"データベース平均値計算エラー (曜日{day_of_week}): {str(e)}")

    def predict_weekly(self):
        """今日から1週間分の予測（7日間、土日は占有率0）"""
        try:
            now = datetime.now()
            current_date = now.date()
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            
            predictions = []
            
            # 7日分の予測を収集
            for i in range(7):
                weekday = current_date.weekday()
                
                # 平日は予測モデル、土日はSupabaseの実データがあれば使用
                if weekday < 5:  # 月曜日から金曜日
                    prediction = self.predict_with_models(weekday)
                else:  # 土曜日・日曜日
                    try:
                        # 土日もSupabaseに実データがあるかチェック
                        prediction = self.get_database_average(weekday)
                    except Exception:
                        # 土日のデータがない場合は0として処理（業務仕様）
                        prediction = {"occupancy_rate": 0.0, "occupied_seats": 0}
                
                predictions.append({
                    "weekday": weekday,
                    "weekday_name": weekday_names[weekday],
                    "is_weekend": weekday >= 5,
                    **prediction
                })
                
                current_date += timedelta(days=1)
            
            return predictions
            
        except Exception as e:
            raise e

    def predict_5days(self):
        """今日から5日分の予測（平日のみ、土日はスキップ）"""
        try:
            # 1週間分の予測から平日のみを抽出
            weekly_result = self.predict_weekly()
            
            result = {}
            day_count = 0
            
            for i in range(7):
                if i < len(weekly_result) and not weekly_result[i]["is_weekend"]:
                    if day_count == 0:
                        result["today"] = weekly_result[i]
                    elif day_count == 1:
                        result["tomorrow"] = weekly_result[i]
                    else:
                        result[f"day{day_count}"] = weekly_result[i]
                    
                    day_count += 1
                    if day_count >= 5:
                        break
            
            return result
            
        except Exception as e:
            raise e

    def predict_weekly_average(self):
        """週間平均値（データベース統計平均のみ使用）"""
        try:
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            weekly_averages = []
            
            for day_of_week in range(5):  # 平日のみ
                try:
                    # 週間平均は常にデータベースの統計平均値を使用
                    prediction = self.get_database_average(day_of_week)
                    
                    weekly_averages.append({
                        "weekday": day_of_week,
                        "weekday_name": weekday_names[day_of_week],
                        "is_weekend": False,  # 平日のみなので常にFalse
                        **prediction
                    })
                except Exception as e:
                    # 個別の曜日でエラーが発生した場合はエラーを再発生
                    raise Exception(f"曜日{day_of_week}({weekday_names[day_of_week]})の統計平均値計算でエラー: {str(e)}")
            
            return {"weekly_averages": weekly_averages}
            
        except Exception as e:
            raise e

    def get_model_accuracy(self):
        """実際のモデル性能指標を取得"""
        try:
            # models.pyのMLPredictorを使用してモデル情報を取得
            from models import MLPredictor
            
            predictor = MLPredictor()
            if predictor.load_models():
                model_info = predictor.get_model_info()
                model_performance = model_info.get('model_performance', {})
                
                accuracy_info = {}
                if 'density' in model_performance:
                    density_r2 = model_performance['density'].get('test_r2')
                    if density_r2 is not None:
                        accuracy_info['density_r2'] = f"{density_r2:.3f}"
                    else:
                        accuracy_info['density_r2'] = "N/A"
                else:
                    accuracy_info['density_r2'] = "N/A"
                
                if 'seats' in model_performance:
                    seats_r2 = model_performance['seats'].get('test_r2')
                    if seats_r2 is not None:
                        accuracy_info['seats_r2'] = f"{seats_r2:.3f}"
                    else:
                        accuracy_info['seats_r2'] = "N/A"
                else:
                    accuracy_info['seats_r2'] = "N/A"
                
                return accuracy_info
            else:
                return {"density_r2": "N/A", "seats_r2": "N/A"}
                
        except Exception as e:
            print(f"モデル精度情報取得エラー: {e}")
            return {"density_r2": "N/A", "seats_r2": "N/A"}

    def save_predictions_to_json(self):
        """予測結果をJSONファイルに保存する（週間予測と週間平均のみ）"""
        try:
            # 1. 週間予測（7日間、土日含む）を生成・保存
            weekly_predictions_data = self.predict_weekly()
            weekly_predictions_file = os.path.join(project_root, 'api/weekly_predictions.json')
            with open(weekly_predictions_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_predictions_data, f, ensure_ascii=False, indent=2)
            
            # 2. 週間平均予測を生成・保存
            weekly_averages_data = self.predict_weekly_average()
            weekly_averages_file = os.path.join(project_root, 'api/weekly_averages.json')
            with open(weekly_averages_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_averages_data, f, ensure_ascii=False, indent=2)
            
            # 3. 更新情報とデータタイプを記録
            timestamp_file = os.path.join(project_root, 'api/last_update.json')
            has_models = (self.ensemble_models and 
                         self.ensemble_models.get('density_model') is not None and 
                         self.ensemble_models.get('seats_model') is not None)
            
            # 実際のモデル精度を動的に取得
            model_accuracy = self.get_model_accuracy()
            
            timestamp_data = {
                "last_update": datetime.now().isoformat(),
                "available_files": {
                    "weekly_predictions": {
                        "file": "weekly_predictions.json",
                        "description": "今日から7日間の予測（土日含む）",
                        "data_type": "predictions" if has_models else "database_averages",
                        "model_type": "ensemble_learning" if has_models else "database_fallback"
                    },
                    "weekly_averages": {
                        "file": "weekly_averages.json", 
                        "description": "平日の曜日別データベース統計平均値（実データのみ）",
                        "data_type": "database_statistics",
                        "model_type": "statistical_average"
                    }
                },
                "prediction_info": {
                    "has_trained_models": has_models,
                    "prediction_method": "ensemble_model" if has_models else "database_average",
                    "model_accuracy": model_accuracy
                }
            }
            with open(timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "files": {
                    "weekly_predictions": weekly_predictions_file,
                    "weekly_averages": weekly_averages_file,
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
            print("✅ アンサンブル予測データが正常に保存されました")
            for name, file_path in result["files"].items():
                print(f"- {name}: {file_path}")
        else:
            print(f"❌ 予測データの保存に失敗しました: {result['error']}")
            
    except Exception as e:
        print(f"実行エラー: {str(e)}")