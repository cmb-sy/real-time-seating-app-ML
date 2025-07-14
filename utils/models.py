"""
機械学習モデルモジュール（訓練と予測を分離）
Supabaseの実データのみを使用したRandomForest予測
"""

# 共通インポート
import numpy as np
import joblib
import logging
import os
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)


class MLTrainer:
    """機械学習モデル訓練クラス（訓練専用）"""

    def __init__(self):
        """初期化"""
        # 訓練時のみ必要な重いインポート
        import pandas as pd
        from sklearn.model_selection import train_test_split, cross_val_score, KFold
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        from data_processor import MLDataProcessor

        # インスタンス変数に保存
        self.pd = pd
        self.train_test_split = train_test_split
        self.cross_val_score = cross_val_score
        self.KFold = KFold
        self.RandomForestRegressor = RandomForestRegressor
        self.mean_squared_error = mean_squared_error
        self.mean_absolute_error = mean_absolute_error
        self.r2_score = r2_score

        self.models = {}
        self.model_performance = {}
        self.data_processor = MLDataProcessor()

    def train_models(self) -> Dict:
        """
        Supabaseの実データのみでRandomForestモデルを訓練

        Returns:
            Dict: モデル性能評価結果
        """
        logger.info("Supabaseの実データでモデルを訓練中...")

        # データ準備
        ml_data, X, y_density, y_seats = self.data_processor.prepare_ml_data()

        if len(ml_data) == 0:
            raise ValueError("Supabaseに訓練用データが存在しません")

        results = {}

        # 密度率予測モデル
        try:
            # RandomForestモデル（実データサイズに基づく動的設定）
            data_size = len(X)
            n_estimators = min(200, max(50, data_size // 10))
            max_depth = min(10, max(3, int(np.log2(data_size + 1))))

            model_density = self.RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=max(2, data_size // 50),
                random_state=42,
                n_jobs=-1,
            )

            # 訓練・テストデータ分割
            X_train, X_test, y_train, y_test = self.train_test_split(
                X, y_density, test_size=0.2, random_state=42, shuffle=True
            )

            # モデル訓練
            model_density.fit(X_train, y_train)
            y_pred = model_density.predict(X_test)

            # 評価指標計算
            rmse = np.sqrt(self.mean_squared_error(y_test, y_pred))
            mae = self.mean_absolute_error(y_test, y_pred)
            r2 = self.r2_score(y_test, y_pred)

            # クロスバリデーション
            kfold = self.KFold(
                n_splits=min(5, data_size // 10), shuffle=True, random_state=42
            )
            cv_scores = self.cross_val_score(
                model_density,
                X_train,
                y_train,
                cv=kfold,
                scoring="neg_mean_squared_error",
            )
            cv_rmse = np.sqrt(-cv_scores.mean())

            results["density"] = {
                "model_type": "random_forest",
                "test_rmse": rmse,
                "test_mae": mae,
                "test_r2": r2,
                "cv_rmse": cv_rmse,
                "data_size": data_size,
                "feature_count": X.shape[1],
            }

            self.models["density"] = model_density
            logger.info(f"密度率予測モデル訓練完了 - RMSE: {rmse:.4f}, R²: {r2:.4f}")

        except Exception as e:
            logger.error(f"密度率予測モデルの訓練エラー: {str(e)}")
            results["density"] = {"error": str(e)}

        # 占有座席数予測モデル
        try:
            model_seats = self.RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=max(2, data_size // 50),
                random_state=42,
                n_jobs=-1,
            )

            X_train, X_test, y_train, y_test = self.train_test_split(
                X, y_seats, test_size=0.2, random_state=42, shuffle=True
            )

            model_seats.fit(X_train, y_train)
            y_pred = model_seats.predict(X_test)

            rmse = np.sqrt(self.mean_squared_error(y_test, y_pred))
            mae = self.mean_absolute_error(y_test, y_pred)
            r2 = self.r2_score(y_test, y_pred)

            kfold = self.KFold(
                n_splits=min(5, data_size // 10), shuffle=True, random_state=42
            )
            cv_scores = self.cross_val_score(
                model_seats,
                X_train,
                y_train,
                cv=kfold,
                scoring="neg_mean_squared_error",
            )
            cv_rmse = np.sqrt(-cv_scores.mean())

            results["seats"] = {
                "model_type": "random_forest",
                "test_rmse": rmse,
                "test_mae": mae,
                "test_r2": r2,
                "cv_rmse": cv_rmse,
                "data_size": data_size,
                "feature_count": X.shape[1],
            }

            self.models["seats"] = model_seats
            logger.info(
                f"占有座席数予測モデル訓練完了 - RMSE: {rmse:.4f}, R²: {r2:.4f}"
            )

        except Exception as e:
            logger.error(f"占有座席数予測モデルの訓練エラー: {str(e)}")
            results["seats"] = {"error": str(e)}

        self.model_performance = results
        return results

    def save_models(self, model_dir: str = "utils/joblib") -> Dict[str, str]:
        """
        訓練済みモデルを保存

        Args:
            model_dir: 保存ディレクトリ

        Returns:
            Dict[str, str]: 保存されたファイルパス
        """
        os.makedirs(model_dir, exist_ok=True)
        saved_files = {}

        # モデル保存
        for target, model in self.models.items():
            model_path = os.path.join(model_dir, f"{target}_model.joblib")
            joblib.dump(model, model_path)
            saved_files[f"{target}_model"] = model_path

        # モデル性能情報を保存
        if self.model_performance:
            performance_path = os.path.join(model_dir, "model_performance.joblib")
            joblib.dump(self.model_performance, performance_path)
            saved_files["model_performance"] = performance_path

        logger.info(f"モデルを保存しました: {saved_files}")
        return saved_files


class MLPredictor:
    """機械学習予測クラス（予測専用・軽量）"""

    def __init__(self, model_dir: str = "utils/joblib"):
        """
        初期化

        Args:
            model_dir: モデルファイルのディレクトリ
        """
        self.models = {}
        self.model_performance = {}
        self.model_dir = model_dir
        self.feature_names = [
            "day_of_week",
            "density_seats_ratio",
            "is_monday",
            "is_tuesday",
            "is_wednesday",
            "is_thursday",
            "is_friday",
            "is_early_week",
            "is_mid_week",
            "is_late_week",
        ]

        # モデル自動読み込み
        self.load_models()

    def predict(self, day_of_week: int) -> Dict:
        """
        指定された曜日の密度率と占有座席数を予測

        Args:
            day_of_week: 曜日（1-5: 月-金）

        Returns:
            Dict: 予測結果
        """
        if day_of_week < 1 or day_of_week > 5:
            raise ValueError(
                f"無効な曜日: {day_of_week}。平日（1-5: 月-金）のみ対応しています。"
            )

        if not self.models:
            raise ValueError("モデルが読み込まれていません。")

        try:
            # 特徴量作成
            features = self._create_prediction_features(day_of_week)
            X = np.array([features])

            predictions = {}

            # 密度率予測
            if "density" in self.models:
                density_pred = self.models["density"].predict(X)[0]
                # 0-100%の範囲に制限
                density_pred = max(0.0, min(100.0, density_pred))
                predictions["density_rate"] = round(density_pred, 2)

            # 占有座席数予測
            if "seats" in self.models:
                seats_pred = self.models["seats"].predict(X)[0]
                # 0-8席の範囲に制限
                seats_pred = max(0, min(8, int(round(seats_pred))))
                predictions["occupied_seats"] = seats_pred

            # 曜日名を追加
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
            predictions["day_name"] = weekday_names[day_of_week - 1]
            predictions["day_of_week"] = day_of_week

            return predictions

        except Exception as e:
            logger.error(f"予測エラー: {str(e)}")
            raise

    def _create_prediction_features(self, day_of_week: int) -> list:
        """
        予測用の特徴量を作成（軽量版）

        Args:
            day_of_week: 曜日（1-5）

        Returns:
            list: 特徴量リスト
        """
        # 基本特徴量
        features = [day_of_week]  # day_of_week

        # density_seats_ratio（固定値を使用）
        features.append(12.5)  # 平均値の近似

        # 曜日ダミー変数
        features.append(1 if day_of_week == 1 else 0)  # is_monday
        features.append(1 if day_of_week == 2 else 0)  # is_tuesday
        features.append(1 if day_of_week == 3 else 0)  # is_wednesday
        features.append(1 if day_of_week == 4 else 0)  # is_thursday
        features.append(1 if day_of_week == 5 else 0)  # is_friday

        # 週の分類
        features.append(1 if day_of_week in [1, 2] else 0)  # is_early_week
        features.append(1 if day_of_week == 3 else 0)  # is_mid_week
        features.append(1 if day_of_week in [4, 5] else 0)  # is_late_week

        return features

    def load_models(self) -> bool:
        """
        保存済みモデルを読み込み

        Returns:
            bool: 読み込み成功可否
        """
        try:
            # モデル読み込み
            for target in ["density", "seats"]:
                model_path = os.path.join(self.model_dir, f"{target}_model.joblib")
                if os.path.exists(model_path):
                    self.models[target] = joblib.load(model_path)
                else:
                    logger.warning(f"モデルファイルが見つかりません: {model_path}")
                    return False

            # モデル性能情報を読み込み
            performance_path = os.path.join(self.model_dir, "model_performance.joblib")
            if os.path.exists(performance_path):
                self.model_performance = joblib.load(performance_path)

            logger.info("モデルの読み込みが完了しました")
            return True

        except Exception as e:
            logger.error(f"モデル読み込みエラー: {e}")
            return False

    def get_model_info(self) -> Dict:
        """
        モデル情報を取得

        Returns:
            Dict: モデル情報
        """
        return {
            "available_models": list(self.models.keys()),
            "model_performance": self.model_performance,
            "model_type": "random_forest",
            "feature_count": len(self.feature_names),
            "weekdays_only": True,
            "prediction_range": {
                "density_rate": {"min": 0.0, "max": 100.0, "unit": "%"},
                "occupied_seats": {"min": 0, "max": 8, "unit": "席"},
            },
        }
