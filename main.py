"""
FastAPI アプリケーション
リアルタイム座席アプリのML用API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import traceback
import logging
from database import supabase_client
from data_analysis import DataAnalyzer
from ml_models import MLPredictor
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Real-time Seating App ML API",
    description="リアルタイム座席アプリのML用API",
    version="1.0.0"
)

# グローバルインスタンス
data_analyzer = DataAnalyzer()
ml_predictor = MLPredictor()

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("アプリケーションを起動中...")
    
    # 保存済みモデルがあれば読み込み
    if ml_predictor.load_models():
        logger.info("保存済みモデルを読み込みました")
    else:
        logger.info("保存済みモデルが見つかりません")

@app.get("/")
async def root():
    """
    ルートエンドポイント
    APIの動作確認用
    """
    return {"message": "Real-time Seating App ML API is running!"}

@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    API及びデータベース接続の確認
    """
    try:
        # Supabase接続テスト
        response = supabase_client.table("density_history").select("*").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "models_loaded": len(ml_predictor.models) > 0,
            "available_models": list(ml_predictor.models.keys()),
            "message": "APIとデータベースが正常に動作しています"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/density_history")
async def get_all_density_history():
    """
    density_historyテーブルから全てのデータを取得
    
    Returns:
        Dict[str, Any]: density_historyテーブルの全レコード
    
    Raises:
        HTTPException: データベースエラーが発生した場合
    """
    try:
        logger.info("density_history全データ取得を開始")
        
        # Supabaseからdensity_historyテーブルの全データを取得
        response = supabase_client.table("density_history").select("*").execute()
        
        # レスポンスデータを取得
        data = response.data
        
        logger.info(f"データ取得成功: {len(data)}件")
        
        result = {
            "success": True,
            "count": len(data),
            "data": data,
            "message": f"density_historyテーブルから {len(data)} 件のデータを取得しました"
        }
        
        return result
        
    except Exception as e:
        # エラーハンドリング
        logger.error(f"データ取得エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "データベースエラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/density_history/recent/{limit}")
async def get_recent_density_history(limit: int = 10):
    """
    density_historyテーブルから最新のデータを指定件数取得
    
    Args:
        limit (int): 取得する件数（デフォルト: 10）
    
    Returns:
        Dict[str, Any]: 最新のdensity_historyレコード
    """
    try:
        # 最新のデータを取得（created_atで降順ソート）
        response = supabase_client.table("density_history").select("*").order("created_at", desc=True).limit(limit).execute()
        
        data = response.data
        
        return {
            "success": True,
            "count": len(data),
            "limit": limit,
            "data": data,
            "message": f"最新 {len(data)} 件のデータを取得しました"
        }
        
    except Exception as e:
        logger.error(f"最新データ取得エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "データベースエラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/density_history/count")
async def get_density_history_count():
    """
    density_historyテーブルの総レコード数を取得
    
    Returns:
        Dict[str, Any]: テーブルのレコード数情報
    """
    try:
        # テーブルの総件数を取得
        response = supabase_client.table("density_history").select("*", count="exact").execute()
        
        return {
            "success": True,
            "count": response.count,
            "message": f"density_historyテーブルには {response.count} 件のレコードがあります"
        }
        
    except Exception as e:
        logger.error(f"カウント取得エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "データベースエラーが発生しました",
                "message": str(e)
            }
        )

# === データ分析エンドポイント ===

@app.get("/analysis/basic_statistics")
async def get_basic_statistics():
    """
    基本統計情報を取得
    
    Returns:
        Dict[str, Any]: 基本統計情報
    """
    try:
        stats = data_analyzer.get_basic_statistics()
        return {
            "success": True,
            "data": stats,
            "message": "基本統計情報を取得しました"
        }
    except Exception as e:
        logger.error(f"基本統計取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "統計情報取得エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/analysis/weekday_analysis")
async def get_weekday_analysis():
    """
    曜日別分析結果を取得
    
    Returns:
        Dict[str, Any]: 曜日別分析結果
    """
    try:
        weekday_stats = data_analyzer.analyze_by_weekday()
        weekday_summary = data_analyzer.get_weekday_summary()
        
        return {
            "success": True,
            "data": {
                "detailed_stats": weekday_stats,
                "summary": weekday_summary
            },
            "message": "曜日別分析を実行しました"
        }
    except Exception as e:
        logger.error(f"曜日別分析エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "曜日別分析エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/analysis/correlation")
async def get_correlation_analysis():
    """
    相関分析結果を取得
    
    Returns:
        Dict[str, Any]: 相関分析結果
    """
    try:
        correlation_analysis = data_analyzer.get_correlation_analysis()
        
        return {
            "success": True,
            "data": correlation_analysis,
            "message": "相関分析を実行しました"
        }
    except Exception as e:
        logger.error(f"相関分析エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "相関分析エラーが発生しました",
                "message": str(e)
            }
        )

@app.post("/analysis/create_visualizations")
async def create_visualizations():
    """
    可視化グラフを作成
    
    Returns:
        Dict[str, Any]: 作成されたグラフのパス
    """
    try:
        plot_paths = data_analyzer.create_visualizations()
        
        return {
            "success": True,
            "data": plot_paths,
            "message": "可視化グラフを作成しました"
        }
    except Exception as e:
        logger.error(f"可視化作成エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "可視化作成エラーが発生しました",
                "message": str(e)
            }
        )

# === 機械学習エンドポイント ===

@app.post("/ml/optimize_hyperparameters")
async def optimize_hyperparameters(
    background_tasks: BackgroundTasks,
    target_type: str = "both",
    n_trials: int = 50
):
    """
    ハイパーパラメータ最適化を実行
    
    Args:
        target_type: 最適化対象 ('density', 'seats', 'both')
        n_trials: 最適化試行回数
    
    Returns:
        Dict[str, Any]: 最適化結果
    """
    try:
        if target_type not in ['density', 'seats', 'both']:
            raise ValueError("target_typeは 'density', 'seats', 'both' のいずれかを指定してください")
        
        logger.info(f"ハイパーパラメータ最適化開始: target_type={target_type}, n_trials={n_trials}")
        
        # 最適化実行
        optimization_results = ml_predictor.optimize_hyperparameters(
            target_type=target_type, 
            n_trials=n_trials
        )
        
        return {
            "success": True,
            "data": optimization_results,
            "message": f"ハイパーパラメータ最適化が完了しました（{n_trials}回試行）"
        }
    except Exception as e:
        logger.error(f"ハイパーパラメータ最適化エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "ハイパーパラメータ最適化エラーが発生しました",
                "message": str(e)
            }
        )

