#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime, timedelta
import numpy as np

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
utils_dir = current_dir

for path in [utils_dir, current_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from models import MLPredictor


class PredictionService:
    """予測専用サービス（純粋ML版）"""

    def __init__(self):
        self.weekday_names = [
            "日曜日",
            "月曜日",
            "火曜日",
            "水曜日",
            "木曜日",
            "金曜日",
            "土曜日",
        ]
        self.predictor = None
        self._load_predictor()

    def _load_predictor(self):
        """予測モデルを読み込み"""
        try:
            self.predictor = MLPredictor()
            print("✅ 予測モデルを読み込みました")
        except Exception as e:
            raise RuntimeError(f"モデル読み込みエラー: {e}")

    def predict_single_day(self, day_of_week):
        """
        Args:
            day_of_week: 曜日（1-5: 月-金、0,6: 土日は0を返す）

        Returns:
            dict: 予測結果
        """
        # 土日は0を返す（ビジネスロジック）
        if day_of_week == 0 or day_of_week == 6:
            return {
                "density_rate": 0.0,
                "occupied_seats": 0,
                "prediction_type": "weekend_zero",
            }

        # 平日のみ機械学習予測
        if 1 <= day_of_week <= 5:
            if not self.predictor:
                raise RuntimeError("予測モデルが初期化されていません")

            try:
                result = self.predictor.predict(day_of_week)
                return {
                    "density_rate": round(float(result["density_rate"]), 2),
                    "occupied_seats": int(result["occupied_seats"]),
                    "prediction_type": "ml_model",
                }
            except Exception as e:
                raise RuntimeError(f"予測エラー (曜日{day_of_week}): {e}")

        raise ValueError(f"無効な曜日です: {day_of_week}")

    def predict_weekly(self):
        """7日分のモデル予測データ生成"""
        now = datetime.now()
        current_date = now.date()
        predictions = []

        for i in range(7):
            target_date = current_date + timedelta(days=i)
            day_of_week = target_date.weekday()  # 0=月曜日, 6=日曜日
            user_weekday = (day_of_week + 1) % 7  # 0=日曜日, 1=月曜日, ..., 6=土曜日

            prediction = self.predict_single_day(user_weekday)
            predictions.append(
                {
                    "date": target_date.isoformat(),
                    "weekday": user_weekday,
                    "weekday_name": self.weekday_names[user_weekday],
                    "density_rate": prediction["density_rate"],
                    "occupied_seats": prediction["occupied_seats"],
                    "prediction_type": prediction["prediction_type"],
                }
            )

        return {"weekly_predictions": predictions}

    def predict_weekly_averages(self):
        """曜日ごとの実データ平均値計算"""
        from supabase_access import get_supabase_data

        weekly_averages = []

        # 曜日ごとの実データ平均値を計算
        weekday_averages = {}

        for day in range(1, 6):  # 平日のみ（DB形式: 1-5）
            # 曜日ごとのデータを取得
            day_data = get_supabase_data(
                f"day_of_week=eq.{day}&select=density_rate,occupied_seats"
            )

            if not day_data or len(day_data) == 0:
                raise RuntimeError(f"曜日{day}のデータが取得できませんでした")

            # 実データの平均値を計算
            density_rates = [
                float(record["density_rate"])
                for record in day_data
                if record.get("density_rate") is not None
            ]
            occupied_seats = [
                int(record["occupied_seats"])
                for record in day_data
                if record.get("occupied_seats") is not None
            ]

            if not density_rates or not occupied_seats:
                raise RuntimeError(f"曜日{day}に有効なデータがありません")

            avg_density = round(np.mean(density_rates), 2)
            avg_seats = round(np.mean(occupied_seats))

            weekday_averages[day] = {
                "density_rate": avg_density,
                "occupied_seats": avg_seats,
                "data_count": len(day_data),
            }
            print(
                f"✅ 曜日{day}の実データ平均値を計算しました（データ数: {len(day_data)}）"
            )

        # 曜日ごとの平均値を設定
        for user_weekday in range(7):
            if user_weekday == 0 or user_weekday == 6:  # 土日
                weekly_averages.append(
                    {
                        "weekday": user_weekday,
                        "weekday_name": self.weekday_names[user_weekday],
                        "density_rate": 0.0,
                        "occupied_seats": 0,
                        "data_type": "weekend_zero",
                        "data_count": 0,
                    }
                )
            else:  # 平日
                weekly_averages.append(
                    {
                        "weekday": user_weekday,
                        "weekday_name": self.weekday_names[user_weekday],
                        "density_rate": weekday_averages[user_weekday]["density_rate"],
                        "occupied_seats": weekday_averages[user_weekday][
                            "occupied_seats"
                        ],
                        "data_type": "real_data_average",
                        "data_count": weekday_averages[user_weekday]["data_count"],
                    }
                )

        return {"weekly_averages": weekly_averages}

    def save_predictions_to_json(self):
        """予測結果をJSONファイルに保存"""
        # 1. 週間予測データ保存
        weekly_predictions = self.predict_weekly()
        weekly_predictions_file = os.path.join(
            project_root, "api/weekly_predictions.json"
        )

        with open(weekly_predictions_file, "w", encoding="utf-8") as f:
            json.dump(
                weekly_predictions,
                f,
                ensure_ascii=False,
                indent=2,
                default=numpy_to_python,
            )

        # 2. 週間平均データ保存
        weekly_averages = self.predict_weekly_averages()
        weekly_averages_file = os.path.join(project_root, "api/weekly_averages.json")

        with open(weekly_averages_file, "w", encoding="utf-8") as f:
            json.dump(
                weekly_averages,
                f,
                ensure_ascii=False,
                indent=2,
                default=numpy_to_python,
            )

        # 3. 更新情報保存
        timestamp_data = {
            "last_update": datetime.now().isoformat(),
            "model_status": "ml_model_only",
            "files": {
                "weekly_predictions": "weekly_predictions.json",
                "weekly_averages": "weekly_averages.json",
            },
            "weekday_format": "sunday_0_to_saturday_6",
            "business_days": [1, 2, 3, 4, 5],
            "fallback_disabled": True,
        }

        timestamp_file = os.path.join(project_root, "api/last_update.json")
        with open(timestamp_file, "w", encoding="utf-8") as f:
            json.dump(
                timestamp_data,
                f,
                ensure_ascii=False,
                indent=2,
                default=numpy_to_python,
            )

        return {
            "success": True,
            "files": {
                "weekly_predictions": weekly_predictions_file,
                "weekly_averages": weekly_averages_file,
                "last_update": timestamp_file,
            },
        }


def numpy_to_python(obj):
    """numpy型をPython標準型に変換"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def main():
    try:
        service = PredictionService()
        result = service.save_predictions_to_json()

        print("\n✅ 予測データの生成が完了しました:")
        for name, file_path in result["files"].items():
            print(f"  - {name}: {file_path}")

    except Exception as e:
        print(f"❌ 実行エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
