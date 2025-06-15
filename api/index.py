"""
Vercel本番環境用API - Vercel標準形式での実装
"""
import os
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# Supabaseクライアント設定
def get_supabase_client():
    """Supabaseクライアントを初期化"""
    try:
        # 環境変数の詳細チェック
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        print(f"=== Supabase診断情報 ===")
        print(f"URL存在: {bool(supabase_url)}")
        print(f"URL値: {supabase_url[:50] if supabase_url else 'None'}...")
        print(f"Key存在: {bool(supabase_key)}")
        print(f"Key値: {supabase_key[:50] if supabase_key else 'None'}...")
        
        if not supabase_url:
            print("❌ NEXT_PUBLIC_SUPABASE_URL が設定されていません")
            return None
            
        if not supabase_key:
            print("❌ SUPABASE_SERVICE_ROLE_KEY または NEXT_PUBLIC_SUPABASE_ANON_KEY が設定されていません")
            return None
        
        # Supabaseライブラリの動的インポート
        try:
            print("📦 Supabaseライブラリをインポート中...")
            from supabase import create_client, Client
            print("✅ Supabaseライブラリのインポートに成功")
        except ImportError as import_error:
            print(f"❌ Supabaseライブラリのインポートエラー: {import_error}")
            return None
        
        # Supabaseクライアントの作成
        try:
            print("🔗 Supabaseクライアントを作成中...")
            supabase: Client = create_client(supabase_url, supabase_key)
            print("✅ Supabaseクライアントの初期化に成功")
            
            # 接続テスト
            print("🧪 データベース接続テスト中...")
            test_response = supabase.table('density_history').select('*').limit(1).execute()
            print(f"✅ データベース接続テストに成功: {len(test_response.data) if test_response.data else 0}件のデータ")
            
            return supabase
        except Exception as client_error:
            print(f"❌ Supabaseクライアント作成エラー: {client_error}")
            print(f"エラータイプ: {type(client_error).__name__}")
            return None
            
    except Exception as e:
        print(f"❌ Supabaseクライアント初期化の全般的エラー: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        return None

def get_database_prediction(day_of_week):
    """データベースから実際のデータを取得して予測"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("データベース接続失敗")
        
        # 該当曜日の過去データを取得
        response = supabase.table('density_history').select('density_rate, occupied_seats').eq('day_of_week', day_of_week).execute()
        data = response.data
        
        if not data or len(data) == 0:
            raise Exception(f"曜日{day_of_week}のデータがデータベースに存在しません")
        
        # 過去データの平均を計算
        total_density = sum(record.get('density_rate', 0) for record in data)
        total_seats = sum(record.get('occupied_seats', 0) for record in data)
        count = len(data)
        
        avg_density_rate = total_density / count
        avg_occupied_seats = total_seats / count
        
        # 正規化
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

def handle_today_tomorrow():
    """今日・明日予測API処理"""
    try:
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
        
        return response_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"今日・明日予測APIでエラーが発生しました: {str(e)}"
        }

def handle_weekly_average():
    """週間平均予測API処理"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("Supabaseクライアントの初期化に失敗しました")
            
        # density_historyテーブルから過去のデータを取得
        response = supabase.table('density_history').select('*').execute()
        data = response.data
        
        if not data or len(data) == 0:
            raise Exception("データベースにデータが存在しません")
            
        # 曜日別に集計（0-4: 月-金のみ、土日は除外）
        day_of_week_data = {i: [] for i in range(5)}  # 平日のみ（0-4）
        
        for record in data:
            day_of_week = record.get('day_of_week')
            density_rate = record.get('density_rate', 0)
            occupied_seats = record.get('occupied_seats', 0)
            
            # 土日（5, 6）のデータは除外し、平日（0-4）のみ処理
            if day_of_week is not None and 0 <= day_of_week <= 4:
                occupancy_rate = density_rate / 100.0 if density_rate > 1 else density_rate
                day_of_week_data[day_of_week].append({
                    'occupancy_rate': occupancy_rate,
                    'occupied_seats': occupied_seats
                })
        
        # 曜日名の定義
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        
        weekly_averages = {
            "success": True,
            "data": {
                "weekly_averages": []
            }
        }
        
        # 平日（0-4）のみ処理
        for day in range(5):  # 0-4の平日のみ
            values = day_of_week_data[day]
            if values:
                avg_occupancy = sum(v['occupancy_rate'] for v in values) / len(values)
                avg_occupied_seats = sum(v['occupied_seats'] for v in values) / len(values)
                
                final_occupied_seats = min(8, max(0, round(avg_occupied_seats)))
                final_occupancy_rate = min(1.0, max(0.0, avg_occupancy))
                
                weekly_averages["data"]["weekly_averages"].append({
                    "weekday": day,
                    "weekday_name": weekday_names[day],
                    "occupancy_rate": round(final_occupancy_rate, 2),
                    "occupied_seats": final_occupied_seats,
                })
            else:
                weekly_averages["data"]["weekly_averages"].append({
                    "weekday": day,
                    "weekday_name": weekday_names[day],
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0,
                })
        
        return weekly_averages
        
    except Exception as e:
        return {
            "success": False,
            "error": f"週間平均予測APIでエラーが発生しました: {str(e)}"
        }

def handle_database_test():
    """データベース接続テスト用のエンドポイント"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("データベース接続失敗")
        
        # 既存データの取得テスト（読み取り専用）
        response = supabase.table('density_history').select('*').limit(5).execute()
        
        return {
            "success": True,
            "message": "データベース接続テストに成功しました",
            "data_count": len(response.data) if response.data else 0,
            "sample_data": response.data if response.data else []
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"データベース接続テストでエラーが発生しました: {str(e)}"
        }

def create_response(data, status_code=200):
    """レスポンスオブジェクトを作成"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin, Accept, X-Requested-With',
            'Access-Control-Max-Age': '86400'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }

