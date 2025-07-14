#!/usr/bin/env python3
import sys
import os
import json
import numpy as np
import joblib
from datetime import datetime, timedelta
from typing import Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
project_root = os.path.dirname(current_dir)

from data_processor import MLDataProcessor


class MLPredictor:
    def __init__(self, model_dir: str = "utils/joblib"):
        self.models = {}
        self.model_dir = model_dir
        self.data_processor = MLDataProcessor()
        self.feature_stats = None
        self.load_models()

    def predict(self, day_of_week: int) -> Dict:
        if not 1 <= day_of_week <= 5:
            raise ValueError(f"無効な曜日: {day_of_week}")

        if not self.models or not self.feature_stats:
            raise ValueError("モデルまたは特徴量統計が読み込まれていません")

        features = self._create_features(day_of_week)
        X = np.array([features])

        predictions = {
            "day_of_week": day_of_week,
            "day_name": ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"][
                day_of_week - 1
            ],
        }

        if "density" in self.models:
            density_pred = self.models["density"].predict(X)[0]
            predictions["density_rate"] = round(max(0.0, min(100.0, density_pred)), 2)

        if "seats" in self.models:
            seats_pred = self.models["seats"].predict(X)[0]
            predictions["occupied_seats"] = max(0, min(8, int(round(seats_pred))))

        return predictions

    def _create_features(self, day_of_week: int) -> list:
        features = [
            day_of_week,
            self.feature_stats["density_seats_ratio_mean"],
            1 if day_of_week == 1 else 0,
            1 if day_of_week == 2 else 0,
            1 if day_of_week == 3 else 0,
            1 if day_of_week == 4 else 0,
            1 if day_of_week == 5 else 0,
            1 if day_of_week in [1, 2] else 0,
            1 if day_of_week == 3 else 0,
            1 if day_of_week in [4, 5] else 0,
        ]
        return features

    def load_models(self) -> bool:
        try:
            for target in ["density", "seats"]:
                model_path = os.path.join(self.model_dir, f"{target}_model.joblib")
                if os.path.exists(model_path):
                    self.models[target] = joblib.load(model_path)
                else:
                    return False
            return True
        except Exception:
            return False


class PredictionService:
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
        self.predictor = MLPredictor()
        self.data_processor = MLDataProcessor()

    def predict_single_day(self, day_of_week: int) -> Dict:
        if day_of_week == 0 or day_of_week == 6:
            return {"density_rate": 0.0, "occupied_seats": 0}

        if 1 <= day_of_week <= 5:
            try:
                result = self.predictor.predict(day_of_week)
                return {
                    "density_rate": round(float(result["density_rate"]), 2),
                    "occupied_seats": int(result["occupied_seats"]),
                }
            except Exception as e:
                raise RuntimeError(f"予測エラー: {e}")

        raise ValueError(f"無効な曜日: {day_of_week}")

    def predict_weekly(self) -> Dict:
        now = datetime.now()
        predictions = []

        for i in range(7):
            target_date = now.date() + timedelta(days=i)
            day_of_week = target_date.weekday()
            user_weekday = (day_of_week + 1) % 7

            prediction = self.predict_single_day(user_weekday)
            predictions.append(
                {
                    "date": target_date.isoformat(),
                    "weekday": user_weekday,
                    "weekday_name": self.weekday_names[user_weekday],
                    "density_rate": prediction["density_rate"],
                    "occupied_seats": prediction["occupied_seats"],
                }
            )

        return {"weekly_predictions": predictions}

    def predict_weekly_averages(self) -> Dict:
        """実データから曜日ごとの平均値を計算"""
        try:
            # MLDataProcessorを使用して実データを取得
            ml_data, _, _, _ = self.data_processor.prepare_ml_data()

            if len(ml_data) == 0:
                raise RuntimeError("実データが取得できません")

            weekly_averages = []

            # 曜日ごとの平均値を計算
            for user_weekday in range(7):
                if user_weekday == 0 or user_weekday == 6:  # 土日
                    weekly_averages.append(
                        {
                            "weekday": user_weekday,
                            "weekday_name": self.weekday_names[user_weekday],
                            "density_rate": 0.0,
                            "occupied_seats": 0,
                        }
                    )
                else:  # 平日
                    # DB形式の曜日（1-5）に変換
                    db_weekday = user_weekday
                    day_data = ml_data[ml_data["day_of_week"] == db_weekday]

                    if len(day_data) > 0:
                        avg_density = round(day_data["density_rate"].mean(), 2)
                        avg_seats = round(day_data["occupied_seats"].mean())
                        data_count = len(day_data)
                    else:
                        avg_density = 0.0
                        avg_seats = 0
                        data_count = 0

                    weekly_averages.append(
                        {
                            "weekday": user_weekday,
                            "weekday_name": self.weekday_names[user_weekday],
                            "density_rate": avg_density,
                            "occupied_seats": avg_seats,
                            "data_type": "real_data_average",
                            "data_count": data_count,
                        }
                    )

            return {"weekly_averages": weekly_averages}

        except Exception as e:
            raise RuntimeError(f"週間平均計算エラー: {e}")

    def save_predictions_to_json(self) -> Dict:
        weekly_predictions = self.predict_weekly()
        weekly_predictions_file = os.path.join(
            project_root, "api/weekly_predictions.json"
        )

        with open(weekly_predictions_file, "w", encoding="utf-8") as f:
            json.dump(weekly_predictions, f, ensure_ascii=False, indent=2)

        weekly_averages = self.predict_weekly_averages()
        weekly_averages_file = os.path.join(project_root, "api/weekly_averages.json")

        with open(weekly_averages_file, "w", encoding="utf-8") as f:
            json.dump(weekly_averages, f, ensure_ascii=False, indent=2)

        timestamp_data = {
            "last_update": datetime.now().isoformat(),
            "files": {
                "weekly_predictions": "weekly_predictions.json",
                "weekly_averages": "weekly_averages.json",
            },
        }

        timestamp_file = os.path.join(project_root, "api/last_update.json")
        with open(timestamp_file, "w", encoding="utf-8") as f:
            json.dump(timestamp_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "files": {
                "weekly_predictions": weekly_predictions_file,
                "weekly_averages": weekly_averages_file,
                "last_update": timestamp_file,
            },
        }


def main():
    try:
        service = PredictionService()
        result = service.save_predictions_to_json()

        print("\n予測データの生成が完了しました:")
        for name, file_path in result["files"].items():
            print(f"  - {name}: {file_path}")

    except Exception as e:
        print(f"実行エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
