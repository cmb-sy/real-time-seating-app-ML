"""
今日・明日予測API - 直接HTTP接続版
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

def get_supabase_data_direct(day_of_week):
    """直接HTTP接続でSupabaseからデータを取得"""
    try:
        # 環境変数の取得
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("環境変数が設定されていません")
        
        # Supabase REST APIエンドポイント
        api_url = f"{supabase_url}/rest/v1/density_history"
        
        # クエリパラメータ
        query_params = urllib.parse.urlencode({
            'select': 'density_rate,occupied_seats',
            'day_of_week': f'eq.{day_of_week}'
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
            
            if not data or len(data) == 0:
                raise Exception(f"曜日{day_of_week}のデータがデータベースに存在しません")
            
            # 平均計算
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
                today_prediction = get_supabase_data_direct(today_weekday)
            
            # 明日の予測
            if tomorrow_weekday >= 5:  # 土日
                tomorrow_prediction = {
                    "occupancy_rate": 0.0,
                    "occupied_seats": 0
                }
            else:
                tomorrow_prediction = get_supabase_data_direct(tomorrow_weekday)
            
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
                "prediction_method": "database_direct_http",
                "environment": "production"
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept, X-Requested-With")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"今日・明日予測APIでエラーが発生しました: {str(e)}"
            }
            
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8")) 