def handler(request, context=None):
    """Vercel用のメインハンドラー関数"""
    try:
        # リクエストオブジェクトの構造を確認
        print(f"🔍 リクエストオブジェクト: {type(request)}")
        print(f"🔍 リクエスト内容: {request}")
        
        # Vercelのリクエスト形式に対応
        if hasattr(request, 'method'):
            method = request.method
            path = getattr(request, 'path', getattr(request, 'url', '/'))
        else:
            method = request.get('httpMethod', request.get('method', 'GET'))
            path = request.get('path', request.get('rawPath', '/'))
        
        print(f"🔍 受信したリクエスト: method={method}, path={path}")
        
        # OPTIONSリクエスト（プリフライト）の処理
        if method == 'OPTIONS':
            return create_response({"message": "CORS preflight"}, 200)
        
        # GETリクエストの処理
        if method == 'GET':
            # パスに基づいてエンドポイントを判定
            if 'today-tomorrow' in path:
                print("📊 今日・明日予測APIを実行")
                response_data = handle_today_tomorrow()
            elif 'weekly-average' in path:
                print("📈 週間平均予測APIを実行")
                response_data = handle_weekly_average()
            elif 'test-db' in path:
                print("🧪 データベーステストAPIを実行")
                response_data = handle_database_test()
            elif path == '/' or path == '':
                print("🏠 ルートエンドポイントを実行")
                response_data = {
                    "success": True,
                    "message": "リアルタイム座席予測API",
                    "version": "3.0.0",
                    "endpoints": {
                        "today_tomorrow": "/api/predictions/today-tomorrow",
                        "weekly_average": "/api/predictions/weekly-average",
                        "database_test": "/api/test-db"
                    },
                    "status": "運用中",
                    "environment": "production",
                    "received_path": path,
                    "request_type": str(type(request))
                }
            else:
                print(f"❌ 未知のエンドポイント: {path}")
                response_data = {
                    "success": False,
                    "error": f"エンドポイントが見つかりません: {path}",
                    "available_endpoints": [
                        "/api/predictions/today-tomorrow",
                        "/api/predictions/weekly-average",
                        "/api/test-db"
                    ],
                    "received_path": path,
                    "request_debug": str(request)[:500]
                }
                return create_response(response_data, 404)
            
            # 成功レスポンス
            status_code = 200 if response_data.get("success", False) else 500
            return create_response(response_data, status_code)
        
        # サポートされていないメソッド
        return create_response({
            "success": False,
            "error": f"サポートされていないHTTPメソッド: {method}"
        }, 405)
        
    except Exception as e:
        print(f"❌ ハンドラーエラー: {e}")
        error_response = {
            "success": False,
            "error": f"サーバーエラーが発生しました: {str(e)}",
            "environment": "production",
            "request_debug": str(request)[:500] if 'request' in locals() else "unknown"
        }
        return create_response(error_response, 500) 