"""
機械学習モデル訓練スクリプト
データ分析からモデル訓練まで一括実行
"""

import logging
import argparse
from src.ml.ml_models import MLPredictor
from src.ml.data_analysis import DataAnalyzer

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_full_ml_pipeline(n_trials: int = 50, target_type: str = 'both'):
    """
    機械学習パイプライン全体を実行
    
    Args:
        n_trials: Optunaの最適化試行回数
        target_type: 最適化対象 ('density', 'seats', 'both')
    """
    logger.info("=== 機械学習パイプライン開始 ===")
    
    # 1. データ分析
    logger.info("1. データ分析を実行中...")
    analyzer = DataAnalyzer()
    
    try:
        # 基本統計
        basic_stats = analyzer.get_basic_statistics()
        logger.info(f"データ件数: {basic_stats['全体統計']['レコード数']} 件")
        logger.info(f"平日データ件数: {basic_stats['平日統計']['レコード数']} 件")
        
        # 曜日別分析
        weekday_analysis = analyzer.analyze_by_weekday()
        logger.info(f"曜日別分析完了: {len(weekday_analysis)} 曜日のデータ")
        
        # 相関分析
        correlation = analyzer.get_correlation_analysis()
        logger.info(f"密度率と占有座席数の相関: {correlation['density_occupied_correlation']:.3f}")
        
        # 可視化
        plot_paths = analyzer.create_visualizations()
        logger.info(f"可視化グラフ作成完了: {len(plot_paths)} 個のグラフ")
        
    except Exception as e:
        logger.error(f"データ分析エラー: {e}")
        return False
    
    # 2. 機械学習モデル訓練
    logger.info("2. 機械学習モデル訓練を実行中...")
    predictor = MLPredictor()
    
    try:
        # ハイパーパラメータ最適化
        logger.info(f"ハイパーパラメータ最適化開始 (試行回数: {n_trials})")
        optimization_results = predictor.optimize_hyperparameters(
            target_type=target_type,
            n_trials=n_trials
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
    
    # 3. 予測テスト
    logger.info("3. 予測テストを実行中...")
    
    try:
        # 各曜日の予測をテスト
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
        
        for day in range(0, 5):
            predictions = predictor.predict(day_of_week=day)
            logger.info(f"{weekday_names[day]}の予測: {predictions}")
        
    except Exception as e:
        logger.error(f"予測テストエラー: {e}")
        return False
    
    logger.info("=== 機械学習パイプライン完了 ===")
    return True

def test_predictions():
    """
    訓練済みモデルで予測テストを実行
    """
    logger.info("=== 予測テスト開始 ===")
    
    predictor = MLPredictor()
    
    # 保存済みモデルを読み込み
    if not predictor.load_models():
        logger.error("保存済みモデルが見つかりません。先にモデルを訓練してください。")
        return False
    
    logger.info("保存済みモデルを読み込みました")
    
    # 各曜日での予測
    weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
    
    for day in range(0, 5):
        logger.info(f"\n--- {weekday_names[day]} ---")
        try:
            predictions = predictor.predict(day_of_week=day)
            density = predictions.get('density_rate', 'N/A')
            seats = predictions.get('occupied_seats', 'N/A')
            logger.info(f"密度率 {density}%, 占有座席数 {seats}")
        except Exception as e:
            logger.error(f"予測エラー: {e}")
    
    logger.info("=== 予測テスト完了 ===")
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
    
    if args.mode == 'train':
        success = run_full_ml_pipeline(n_trials=args.n_trials, target_type=args.target)
        if success:
            logger.info("✅ 機械学習パイプラインが正常に完了しました")
        else:
            logger.error("❌ 機械学習パイプラインでエラーが発生しました")
    
    elif args.mode == 'test':
        success = test_predictions()
        if success:
            logger.info("✅ 予測テストが正常に完了しました")
        else:
            logger.error("❌ 予測テストでエラーが発生しました")
    
    elif args.mode == 'info':
        success = show_model_info()
        if success:
            logger.info("✅ モデル情報の表示が完了しました")
        else:
            logger.error("❌ モデル情報の表示でエラーが発生しました")

if __name__ == "__main__":
    main() 