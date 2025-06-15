"""
週間平均予測API - 直接HTTP接続版
"""
import os
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

def get_all_supabase_data_direct():
    """直接HTTP接続でSupabaseから全データを取得"""
    try:
        # 環境変数の取得
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("環境変数が設定されていません")
        
        # Supabase REST APIエンドポイント
        api_url = f"{supabase_url}/rest/v1/density_history"
        
        # クエリパラメータ（全データを取得）
        query_params = urllib.parse.urlencode({
            'select': '*'
        })
        
        # HTTPリクエストヘッダー
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # HTTPリクエストの作成
        req = urllib.request.Request(
            url=f"{api_url}?{query_params}",
            headers=headers,
            method='GET'
        )
        
        # リクエストの実行
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
            
    except Exception as e:
        print(f"データベース取得エラー: {e}")
        raise Exception(f"データベースからデータを取得できませんでした: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()
    
    def do_GET(self):
        """週間平均予測API処理"""
        try:
            # データベースから全データを取得
            data = get_all_supabase_data_direct()
            
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
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
            self.end_headers()
            self.wfile.write(json.dumps(weekly_averages, ensure_ascii=False).encode("utf-8"))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"週間平均予測APIでエラーが発生しました: {str(e)}"
            }
            
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8")) 