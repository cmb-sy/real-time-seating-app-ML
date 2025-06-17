"""
機械学習モデル構築スクリプト
"""
import sys
sys.path.append('utils') #先に呼ばないとダメ

import logging
import argparse
import json
import numpy as np
from models import MLPredictor
from data_processor import MLDataProcessor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def json_serializable(obj):
    """
    JSON互換形式に変換するヘルパー関数
    
    Args:
        obj: 変換対象のオブジェクト
    
    Returns:
        JSON互換形式のオブジェクト
    """
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

def run_full_ml_pipeline(n_trials: int = 100, target_type: str = 'both'):
    """
    機械学習パイプライン実行
    
    Args:
        n_trials: Optunaの最適化試行回数
        target_type: 最適化対象 ('density', 'seats', 'both')
    """

    logger.info("=== 機械学習パイプライン開始 ===")
    
    # 1. データ準備確認
    logger.info("1. データ準備確認を実行中...")
    data_processor = MLDataProcessor()
    
    try:
        # データ読み込み確認
        data_processor.load_data_from_supabase()
        logger.info("Supabaseからのデータ取得が正常に完了しました")
        
    except Exception as e:
        logger.error(f"データ準備エラー: {e}")
        return False
    
    # 2. 機械学習モデル訓練
    logger.info("2. 機械学習モデル訓練を実行中...")
    predictor = MLPredictor()
    
    try:
        logger.info(f"ハイパーパラメータ最適化開始 (試行回数: {n_trials})")
        optimization_results = predictor.optimize_hyperparameters(
            target_type=target_type,
            n_trials=n_trials,
        )
        
        # 結果表示
        if 'density' in optimization_results:
            logger.info(f"密度率予測 - Best RMSE: {optimization_results['density']['best_score']:.4f}")
            logger.info(f"密度率予測 - Best Model: {optimization_results['density']['best_params']['model_type']}")
        
        if 'seats' in optimization_results:
            logger.info(f"座席数予測 - Best RMSE: {optimization_results['seats']['best_score']:.4f}")
            logger.info(f"座席数予測 - Best Model: {optimization_results['seats']['best_params']['model_type']}")
        
        # 最適パラメータでモデル訓練
        logger.info("最適パラメータでモデル訓練中...")
        training_results = predictor.train_best_models()
        
        # 結果表示
        if 'density' in training_results:
            result = training_results['density']
            logger.info(f"密度率予測モデル - RMSE: {result['test_rmse']:.4f}, R²: {result['test_r2']:.4f}")
        
        if 'seats' in training_results:
            result = training_results['seats']
            logger.info(f"座席数予測モデル - RMSE: {result['test_rmse']:.4f}, R²: {result['test_r2']:.4f}")
        
        # モデル保存
        saved_files = predictor.save_models()
        logger.info(f"モデル保存完了: {len(saved_files)} ファイル")
        
    except Exception as e:
        logger.error(f"機械学習エラー: {e}")
        return False
    
    logger.info("=== 機械学習パイプライン完了 ===")
    return True

def export_model_info():
    """
    機械学習モデルの情報をJSONとして出力
    """
    logger.info("=== モデル情報をJSONとして出力 ===")
    
    try:
        # データ情報を取得
        data_processor = MLDataProcessor()
        data_processor.load_data_from_supabase()
        data_info = data_processor.get_data_info()
        
        # モデル情報を取得
        predictor = MLPredictor()
        if not predictor.load_models():
            logger.error("保存済みモデルが見つかりません。")
            return False
        
        model_info = predictor.get_model_info()
        
        # 出力用のJSONオブジェクト作成
        output_info = {
            "data": {
                "shape": data_info.get("shape", {}),
                "columns": data_info.get("columns", []),
                "features": data_info.get("features", []),
                "targets": data_info.get("targets", []),
                "categorical_features": data_info.get("categorical_features", []),
                "numeric_features": data_info.get("numeric_features", []),
                "stats": data_info.get("stats", {}),
                "weekday_stats": data_info.get("weekday_stats", {})
            },
            "models": {
                "available_models": model_info.get("available_models", []),
                "best_parameters": model_info.get("best_parameters", {}),
                "performance": model_info.get("model_performance", {}),
                "model_details": model_info.get("model_details", {}),
                "feature_names": model_info.get("feature_names", []),
                "usage_info": model_info.get("usage_info", {})
            }
        }
        
        # JSON互換形式に変換
        serializable_info = json_serializable(output_info)
        
        # JSONファイルとして出力
        with open('model_info.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_info, f, ensure_ascii=False, indent=2)
        
        logger.info("モデル情報をmodel_info.jsonに保存しました")
        
        # コンソールにも表示
        print(json.dumps(serializable_info, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        logger.error(f"モデル情報の出力中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='機械学習モデル訓練スクリプト')
    parser.add_argument('--mode', choices=['train', 'export'], default='train',
                       help='実行モード (train: 訓練, export: モデル情報をJSON出力)')
    parser.add_argument('--n-trials', type=int, default=50,
                       help='Optunaの最適化試行回数 (デフォルト: 50)')
    parser.add_argument('--target', choices=['density', 'seats', 'both'], default='both',
                       help='最適化対象 (デフォルト: both)')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        success = run_full_ml_pipeline(
            n_trials=args.n_trials, 
            target_type=args.target
        )
        if success:
            logger.info("✅ 機械学習パイプラインが正常に完了しました")
        else:
            logger.error("❌ 機械学習パイプラインでエラーが発生しました")    
    elif args.mode == 'export':
        success = export_model_info()
        if success:
            logger.info("✅ モデル情報のJSON出力が完了しました")
        else:
            logger.error("❌ モデル情報のJSON出力でエラーが発生しました")

if __name__ == "__main__":
    main() 