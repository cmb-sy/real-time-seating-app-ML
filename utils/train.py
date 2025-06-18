"""
アンサンブル機械学習モデル構築
"""
import sys
sys.path.append('utils')

import logging
import argparse
import json
import numpy as np
from models import MLPredictor
from data_processor import MLDataProcessor
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ml_training.log')
    ]
)
logger = logging.getLogger(__name__)

def json_serializable(obj):
    """JSON互換形式に変換するヘルパー関数"""
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_serializable(i) for i in obj]
    elif isinstance(obj, tuple):
        return [json_serializable(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        try:
            return str(obj)
        except:
            return None

def run_ml_pipeline(n_trials: int = 200, target_type: str = 'both'):
    """
    機械学習パイプライン実行
   
    Args:
        n_trials: Optunaの最適化試行回数
        target_type: 最適化対象 ('density', 'seats', 'both')
    """

    logger.info("=== アンサンブル機械学習パイプライン開始 ===")
    
    # 1. データ準備確認
    logger.info("1. データ準備確認を実行中...")
    data_processor = MLDataProcessor()
    
    try:
        # データ読み込み確認
        data_processor.load_data_from_supabase()
        logger.info("✅ Supabaseからのデータ取得が正常に完了しました")
        
        # データの基本統計情報をログ出力
        data_info = data_processor.get_data_info()
        logger.info(f"データサイズ: {data_info.get('shape', 'N/A')}")
        logger.info(f"特徴量数: {len(data_info.get('features', []))}")
        
    except Exception as e:
        logger.error(f"❌ データ準備エラー: {e}")
        return False
    
    # 2. アンサンブル機械学習モデル訓練
    logger.info("2. アンサンブル機械学習モデル訓練を実行中...")
    predictor = MLPredictor()
    
    try:
        logger.info(f"高精度ハイパーパラメータ最適化開始 (試行回数: {n_trials})")
        logger.info("TPEサンプラーとMedianPrunerを使用した高速最適化")
        
        # ハイパーパラメータ最適化
        optimization_results = predictor.optimize_hyperparameters(
            target_type=target_type,
            n_trials=n_trials,
        )
        
        # 最適化結果表示
        if 'density' in optimization_results:
            result = optimization_results['density']
            logger.info(f"✅ 密度率予測 - Best RMSE: {result['best_score']:.4f}")
            logger.info(f"  - Best Model: {result['best_params']['model_type']}")
            logger.info(f"  - Best Trial: {result['best_trial']}/{result['n_trials']}")
        
        if 'seats' in optimization_results:
            result = optimization_results['seats']
            logger.info(f"✅ 座席数予測 - Best RMSE: {result['best_score']:.4f}")
            logger.info(f"  - Best Model: {result['best_params']['model_type']}")
            logger.info(f"  - Best Trial: {result['best_trial']}/{result['n_trials']}")
        
        # アンサンブルモデル訓練
        logger.info("3. アンサンブルモデル訓練中...")
        logger.info("各ターゲットに対してVotingRegressorを使用した複数モデル統合")
        
        training_results = predictor.train_best_models()
        
        # 訓練結果表示
        if 'density' in training_results:
            result = training_results['density']
            if 'error' not in result:
                logger.info(f"✅ 密度率予測アンサンブルモデル")
                logger.info(f"  - Test RMSE: {result['test_rmse']:.4f}")
                logger.info(f"  - Test R²: {result['test_r2']:.4f}")
                logger.info(f"  - CV RMSE: {result['cv_rmse']:.4f} ± {result['cv_std']:.4f}")
                logger.info(f"  - 過学習検出: {'⚠️ あり' if result['overfitting_detected'] else '✅ なし'}")
            else:
                logger.error(f"❌ 密度率予測モデル訓練エラー: {result['error']}")
        
        if 'seats' in training_results:
            result = training_results['seats']
            if 'error' not in result:
                logger.info(f"✅ 占有座席数予測アンサンブルモデル")
                logger.info(f"  - Test RMSE: {result['test_rmse']:.4f}")
                logger.info(f"  - Test R²: {result['test_r2']:.4f}")
                logger.info(f"  - CV RMSE: {result['cv_rmse']:.4f} ± {result['cv_std']:.4f}")
                logger.info(f"  - 過学習検出: {'⚠️ あり' if result['overfitting_detected'] else '✅ なし'}")
            else:
                logger.error(f"❌ 占有座席数予測モデル訓練エラー: {result['error']}")
        
        # モデル保存
        logger.info("4. アンサンブルモデル保存中...")
        saved_files = predictor.save_models()
        logger.info(f"✅ モデル保存完了: {len(saved_files)} ファイル")
        for name, path in saved_files.items():
            logger.info(f"  - {name}: {path}")
        
        # 性能サマリー出力
        logger.info("=== 訓練完了サマリー ===")
        for target, result in training_results.items():
            if 'error' not in result:
                improvement = "高精度" if result['test_r2'] > 0.8 else "中精度" if result['test_r2'] > 0.6 else "要改良"
                logger.info(f"{target}: {improvement} (R² = {result['test_r2']:.3f})")
        
    except Exception as e:
        logger.error(f"❌ 機械学習パイプラインエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("=== 高精度アンサンブル機械学習パイプライン完了 ===")
    return True

def export_enhanced_model_info():
    """
    アンサンブル機械学習モデルの詳細情報をJSONとして出力
    """
    logger.info("=== アンサンブルモデル情報をJSONとして出力 ===")
    
    try:
        # データ情報を取得
        data_processor = MLDataProcessor()
        data_processor.load_data_from_supabase()
        data_info = data_processor.get_data_info()
        
        # モデル情報を取得
        predictor = MLPredictor()
        if not predictor.load_models():
            logger.error("❌ 保存済みアンサンブルモデルが見つかりません。")
            return False
        
        model_info = predictor.get_model_info()
        
        # 詳細な出力用のJSONオブジェクト作成
        output_info = {
            "system_info": {
                "model_type": "ensemble_learning",
                "optimization_method": "TPE_sampling_with_pruning",
                "cross_validation": "10_fold_stratified",
                "ensemble_strategy": "voting_regressor"
            },
            "data_summary": {
                "shape": data_info.get("shape", {}),
                "columns": data_info.get("columns", []),
                "features": data_info.get("features", []),
                "targets": data_info.get("targets", []),
                "categorical_features": data_info.get("categorical_features", []),
                "numeric_features": data_info.get("numeric_features", []),
                "stats": data_info.get("stats", {}),
                "weekday_distribution": data_info.get("weekday_stats", {})
            },
            "model_architecture": {
                "available_models": model_info.get("available_models", []),
                "best_parameters": model_info.get("best_parameters", {}),
                "ensemble_components": model_info.get("usage_info", {}).get("ensemble_components", []),
                "feature_names": model_info.get("feature_names", [])
            },
            "performance_metrics": {
                "model_performance": model_info.get("model_performance", {}),
                "prediction_ranges": model_info.get("usage_info", {}).get("prediction_range", {})
            },
            "deployment_info": {
                "model_files": ["density_model.joblib", "seats_model.joblib"],
                "prediction_api": "prediction.py",
                "update_frequency": "daily_recommended",
                "performance_monitoring": "cross_validation_based"
            }
        }
        
        # JSON互換形式に変換
        serializable_info = json_serializable(output_info)
        
        # API下に出力するためのパス設定
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        api_dir = os.path.join(project_root, 'api')
        
        # apiディレクトリが存在しない場合は作成
        os.makedirs(api_dir, exist_ok=True)
        
        # JSONファイルとして出力（api下に配置）
        output_file = os.path.join(api_dir, 'model_info.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ アンサンブルモデル情報を{output_file}に保存しました")
        
        # 簡易サマリーをコンソールに表示
        print("\n=== アンサンブルモデル情報サマリー ===")
        print(f"モデルタイプ: {serializable_info['system_info']['model_type']}")
        print(f"利用可能モデル: {', '.join(serializable_info['model_architecture']['available_models'])}")
        print(f"アンサンブル構成: {', '.join(serializable_info['model_architecture']['ensemble_components'])}")
        print(f"特徴量数: {len(serializable_info['model_architecture']['feature_names'])}")
        print(f"出力先: {output_file}")
        
        performance = serializable_info['performance_metrics']['model_performance']
        for target, metrics in performance.items():
            if 'test_r2' in metrics:
                print(f"{target}予測 R²: {metrics['test_r2']:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ モデル情報の出力中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='高精度アンサンブル機械学習モデル訓練スクリプト')
    parser.add_argument('--mode', choices=['train', 'export'], default='train',
                       help='実行モード (train: 訓練, export: モデル情報をJSON出力)')
    parser.add_argument('--n-trials', type=int, default=200,
                       help='Optunaの最適化試行回数 (デフォルト: 200)')
    parser.add_argument('--target', choices=['density', 'seats', 'both'], default='both',
                       help='最適化対象 (デフォルト: both)')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        success = run_ml_pipeline(
            n_trials=args.n_trials, 
            target_type=args.target
        )
        if success:
            logger.info("🎉 アンサンブル機械学習パイプラインが正常に完了しました")
        else:
            logger.error("💥 アンサンブル機械学習パイプラインでエラーが発生しました")    
    elif args.mode == 'export':
        success = export_enhanced_model_info()
        if success:
            logger.info("🎉 アンサンブルモデル情報のJSON出力が完了しました")
        else:
            logger.error("💥 アンサンブルモデル情報のJSON出力でエラーが発生しました")

if __name__ == "__main__":
    main() 