@app.post("/ml/train_models")
async def train_models():
    """
    最適パラメータでモデルを訓練
    
    Returns:
        Dict[str, Any]: 訓練結果と性能評価
    """
    try:
        if not ml_predictor.best_params:
            raise ValueError("ハイパーパラメータ最適化が実行されていません。先に/ml/optimize_hyperparametersを実行してください。")
        
        logger.info("最適パラメータでモデル訓練開始")
        
        # モデル訓練
        training_results = ml_predictor.train_best_models()
        
        # モデル保存
        saved_files = ml_predictor.save_models()
        
        return {
            "success": True,
            "data": {
                "model_performance": training_results,
                "saved_files": saved_files
            },
            "message": "モデル訓練が完了し、保存されました"
        }
    except Exception as e:
        logger.error(f"モデル訓練エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "モデル訓練エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/ml/predict")
async def predict_values(day_of_week: int, hour: int):
    """
    曜日と時間から密度率と占有座席数を予測
    
    Args:
        day_of_week: 曜日（0-4: 月-金）
        hour: 時間（0-23）
    
    Returns:
        Dict[str, Any]: 予測結果
    """
    try:
        # 入力検証
        if day_of_week < 0 or day_of_week > 4:
            raise ValueError("day_of_weekは0-4（月-金）の範囲で指定してください")
        
        if hour < 0 or hour > 23:
            raise ValueError("hourは0-23の範囲で指定してください")
        
        # 予測実行
        predictions = ml_predictor.predict(day_of_week, hour)
        
        # 曜日名を追加
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
        
        return {
            "success": True,
            "data": {
                "input": {
                    "day_of_week": day_of_week,
                    "weekday_name": weekday_names[day_of_week],
                    "hour": hour
                },
                "predictions": predictions
            },
            "message": f"{weekday_names[day_of_week]} {hour}時の予測を実行しました"
        }
    except Exception as e:
        logger.error(f"予測エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "予測エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/ml/model_info")
async def get_model_info():
    """
    モデル情報を取得
    
    Returns:
        Dict[str, Any]: モデル情報
    """
    try:
        model_info = ml_predictor.get_model_info()
        
        return {
            "success": True,
            "data": model_info,
            "message": "モデル情報を取得しました"
        }
    except Exception as e:
        logger.error(f"モデル情報取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "モデル情報取得エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/ml/predict_day_schedule")
async def predict_day_schedule(day_of_week: int):
    """
    指定曜日の1日の予測スケジュールを取得
    
    Args:
        day_of_week: 曜日（0-4: 月-金）
    
    Returns:
        Dict[str, Any]: 1日の予測スケジュール
    """
    try:
        if day_of_week < 0 or day_of_week > 4:
            raise ValueError("day_of_weekは0-4（月-金）の範囲で指定してください")
        
        # 1時間ごとの予測を実行
        schedule = []
        for hour in range(24):
            predictions = ml_predictor.predict(day_of_week, hour)
            schedule.append({
                "hour": hour,
                "time": f"{hour:02d}:00",
                "predictions": predictions
            })
        
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
        
        return {
            "success": True,
            "data": {
                "day_of_week": day_of_week,
                "weekday_name": weekday_names[day_of_week],
                "schedule": schedule
            },
            "message": f"{weekday_names[day_of_week]}の1日予測スケジュールを作成しました"
        }
    except Exception as e:
        logger.error(f"スケジュール予測エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "スケジュール予測エラーが発生しました",
                "message": str(e)
            }
        )

@app.post("/generate_frontend_data")
async def generate_frontend_data():
    """
    フロントエンド向けの包括的なデータを生成
    
    Returns:
        Dict[str, Any]: 分析結果、予測データ、可視化データの包括的な結果
    """
    try:
        logger.info("フロントエンド向けデータ生成開始")
        
        # 1. データ分析を実行
        analyzer = DataAnalyzer()
        
        # 基本統計情報
        basic_stats = analyzer.get_basic_statistics()
        logger.info("基本統計情報生成完了")
        
        # 曜日別分析
        weekday_analysis = analyzer.analyze_by_weekday()
        logger.info("曜日別分析完了")
        
        # 相関分析
        correlation_analysis = analyzer.get_correlation_analysis()
        logger.info("相関分析完了")
        
        # 可視化グラフ生成
        visualization_paths = analyzer.create_visualizations()
        logger.info("可視化グラフ生成完了")
        
        # 2. 機械学習予測データ生成
        if ml_predictor is None:
            return {
                "success": False,
                "error": "モデルが訓練されていません",
                "message": "先にtrain_best_models()を実行してください。"
            }
        
        # 各曜日の24時間予測データ生成
        prediction_schedules = {}
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
        
        for day in range(0, 5):
            schedule = []
            for hour in range(24):
                predictions = ml_predictor.predict(day_of_week=day, hour=hour)
                schedule.append({
                    "hour": hour,
                    "time": f"{hour:02d}:00",
                    "predictions": predictions
                })
            
            prediction_schedules[weekday_names[day]] = {
                "day_of_week": day,
                "weekday_name": weekday_names[day],
                "schedule": schedule
            }
        
        logger.info("予測スケジュール生成完了")
        
        # 3. サマリー統計生成
        # DataAnalyzerからの曜日サマリーを取得
        daily_summary = analyzer.get_weekday_summary()
        
        # 各曜日の予測平均値も追加
        for day in range(0, 5):
            day_predictions = [item["predictions"] for item in prediction_schedules[weekday_names[day]]["schedule"]]
            avg_density = sum(p["density_rate"] for p in day_predictions) / len(day_predictions)
            avg_seats = sum(p["occupied_seats"] for p in day_predictions) / len(day_predictions)
            
            if weekday_names[day] not in daily_summary:
                daily_summary[weekday_names[day]] = {}
                
            daily_summary[weekday_names[day]].update({
                "day_of_week": day,
                "predicted_average_density_rate": round(avg_density, 2),
                "predicted_average_occupied_seats": round(avg_seats, 1),
                "peak_hour_prediction": max(day_predictions, key=lambda x: x["density_rate"]),
                "low_hour_prediction": min(day_predictions, key=lambda x: x["density_rate"])
            })
        
        # 4. 包括的なレスポンス作成
        frontend_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_period": "2週間",
                "total_records": len(analyzer.df) if hasattr(analyzer, 'df') else 0,
                "weekday_records": len(analyzer.df_weekdays) if hasattr(analyzer, 'df_weekdays') else 0
            },
            "analysis": {
                "basic_statistics": basic_stats,
                "weekday_analysis": weekday_analysis,
                "correlation_analysis": correlation_analysis,
                "daily_summary": daily_summary
            },
            "predictions": {
                "schedules": prediction_schedules,
                "model_performance": {
                    "density_model": ml_predictor.model_performance.get("density", {}) if hasattr(ml_predictor, 'model_performance') else {},
                    "seats_model": ml_predictor.model_performance.get("seats", {}) if hasattr(ml_predictor, 'model_performance') else {}
                }
            },
            "visualizations": {
                "file_paths": visualization_paths,
                "available": True if visualization_paths else False
            }
        }
        
        # 5. JSONファイルとして保存
        import os
        os.makedirs("frontend_data", exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 最新データファイル（フロントエンドが読み込む用）
        latest_file = "frontend_data/latest_data.json"
        
        # アーカイブファイル（履歴保存用）
        archive_file = f"frontend_data/data_{timestamp}.json"
        
        import json
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, ensure_ascii=False, indent=2)
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"フロントエンド向けデータを保存: {latest_file}, {archive_file}")
        
        return {
            "success": True,
            "data": frontend_data,
            "files": {
                "latest": latest_file,
                "archive": archive_file
            },
            "message": "フロントエンド向けデータ生成が完了しました"
        }
        
    except Exception as e:
        logger.error(f"フロントエンド向けデータ生成エラー: {str(e)}")
        return {
            "success": False,
            "error": "フロントエンド向けデータ生成でエラーが発生しました",
            "message": str(e)
        }

@app.get("/frontend_data/latest")
async def get_latest_frontend_data():
    """
    フロントエンド向けの最新データを取得
    
    Returns:
        Dict[str, Any]: 最新の分析・予測データ
    """
    try:
        import json
        import os
        
        latest_file = "frontend_data/latest_data.json"
        
        if not os.path.exists(latest_file):
            return {
                "success": False,
                "error": "最新データが見つかりません",
                "message": "先にgenerate_frontend_data()を実行してください。"
            }
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "data": data,
            "message": "最新のフロントエンド向けデータを取得しました"
        }
        
    except Exception as e:
        logger.error(f"最新データ取得エラー: {str(e)}")
        return {
            "success": False,
            "error": "最新データ取得でエラーが発生しました",
            "message": str(e)
        }
