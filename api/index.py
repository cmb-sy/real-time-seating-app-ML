"""
Vercel Serverless Function エントリーポイント
簡略化バージョン - Vercelのサイズ制限に対応
"""
import sys
import os
import logging
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Real-time Seating App ML API",
    description="リアルタイム座席アプリのML用API (簡略版)",
    version="1.0.0"
)

# CORS設定
def get_cors_origins():
    """環境変数からCORSオリジンを取得"""
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if cors_origins:
        return cors_origins.split(",")
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://v0-real-time-seating-app.vercel.app",
        "https://real-time-seating-app-ml.vercel.app",
        "*"  # すべてのオリジンを許可（テスト用）
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept", "Accept-Language", "Content-Language", "Content-Type",
        "Authorization", "X-Requested-With", "X-API-Key", "Cache-Control",
        "Pragma", "Origin"
    ],
    expose_headers=["X-Total-Count", "X-Page-Count", "Content-Range"],
    max_age=3600,
)

# 明示的なCORSヘッダー追加ミドルウェア
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Origin"
    return response

@app.get("/")
@app.options("/")
async def root():
    """ルートエンドポイント - APIの動作確認用"""
    return {"message": "Real-time Seating App ML API is running (simplified version)!"}

@app.get("/api")
@app.options("/api")
async def api_root():
    """APIルートエンドポイント"""
    return {"message": "Real-time Seating App ML API is running (simplified version)!"}

# OPTIONSリクエスト対応
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """プレフライトリクエスト(OPTIONS)のためのハンドラー"""
    return {}

# ヘルスチェックエンドポイント（複数のパスで対応）
@app.get("/health")
@app.get("/api/health")
@app.get("/api/health-check")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        return {
            "status": "healthy",
            "database": "simulated",
            "models_loaded": False,
            "available_models": [],
            "environment": "production-lite",
            "message": "簡略化されたAPIが正常に動作しています",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/api/predictions/today-tomorrow")
async def get_today_tomorrow_predictions():
    """今日と明日の予測データを取得 (ダミーデータ)"""
    try:
        # 現在の曜日を取得（0=月曜日）
        today_weekday = datetime.now().weekday()
        tomorrow_weekday = (today_weekday + 1) % 7
        
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜", 5: "土曜", 6: "日曜"}
        
        # サンプルデータ
        sample_predictions = {
            0: {"density_rate": 0.75, "occupied_seats": 45},
            1: {"density_rate": 0.65, "occupied_seats": 39},
            2: {"density_rate": 0.80, "occupied_seats": 48},
            3: {"density_rate": 0.70, "occupied_seats": 42},
            4: {"density_rate": 0.55, "occupied_seats": 33},
        }
        
        # 平日のみ予測可能
        predictions = {}
        
        if today_weekday <= 4:  # 月-金
            predictions["today"] = {
                "day_of_week": today_weekday,
                "weekday_name": weekday_names[today_weekday],
                "predictions": sample_predictions.get(today_weekday, {"density_rate": 0.65, "occupied_seats": 39})
            }
        else:
            predictions["today"] = {
                "day_of_week": today_weekday,
                "weekday_name": weekday_names[today_weekday],
                "predictions": None,
                "message": "土日は予測データがありません"
            }
        
        if tomorrow_weekday <= 4:  # 月-金
            predictions["tomorrow"] = {
                "day_of_week": tomorrow_weekday,
                "weekday_name": weekday_names[tomorrow_weekday],
                "predictions": sample_predictions.get(tomorrow_weekday, {"density_rate": 0.65, "occupied_seats": 39})
            }
        else:
            predictions["tomorrow"] = {
                "day_of_week": tomorrow_weekday,
                "weekday_name": weekday_names[tomorrow_weekday],
                "predictions": None,
                "message": "土日は予測データがありません"
            }
        
        return {
            "success": True,
            "data": predictions,
            "message": "今日と明日の予測データを取得しました (サンプルデータ)"
        }
        
    except Exception as e:
        logger.error(f"今日明日予測エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "今日明日予測エラーが発生しました",
                "message": str(e)
            }
        )

@app.get("/api/predictions/weekly-average")
async def get_weekly_average_predictions():
    """週平均の予測データを取得 (ダミーデータ)"""
    try:
        # サンプルデータ
        weekday_predictions = {
            "月曜": {"day_of_week": 0, "weekday_name": "月曜", "predictions": {"density_rate": 0.75, "occupied_seats": 45}},
            "火曜": {"day_of_week": 1, "weekday_name": "火曜", "predictions": {"density_rate": 0.65, "occupied_seats": 39}},
            "水曜": {"day_of_week": 2, "weekday_name": "水曜", "predictions": {"density_rate": 0.80, "occupied_seats": 48}},
            "木曜": {"day_of_week": 3, "weekday_name": "木曜", "predictions": {"density_rate": 0.70, "occupied_seats": 42}},
            "金曜": {"day_of_week": 4, "weekday_name": "金曜", "predictions": {"density_rate": 0.55, "occupied_seats": 33}}
        }
        
        # 週平均
        weekly_average = {
            "average_density_rate": 0.69,
            "average_occupied_seats": 41.4,
            "total_weekdays": 5
        }
        
        return {
            "success": True,
            "data": {
                "weekly_average": weekly_average,
                "daily_predictions": weekday_predictions
            },
            "message": "週平均予測データを取得しました (サンプルデータ)"
        }
        
    except Exception as e:
        logger.error(f"週平均予測エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "週平均予測エラーが発生しました",
                "message": str(e)
            }
        )

# Vercel Serverless Functions 用のハンドラー
handler = app 