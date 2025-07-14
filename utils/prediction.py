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
        self.data_processor = MLDataProcessor()
        self.models = {}
        self.feature_stats = None
        self._load_models()

    def _load_models(self) -> None:
        """機械学習モデルを読み込み"""
        model_dir = "utils/joblib"
        for target in ["density", "seats"]:
            model_path = os.path.join(model_dir, f"{target}_model.joblib")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
            self.models[target] = joblib.load(model_path)

        # 特徴量統計を計算
        ml_data, _, _, _ = self.data_processor.prepare_ml_data()
        if len(ml_data) == 0:
            raise RuntimeError("実データが取得できません")
        self.feature_stats = {
            "density_seats_ratio_mean": ml_data["density_seats_ratio"].mean()
        }

    def _predict_day(self, day_of_week: int) -> Dict:
        """単日の予測を実行"""
        if day_of_week == 0 or day_of_week == 6:  # 土日
            return {"density_rate": 0.0, "occupied_seats": 0}

        if not 1 <= day_of_week <= 5:
            raise ValueError(f"無効な曜日: {day_of_week}")

        # 特徴量を作成
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
        X = np.array([features])

        # 予測を実行
        density_pred = self.models["density"].predict(X)[0]
        seats_pred = self.models["seats"].predict(X)[0]

        return {
            "density_rate": round(max(0.0, min(100.0, density_pred)), 2),
            "occupied_seats": max(0, min(8, int(round(seats_pred)))),
        }

    def predict_weekly(self) -> Dict:
        """今後7日間の予測を生成"""
        now = datetime.now()
        predictions = []

        for i in range(7):
            target_date = now.date() + timedelta(days=i)
            day_of_week = target_date.weekday()
            user_weekday = (day_of_week + 1) % 7

            prediction = self._predict_day(user_weekday)
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
        ml_data, _, _, _ = self.data_processor.prepare_ml_data()
        if len(ml_data) == 0:
            raise RuntimeError("実データが取得できません")

        weekly_averages = []

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
                day_data = ml_data[ml_data["day_of_week"] == user_weekday]
                if len(day_data) == 0:
                    raise RuntimeError(f"曜日{user_weekday}のデータが存在しません")

                weekly_averages.append(
                    {
                        "weekday": user_weekday,
                        "weekday_name": self.weekday_names[user_weekday],
                        "density_rate": round(day_data["density_rate"].mean(), 2),
                        "occupied_seats": round(day_data["occupied_seats"].mean()),
                        "data_count": len(day_data),
                    }
                )

        return {"weekly_averages": weekly_averages}

    def save_predictions_to_json(self) -> Dict:
        """予測結果をJSONファイルとして保存"""
        # 週間予測を保存
        weekly_predictions = self.predict_weekly()
        weekly_predictions_file = os.path.join(
            project_root, "api/weekly_predictions.json"
        )
        with open(weekly_predictions_file, "w", encoding="utf-8") as f:
            json.dump(weekly_predictions, f, ensure_ascii=False, indent=2)

        # 週間平均を保存
        weekly_averages = self.predict_weekly_averages()
        weekly_averages_file = os.path.join(project_root, "api/weekly_averages.json")
        with open(weekly_averages_file, "w", encoding="utf-8") as f:
            json.dump(weekly_averages, f, ensure_ascii=False, indent=2)

        # 最終更新時刻を保存
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
    service = PredictionService()
    result = service.save_predictions_to_json()

    print("\n予測データの生成が完了しました:")
    for name, file_path in result["files"].items():
        print(f"  - {name}: {file_path}")


if __name__ == "__main__":
    main()
