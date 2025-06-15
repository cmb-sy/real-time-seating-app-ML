"""
今日・明日予測API - Vercel個別エンドポイント
"""
import os
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs

def get_supabase_client():
    """Supabaseクライアントを初期化"""
    try:
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase環境変数が設定されていません")
            return None
        
        from supabase import create_client, Client
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
        
    except Exception as e:
        print(f"❌ Supabaseクライアント初期化エラー: {e}")
        return None

def get_database_prediction(day_of_week):
    """データベースから実際のデータを取得して予測"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("データベース接続失敗")
        
        response = supabase.table('density_history').select('density_rate, occupied_seats').eq('day_of_week', day_of_week).execute()
        data = response.data
        
        if not data or len(data) == 0:
            raise Exception(f"曜日{day_of_week}のデータがデータベースに存在しません")
        
        total_density = sum(record.get('density_rate', 0) for record in data)
        total_seats = sum(record.get('occupied_seats', 0) for record in data)
        count = len(data)
        
        avg_density_rate = total_density / count
        avg_occupied_seats = total_seats / count
        
        occupancy_rate = avg_density_rate / 100.0 if avg_density_rate > 1 else avg_density_rate
        occupancy_rate = min(1.0, max(0.0, occupancy_rate))
        occupied_seats = min(8, max(0, round(avg_occupied_seats)))
        
        return {
            "occupancy_rate": round(occupancy_rate, 2),
            "occupied_seats": occupied_seats
        }
            
    except Exception as e:
        print(f"データベース予測エラー: {e}")
        raise Exception(f"データベースから予測データを取得できませんでした: {str(e)}")

def handler(request, context):
    """Vercel用のハンドラー関数"""
    try:
        # リクエストメソッドの取得
        method = request.method if hasattr(request, 'method') else 'GET'
        
        # CORSヘッダーの設定
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin, Accept, X-Requested-With',
            'Content-Type': 'application/json'
        }
        
        # OPTIONSリクエスト（プリフライト）の処理
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({"message": "CORS preflight"})
            }
        
        # GETリクエストの処理
        if method == 'GET':
            # 現在の日時を取得
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            today_weekday = today.weekday()
            tomorrow_weekday = tomorrow.weekday()
            
            # 曜日名を取得するヘルパー関数
            def get_weekday_name(weekday):
                weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
                return weekday_names[weekday]
            
            # 今日の予測
            if today_weekday >= 5:  # 土日
                today_prediction = {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0
                }
            else:
                today_prediction = get_database_prediction(today_weekday)
            
            # 明日の予測
            if tomorrow_weekday >= 5:  # 土日
                tomorrow_prediction = {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0
                }
            else:
                tomorrow_prediction = get_database_prediction(tomorrow_weekday)
            
            # フロントエンドの型定義に合わせたレスポンス形式
            response_data = {
                "success": True,
                "data": {
                    "today": {
                        "weekday": today_weekday,
                        "weekday_name": get_weekday_name(today_weekday),
                        "occupancy_rate": today_prediction["occupancy_rate"],
                        "occupied_seats": today_prediction["occupied_seats"]
                    },
                    "tomorrow": {
                        "weekday": tomorrow_weekday,
                        "weekday_name": get_weekday_name(tomorrow_weekday),
                        "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                        "occupied_seats": tomorrow_prediction["occupied_seats"]
                    }
                },
                "prediction_method": "database",
                "environment": "production"
            }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data, ensure_ascii=False)
            }
        
        # サポートされていないメソッド
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({
                "success": False,
                "error": f"サポートされていないHTTPメソッド: {method}"
            }, ensure_ascii=False)
        }
            
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"今日・明日予測APIでエラーが発生しました: {str(e)}"
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(error_response, ensure_ascii=False)
        } 