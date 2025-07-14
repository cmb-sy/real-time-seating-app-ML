#!/usr/bin/env python3

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from supabase_access import get_supabase_data


class MLDataProcessor:
    def __init__(self):
        self.df = None
        self.df_weekdays = None

    def load_data_from_supabase(self) -> pd.DataFrame:
        """
        Returns:
            pd.DataFrame: 取得したデータ
        """
        try:
            data = get_supabase_data()
            self.df = pd.DataFrame(data)

            if self.df.empty:
                raise ValueError("Supabaseからデータを取得できませんでした")

            # created_atをdatetime型に変換（ISO8601形式に対応）
            self.df["created_at"] = pd.to_datetime(
                self.df["created_at"], format="ISO8601"
            )

            # DBの曜日形式に変換（月曜日=1, 金曜日=5）
            self.df["day_of_week"] = self.df["created_at"].dt.weekday + 1

            # 平日データのみフィルタリング（月-金: 1-5）
            self.df_weekdays = self.df[
                self.df["day_of_week"].isin([1, 2, 3, 4, 5])
            ].copy()

            print(
                f"平日データ{len(self.df_weekdays)}件を読み込みました（全{len(self.df)}件中）"
            )
            return self.df_weekdays

        except Exception as e:
            print(f"Supabaseデータ取得エラー: {str(e)}")
            raise

    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量エンジニアリング（曜日情報と統計的特徴量）

        Args:
            df: 元データ

        Returns:
            pd.DataFrame: 特徴量エンジニアリング後のデータ
        """
        feature_df = df.copy()

        # 密度率と座席数の比率特徴量を作成
        feature_df["density_seats_ratio"] = feature_df["density_rate"] / (
            feature_df["occupied_seats"] + 1
        )  # ゼロ除算回避

        # 1. 曜日ダミー変数（DB形式: 1-5）
        feature_df["is_monday"] = (feature_df["day_of_week"] == 1).astype(int)
        feature_df["is_tuesday"] = (feature_df["day_of_week"] == 2).astype(int)
        feature_df["is_wednesday"] = (feature_df["day_of_week"] == 3).astype(int)
        feature_df["is_thursday"] = (feature_df["day_of_week"] == 4).astype(int)
        feature_df["is_friday"] = (feature_df["day_of_week"] == 5).astype(int)

        # 2. 週の分類（月火・水・木金の3グループ、DB形式: 1-5）
        feature_df["is_early_week"] = (feature_df["day_of_week"].isin([1, 2])).astype(
            int
        )  # 月火
        feature_df["is_mid_week"] = (feature_df["day_of_week"] == 3).astype(int)  # 水
        feature_df["is_late_week"] = (feature_df["day_of_week"].isin([4, 5])).astype(
            int
        )  # 木金

        feature_df = feature_df.fillna(0)

        return feature_df

    def prepare_ml_data(
        self,
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
        """
        機械学習用のデータを準備

        Returns:
            Tuple: (元データ, 特徴量X, 密度率y, 占有座席数y)
        """
        if self.df is None:
            self.load_data_from_supabase()

        # 平日データのみ使用
        ml_data = self.df_weekdays.copy()

        # 特徴量エンジニアリングを実行
        ml_data = self.create_advanced_features(ml_data)

        feature_columns = [
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

        # 存在する特徴量のみを選択（エラー回避）
        available_features = [col for col in feature_columns if col in ml_data.columns]
        X = ml_data[available_features].values

        # 特徴量名を保存
        self.feature_names = available_features

        # ターゲット変数
        y_density = ml_data["density_rate"].values
        y_seats = ml_data["occupied_seats"].values

        return ml_data, X, y_density, y_seats


if __name__ == "__main__":

    # データ処理テスト
    processor = MLDataProcessor()

    try:
        # 基本データ準備
        print("=== 基本データ準備テスト ===")
        ml_data, X_basic, y_density, y_seats = processor.prepare_ml_data()
        print(f"基本特徴量: {X_basic.shape}")

        # 特徴量エンジニアリング
        print("\n=== 特徴量エンジニアリングテスト ===")
        ml_data_fe, X_advanced, y_density_fe, y_seats_fe = processor.prepare_ml_data()
        print(f"高度な特徴量: {X_advanced.shape}")

        print("\n✅ データ処理テスト完了")

    except Exception as e:
        print(f"❌ データ処理テストエラー: {e}")
        import traceback

        traceback.print_exc()
