#!/usr/bin/env python3
import os
import sys
import json
from typing import Dict
import numpy as np
import joblib
import optuna
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
project_root = os.path.dirname(current_dir)

from data_processor import MLDataProcessor

optuna.logging.set_verbosity(optuna.logging.WARNING)


class Trainer:
    def __init__(self, n_trials: int = 100):
        self.n_trials = n_trials
        self.data_processor = MLDataProcessor()
        self.X, self.y_density, self.y_seats = None, None, None
        self.best_models = {}
        self.best_params = {}
        self.results = {}

    def prepare_data(self) -> None:
        ml_data, self.X, self.y_density, self.y_seats = (
            self.data_processor.prepare_ml_data()
        )

        if len(ml_data) == 0:
            raise ValueError("訓練用データが存在しません")

    def objective_density(self, trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
            "random_state": 42,
            "n_jobs": -1,
        }

        model = RandomForestRegressor(**params)
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            model, self.X, self.y_density, cv=kfold, scoring="neg_mean_squared_error"
        )

        return np.sqrt(-cv_scores.mean())

    def objective_seats(self, trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
            "random_state": 42,
            "n_jobs": -1,
        }

        model = RandomForestRegressor(**params)
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            model, self.X, self.y_seats, cv=kfold, scoring="neg_mean_squared_error"
        )

        return np.sqrt(-cv_scores.mean())

    def optimize_and_train(self) -> Dict:
        self.prepare_data()

        # 密度率予測モデルの最適化
        study_density = optuna.create_study(direction="minimize")
        study_density.optimize(self.objective_density, n_trials=self.n_trials)
        self.best_params["density"] = study_density.best_params

        # 占有座席数予測モデルの最適化
        study_seats = optuna.create_study(direction="minimize")
        study_seats.optimize(self.objective_seats, n_trials=self.n_trials)
        self.best_params["seats"] = study_seats.best_params

        # 最適パラメータでモデル訓練
        self._train_final_models()

        # 結果をまとめ
        self.results = {
            "density": {
                "best_params": self.best_params["density"],
                "best_cv_rmse": study_density.best_value,
                "n_trials": self.n_trials,
                "data_size": len(self.X),
            },
            "seats": {
                "best_params": self.best_params["seats"],
                "best_cv_rmse": study_seats.best_value,
                "n_trials": self.n_trials,
                "data_size": len(self.X),
            },
        }

        return self.results

    def _train_final_models(self) -> None:
        # 密度率予測モデル
        self.best_models["density"] = RandomForestRegressor(
            **self.best_params["density"]
        )
        self.best_models["density"].fit(self.X, self.y_density)

        # 占有座席数予測モデル
        self.best_models["seats"] = RandomForestRegressor(**self.best_params["seats"])
        self.best_models["seats"].fit(self.X, self.y_seats)

    def save_models(self, model_dir: str = "utils/joblib") -> Dict[str, str]:
        os.makedirs(model_dir, exist_ok=True)
        saved_files = {}

        # モデル保存
        for target, model in self.best_models.items():
            model_path = os.path.join(model_dir, f"{target}_model.joblib")
            joblib.dump(model, model_path)
            saved_files[f"{target}_model"] = model_path

        # 最適パラメータと結果を保存
        performance_path = os.path.join(model_dir, "model_performance.joblib")
        joblib.dump(self.results, performance_path)
        saved_files["model_performance"] = performance_path

        # パラメータをJSONでも保存
        params_path = os.path.join(model_dir, "best_params.json")
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(self.best_params, f, ensure_ascii=False, indent=2)
        saved_files["best_params"] = params_path

        return saved_files


def main():
    try:
        trainer = Trainer(n_trials=100)
        results = trainer.optimize_and_train()
        trainer.save_models()

        output_file = os.path.join(project_root, "training_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        return results

    except Exception as e:
        print(f"訓練エラー: {str(e)}")


if __name__ == "__main__":
    try:
        print("訓練を開始します...")
        main()
        print("訓練完了")
    except Exception as e:
        print(f"訓練エラー: {str(e)}")
