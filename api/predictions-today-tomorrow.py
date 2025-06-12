"""
今日と明日の予測データを提供するVercelサーバーレス関数
Supabaseの実際のデータのみを使用
"""
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """今日・明日の座席予測データを返す"""
        try:
            # Supabaseから実際のデータを取得
            historical_data = self.fetch_supabase_data()
            
            if not historical_data:
                self.send_error_response("Supabaseからデータを取得できませんでした。データベースにデータが存在しない可能性があります。")
                return
            
            # 現在の日時を取得
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            current_hour = now.hour
            
            # 実データに基づく予測計算
            today_predictions = self.calculate_predictions_with_data(
                historical_data, today, current_hour, is_today=True
            )
            tomorrow_predictions = self.calculate_predictions_with_data(
                historical_data, tomorrow, 9, is_today=False
            )
            
            # レスポンスデータ
            response_data = {
                "success": True,
                "timestamp": now.isoformat(),
                "data": {
                    "today": {
                        "date": today.isoformat(),
                        "day_of_week": ["月", "火", "水", "木", "金", "土", "日"][today.weekday()],
                        "predictions": today_predictions,
                        "total_hours": len(today_predictions)
                    },
                    "tomorrow": {
                        "date": tomorrow.isoformat(),
                        "day_of_week": ["月", "火", "水", "木", "金", "土", "日"][tomorrow.weekday()],
                        "predictions": tomorrow_predictions,
                        "total_hours": len(tomorrow_predictions)
                    }
                },
                "metadata": {
                    "model_version": "2.1.0",
                    "last_updated": now.isoformat(),
                    "confidence": "high",
                    "data_source": "supabase_historical_data",
                    "historical_records_used": len(historical_data)
                }
            }
            
            self.send_success_response(response_data)
            
        except Exception as e:
            self.send_error_response(f"予測データの生成中にエラーが発生しました: {str(e)}")
    
    def send_success_response(self, data):
        """成功レスポンスを送信"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, error_message):
        """エラーレスポンスを送信"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        error_data = {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
            "message": "Supabaseデータベースの設定を確認してください。SUPABASE_SETUP.mdを参照してください。"
        }
        
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def fetch_supabase_data(self):
        """Supabaseから履歴データを取得"""
        # Supabase設定（環境変数から取得）
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("SUPABASE_URLまたはSUPABASE_ANON_KEYが設定されていません")
        
        # 過去30日間のデータを取得
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Supabase REST API呼び出し
        url = f"{supabase_url}/rest/v1/density_history"
        params = {
            'select': '*',
            'created_at': f'gte.{thirty_days_ago}',
            'order': 'created_at.desc',
            'limit': '1000'
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        req = urllib.request.Request(full_url)
        req.add_header('apikey', supabase_key)
        req.add_header('Authorization', f'Bearer {supabase_key}')
        req.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Supabase API エラー: HTTP {response.status}")
                
                data = json.loads(response.read().decode('utf-8'))
                return data
        except Exception as e:
            raise Exception(f"Supabaseデータ取得エラー: {str(e)}")
    
    def calculate_predictions_with_data(self, historical_data, target_date, start_hour, is_today=True):
        """実データに基づく予測計算"""
        predictions = []
        weekday = target_date.weekday()
        
        # 同じ曜日の履歴データを抽出
        same_weekday_data = []
        for record in historical_data:
            try:
                record_date = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00')).date()
                if record_date.weekday() == weekday:
                    same_weekday_data.append(record)
            except:
                continue
        
        # 時間帯別の平均占有率を計算
        hourly_averages = {}
        hourly_data_counts = {}
        
        for hour in range(9, 19):
            hour_data = []
            for record in same_weekday_data:
                try:
                    record_hour = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00')).hour
                    if record_hour == hour and 'density' in record:
                        # densityを占有率に変換（0-1の範囲）
                        density = float(record['density'])
                        occupancy_rate = min(max(density / 100.0, 0.0), 1.0)
                        hour_data.append(occupancy_rate)
                except:
                    continue
            
            # 平均計算
            if hour_data:
                hourly_averages[hour] = sum(hour_data) / len(hour_data)
                hourly_data_counts[hour] = len(hour_data)
            else:
                # データがない時間帯はスキップ（予測しない）
                hourly_averages[hour] = None
                hourly_data_counts[hour] = 0
        
        # 予測データ生成
        end_hour = 19 if not is_today else 19
        for hour in range(start_hour, end_hour):
            if hourly_averages.get(hour) is None:
                # データがない時間帯は予測不可として表示
                predictions.append({
                    "hour": hour,
                    "occupancy_rate": None,
                    "available_seats": None,
                    "status": "no_data",
                    "confidence": "none",
                    "data_points": 0,
                    "message": "この時間帯のデータが不足しています"
                })
                continue
            
            occupancy_rate = hourly_averages[hour]
            data_points = hourly_data_counts[hour]
            
            # 占有率を0-1の範囲に制限
            occupancy_rate = min(max(occupancy_rate, 0.0), 1.0)
            available_seats = int(100 * (1 - occupancy_rate))
            
            # 信頼度の計算
            if data_points >= 10:
                confidence = "high"
            elif data_points >= 5:
                confidence = "medium"
            elif data_points >= 2:
                confidence = "low"
            else:
                confidence = "very_low"
            
            predictions.append({
                "hour": hour,
                "occupancy_rate": round(occupancy_rate, 2),
                "available_seats": available_seats,
                "status": "busy" if occupancy_rate > 0.8 else "moderate" if occupancy_rate > 0.5 else "available",
                "confidence": confidence,
                "data_points": data_points
            })
        
        return predictions 