"""
週間平均予測API - Vercel個別エンドポイント
"""
import os
import json
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
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(weekly_averages, ensure_ascii=False)
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
            "error": f"週間平均予測APIでエラーが発生しました: {str(e)}"
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(error_response, ensure_ascii=False)
        } 