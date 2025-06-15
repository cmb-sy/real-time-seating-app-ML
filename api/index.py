"""
Vercel用統合API - 単一ファイルで全機能を提供
依存関係を最小限に抑えたスタンドアロン版
"""
import os
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

# 環境変数の取得
NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_ml_prediction(day_of_week):
    """機械学習予測（フォールバック版）"""
    try:
        # 土日は0を返す
        if day_of_week >= 5:
            return {"occupancy_rate": 0.0, "occupied_seats": 0}
        
        # 簡易的な予測値（モデルファイルが読み込めない場合のフォールバック）
        # 曜日別の平均的な値を使用
        weekday_averages = {
            0: {"occupancy_rate": 0.65, "occupied_seats": 5},  # 月曜日
            1: {"occupancy_rate": 0.75, "occupied_seats": 6},  # 火曜日
            2: {"occupancy_rate": 0.70, "occupied_seats": 6},  # 水曜日
            3: {"occupancy_rate": 0.80, "occupied_seats": 6},  # 木曜日
            4: {"occupancy_rate": 0.60, "occupied_seats": 5},  # 金曜日
        }
        
        # まずフォールバック値を取得
        fallback_prediction = weekday_averages.get(day_of_week, {"occupancy_rate": 0.5, "occupied_seats": 4})
        
        try:
            # 機械学習ライブラリの動的インポート
            import joblib
            import numpy as np
            
            # モデルファイルの読み込みを試行
            density_model = joblib.load('density_model.joblib')
            seats_model = joblib.load('seats_model.joblib')
            
            # 10個の特徴量を作成
            features = np.zeros((1, 10))
            features[0, 0] = day_of_week
            features[0, 1] = 0.1  # density_seats_ratio
            if day_of_week < 5:  # 平日のみ
                features[0, 2 + day_of_week] = 1  # 曜日ダミー変数
            features[0, 7] = 1 if day_of_week in [0, 1] else 0  # is_early_week
            features[0, 8] = 1 if day_of_week == 2 else 0       # is_mid_week
            features[0, 9] = 1 if day_of_week in [3, 4] else 0  # is_late_week
            
            # 予測実行
            density_pred = density_model.predict(features)[0]
            seats_pred = seats_model.predict(features)[0]
            
            return {
                "occupancy_rate": max(0.0, min(1.0, density_pred / 100.0 if density_pred > 1 else density_pred)),
                "occupied_seats": max(0, min(8, int(round(seats_pred))))
            }
            
        except Exception as model_error:
            # モデルファイルが読み込めない場合はフォールバック値を使用
            print(f"モデル読み込みエラー（フォールバック使用）: {model_error}")
            return fallback_prediction
            
    except Exception as e:
        print(f"予測エラー: {e}")
        return {"occupancy_rate": 0.0, "occupied_seats": 0}

def handle_today_tomorrow():
    """今日・明日の予測"""
    try:
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        today_prediction = get_ml_prediction(today.weekday())
        tomorrow_prediction = get_ml_prediction(tomorrow.weekday())
        
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        
        return {
            "success": True,
            "data": {
                "today": {
                    "weekday": today.weekday(),
                    "weekday_name": weekday_names[today.weekday()],
                    "occupancy_rate": today_prediction["occupancy_rate"],
                    "occupied_seats": today_prediction["occupied_seats"]
                },
                "tomorrow": {
                    "weekday": tomorrow.weekday(),
                    "weekday_name": weekday_names[tomorrow.weekday()],
                    "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                    "occupied_seats": tomorrow_prediction["occupied_seats"]
                }
            }
        }
    except Exception as e:
        return {"success": False, "error": f"今日・明日予測エラー: {str(e)}"}

def handle_weekly_average():
    """週間平均予測"""
    try:
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        weekly_averages = []
        
        for day in range(5):  # 平日のみ
            prediction = get_ml_prediction(day)
            weekly_averages.append({
                "weekday": day,
                "weekday_name": weekday_names[day],
                "occupancy_rate": prediction["occupancy_rate"],
                "occupied_seats": prediction["occupied_seats"]
            })
        
        return {
            "success": True,
            "data": {
                "weekly_averages": weekly_averages
            }
        }
    except Exception as e:
        return {"success": False, "error": f"週間平均予測エラー: {str(e)}"}

def handle_root():
    """ルートパスでのAPI情報表示"""
    return {
        "success": True,
        "message": "リアルタイム座席予測API",
        "version": "1.0.0",
        "endpoints": {
            "today_tomorrow": "/api/predictions/today-tomorrow",
            "weekly_average": "/api/predictions/weekly-average"
        },
        "status": "運用中",
        "environment": "production"
    }

# Vercel用のメインハンドラー関数
def handler(request):
    """Vercel用のメインハンドラー関数"""
    try:
        # リクエストメソッドとURLを取得
        method = getattr(request, 'method', 'GET')
        url = getattr(request, 'url', '/')
        
        # URLからパスを抽出
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # CORS ヘッダーを設定
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin, Accept, X-Requested-With',
            'Access-Control-Max-Age': '86400'
        }
        
        # OPTIONSリクエストの処理（プリフライト）
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # パスに応じてレスポンスを生成
        if path == "/api/predictions/today-tomorrow" or path == "/predictions/today-tomorrow":
            response_data = handle_today_tomorrow()
        elif path == "/api/predictions/weekly-average" or path == "/predictions/weekly-average":
            response_data = handle_weekly_average()
        elif path == "/" or path == "":
            response_data = handle_root()
        else:
            response_data = {
                "success": False, 
                "error": f"エンドポイントが見つかりません: {path}",
                "available_endpoints": [
                    "/api/predictions/today-tomorrow",
                    "/api/predictions/weekly-average"
                ]
            }
        
        # レスポンスヘッダーにCORSとContent-Typeを追加
        response_headers = {
            'Content-Type': 'application/json',
            **cors_headers
        }
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps(response_data, ensure_ascii=False)
        }
        
    except Exception as e:
        # エラー時もCORSヘッダーを設定
        error_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        error_response = {
            "success": False, 
            "error": f"サーバーエラー: {str(e)}",
            "debug_info": {
                "error_type": type(e).__name__,
                "request_method": method,
                "request_url": url,
                "path": path
            }
        }
        
        return {
            'statusCode': 500,
            'headers': error_headers,
            'body': json.dumps(error_response, ensure_ascii=False)
        }

# デフォルトエクスポート（Vercelが自動的に呼び出す）
default = handler 