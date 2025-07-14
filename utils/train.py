#!/usr/bin/env python3
"""
機械学習モデル訓練スクリプト
"""

import sys
import os
import json

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
utils_dir = current_dir

for path in [utils_dir, current_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from models import MLTrainer


def train_models():
    """
    Supabaseからデータを取得し、データ加工後にモデルを学習・保存する
    """
    try:
        print("🚀 機械学習モデルの訓練を開始します...")

        # MLTrainerでモデル学習（データ取得・加工も自動実行）
        ml_trainer = MLTrainer()
        print("🤖 モデルの学習を開始...")
        training_results = ml_trainer.train_models()

        # トレーニング結果の表示
        print("\n📈 学習結果:")
        for target, result in training_results.items():
            if "error" in result:
                print(f"❌ {target}モデル: エラー - {result['error']}")
            else:
                print(f"✅ {target}モデル:")
                print(f"  - RMSE: {result['test_rmse']:.4f}")
                print(f"  - MAE: {result['test_mae']:.4f}")
                print(f"  - R²: {result['test_r2']:.4f}")
                print(f"  - CV RMSE: {result['cv_rmse']:.4f}")
                print(f"  - データサイズ: {result['data_size']}")
                print(f"  - 特徴量数: {result['feature_count']}")

        # モデル保存
        print("\n💾 モデルを保存中...")
        saved_files = ml_trainer.save_models()
        for name, path in saved_files.items():
            print(f"  - {name}: {path}")

        # 結果をJSON形式で保存
        output_file = "training_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(training_results, f, ensure_ascii=False, indent=2)
        print(f"📄 学習結果を保存: {output_file}")

        print("\n🎉 モデル学習が完了しました！")
        return training_results

    except Exception as e:
        print(f"❌ トレーニングエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    train_models()
