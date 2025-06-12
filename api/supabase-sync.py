import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

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
        """Supabase用の座席データを返す"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        # URLパラメータの解析
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # パラメータの取得
        data_type = query_params.get('type', ['current'])[0]
        date_param = query_params.get('date', [None])[0]
        
        now = datetime.now()
        
        if data_type == 'current':
            # 現在の座席状況
            response_data = self.get_current_status(now)
        elif data_type == 'predictions':
            # 予測データ
            response_data = self.get_predictions_for_supabase(now, date_param)
        elif data_type == 'historical':
            # 履歴データ（シミュレーション）
            response_data = self.get_historical_data(now)
        else:
            response_data = {"error": "Invalid data type", "valid_types": ["current", "predictions", "historical"]}
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """Supabaseからのデータ更新リクエストを処理"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Origin')
        self.end_headers()
        
        try:
            # リクエストボディの読み取り
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # データ更新の処理（実際のSupabaseとの連携では、ここでデータベースを更新）
            response_data = {
                "success": True,
                "message": "データが正常に受信されました",
                "timestamp": datetime.now().isoformat(),
                "received_data": request_data,
                "next_sync": (datetime.now() + timedelta(minutes=15)).isoformat()
            }
            
        except Exception as e:
            response_data = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def get_current_status(self, now):
        """現在の座席状況を生成"""
        current_hour = now.hour
        weekday = now.weekday()
        
        # 現在時刻に基づく占有率計算
        if 9 <= current_hour <= 18:
            if current_hour < 11:
                base_rate = 0.2 + (current_hour - 9) * 0.1
            elif current_hour < 13:
                base_rate = 0.7 + (current_hour - 11) * 0.1
            elif current_hour < 15:
                base_rate = 0.8 - (current_hour - 13) * 0.1
            else:
                base_rate = 0.6 + (current_hour - 15) * 0.05
            
            # 曜日調整
            if weekday >= 5:  # 土日
                base_rate *= 0.5
            elif weekday == 4:  # 金曜日
                base_rate *= 1.1
        else:
            base_rate = 0.1  # 営業時間外
        
        occupancy_rate = min(max(base_rate, 0.05), 0.98)
        total_seats = 100
        occupied_seats = int(total_seats * occupancy_rate)
        available_seats = total_seats - occupied_seats
        
        return {
            "success": True,
            "timestamp": now.isoformat(),
            "current_status": {
                "total_seats": total_seats,
                "occupied_seats": occupied_seats,
                "available_seats": available_seats,
                "occupancy_rate": round(occupancy_rate, 2),
                "status": "busy" if occupancy_rate > 0.8 else "moderate" if occupancy_rate > 0.5 else "available",
                "last_updated": now.isoformat(),
                "is_open": 9 <= current_hour <= 18
            },
            "metadata": {
                "source": "ml_prediction",
                "confidence": "high" if 9 <= current_hour <= 18 else "low"
            }
        }
    
    def get_predictions_for_supabase(self, now, date_param):
        """Supabase用の予測データを生成"""
        if date_param:
            try:
                target_date = datetime.fromisoformat(date_param).date()
            except:
                target_date = now.date()
        else:
            target_date = now.date()
        
        predictions = []
        weekday = target_date.weekday()
        
        for hour in range(9, 19):
            # 時間帯パターン
            if hour < 11:
                base_rate = 0.25 + (hour - 9) * 0.12
            elif hour < 13:
                base_rate = 0.75 + (hour - 11) * 0.1
            elif hour < 15:
                base_rate = 0.85 - (hour - 13) * 0.15
            else:
                base_rate = 0.55 + (hour - 15) * 0.08
            
            # 曜日調整
            if weekday >= 5:  # 土日
                base_rate *= 0.5
            elif weekday == 4:  # 金曜日
                base_rate *= 1.15
            
            occupancy_rate = min(max(base_rate, 0.05), 0.98)
            
            predictions.append({
                "date": target_date.isoformat(),
                "hour": hour,
                "predicted_occupancy_rate": round(occupancy_rate, 2),
                "predicted_available_seats": int(100 * (1 - occupancy_rate)),
                "confidence": "high",
                "created_at": now.isoformat()
            })
        
        return {
            "success": True,
            "timestamp": now.isoformat(),
            "predictions": predictions,
            "metadata": {
                "target_date": target_date.isoformat(),
                "total_predictions": len(predictions),
                "model_version": "2.0.0"
            }
        }
    
    def get_historical_data(self, now):
        """履歴データのシミュレーション"""
        historical_data = []
        
        # 過去7日間のデータを生成
        for days_ago in range(7):
            date = (now - timedelta(days=days_ago)).date()
            weekday = date.weekday()
            
            for hour in range(9, 19):
                # 基本パターン + ランダム要素
                if hour < 11:
                    base_rate = 0.2 + (hour - 9) * 0.1
                elif hour < 13:
                    base_rate = 0.7 + (hour - 11) * 0.1
                elif hour < 15:
                    base_rate = 0.8 - (hour - 13) * 0.1
                else:
                    base_rate = 0.6 + (hour - 15) * 0.05
                
                # 曜日調整
                if weekday >= 5:
                    base_rate *= 0.6
                elif weekday == 4:
                    base_rate *= 1.1
                
                # 若干のランダム性を追加
                import random
                random.seed(int(date.strftime('%Y%m%d')) + hour)  # 再現可能なランダム性
                variation = random.uniform(-0.1, 0.1)
                occupancy_rate = min(max(base_rate + variation, 0.05), 0.98)
                
                historical_data.append({
                    "date": date.isoformat(),
                    "hour": hour,
                    "actual_occupancy_rate": round(occupancy_rate, 2),
                    "actual_occupied_seats": int(100 * occupancy_rate),
                    "recorded_at": (datetime.combine(date, datetime.min.time().replace(hour=hour)) + timedelta(minutes=30)).isoformat()
                })
        
        return {
            "success": True,
            "timestamp": now.isoformat(),
            "historical_data": historical_data,
            "metadata": {
                "period": "past_7_days",
                "total_records": len(historical_data),
                "data_source": "simulated_historical"
            }
        } 