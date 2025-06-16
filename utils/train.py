"""
機械学習モデル構築スクリプト
"""
import sys
sys.path.append('utils') #先に呼ばないとダメ

import logging
import argparse
from models import MLPredictor
from data_processor import MLDataProcessor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_full_ml_pipeline(n_trials: int = 100, target_type: str = 'both'):
    """
    機械学習パイプライン全体を実行（特徴量エンジニアリング常に有効）
    
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
            use_feature_engineering=True  # 常に有効
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
        training_results = predictor.train_best_models(use_feature_engineering=True)  # 常に有効
        
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

def show_model_info():
    """
    モデル情報を表示
    """
    logger.info("=== モデル情報表示 ===")
    
    predictor = MLPredictor()
    
    if not predictor.load_models():
        logger.error("保存済みモデルが見つかりません。")
        return False
    
    model_info = predictor.get_model_info()
    
    logger.info(f"利用可能なモデル: {model_info['available_models']}")
    
    if model_info['best_parameters']:
        logger.info("\n--- 最適パラメータ ---")
        for target, params in model_info['best_parameters'].items():
            logger.info(f"{target}: {params}")
    
    if model_info['model_performance']:
        logger.info("\n--- モデル性能 ---")
        for target, performance in model_info['model_performance'].items():
            logger.info(f"{target}:")
            for metric, value in performance.items():
                logger.info(f"  {metric}: {value}")
    
    logger.info("=== モデル情報表示完了 ===")
    return True

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description='機械学習モデル訓練スクリプト')
    parser.add_argument('--mode', choices=['train', 'test', 'info'], default='train',
                       help='実行モード (train: 訓練, test: 予測テスト, info: モデル情報表示)')
    parser.add_argument('--n-trials', type=int, default=50,
                       help='Optunaの最適化試行回数 (デフォルト: 50)')
    parser.add_argument('--target', choices=['density', 'seats', 'both'], default='both',
                       help='最適化対象 (デフォルト: both)')
    
    args = parser.parse_args()
    print("assssssssss",args)
    
    if args.mode == 'train':
        success = run_full_ml_pipeline(
            n_trials=args.n_trials, 
            target_type=args.target
        )
        if success:
            logger.info("✅ 機械学習パイプラインが正常に完了しました")
        else:
            logger.error("❌ 機械学習パイプラインでエラーが発生しました")    
    elif args.mode == 'info':
        success = show_model_info()
        if success:
            logger.info("✅ モデル情報の表示が完了しました")
        else:
            logger.error("❌ モデル情報の表示でエラーが発生しました")

if __name__ == "__main__":
    main() 