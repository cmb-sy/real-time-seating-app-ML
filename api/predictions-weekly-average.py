"""
週間平均予測データを提供するVercelサーバーレス関数
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
        """週間平均予測データを返す"""
        try:
            # Supabaseから実際のデータを取得
            historical_data = self.fetch_supabase_data()
            
            if not historical_data:
                self.send_error_response("Supabaseからデータを取得できませんでした。データベースにデータが存在しない可能性があります。")
                return
            
            # 実データに基づく週間平均計算
            weekly_averages = self.calculate_weekly_averages_with_data(historical_data)
            
            now = datetime.now()
            
            # レスポンスデータ
            response_data = {
                "success": True,
                "timestamp": now.isoformat(),
                "data": {
                    "weekly_averages": weekly_averages,
                    "summary": self.get_weekly_summary(weekly_averages)
                },
                "metadata": {
                    "model_version": "2.1.0",
                    "last_updated": now.isoformat(),
                    "confidence": "high",
                    "data_source": "supabase_historical_data",
                    "historical_records_used": len(historical_data),
                    "analysis_period": "past_30_days"
                }
            }
            
            self.send_success_response(response_data)
            
        except Exception as e:
            self.send_error_response(f"週間平均データの生成中にエラーが発生しました: {str(e)}")
    
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
            'limit': '2000'
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
    
    def calculate_weekly_averages_with_data(self, historical_data):
        """実データに基づく週間平均計算"""
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        weekly_averages = []
        
        for weekday in range(7):
            # 該当曜日のデータを抽出
            weekday_data = []
            for record in historical_data:
                try:
                    record_date = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                    if record_date.weekday() == weekday and 'density' in record:
                        density = float(record['density'])
                        occupancy_rate = min(max(density / 100.0, 0.0), 1.0)
                        weekday_data.append({
                            'hour': record_date.hour,
                            'occupancy_rate': occupancy_rate,
                            'date': record_date.date()
                        })
                except:
                    continue
            
            # 時間帯別平均を計算
            hourly_predictions = []
            total_data_points = 0
            
            for hour in range(9, 19):
                hour_data = [d['occupancy_rate'] for d in weekday_data if d['hour'] == hour]
                
                if hour_data:
                    avg_occupancy = sum(hour_data) / len(hour_data)
                    data_points = len(hour_data)
                    total_data_points += data_points
                    
                    # 信頼度の計算
                    if data_points >= 10:
                        confidence = "high"
                    elif data_points >= 5:
                        confidence = "medium"
                    elif data_points >= 2:
                        confidence = "low"
                    else:
                        confidence = "very_low"
                    
                    # 占有率を0-1の範囲に制限
                    avg_occupancy = min(max(avg_occupancy, 0.0), 1.0)
                    available_seats = int(100 * (1 - avg_occupancy))
                    
                    hourly_predictions.append({
                        "hour": hour,
                        "average_occupancy_rate": round(avg_occupancy, 2),
                        "average_available_seats": available_seats,
                        "status": "busy" if avg_occupancy > 0.8 else "moderate" if avg_occupancy > 0.5 else "available",
                        "confidence": confidence,
                        "data_points": data_points
                    })
                else:
                    # データがない時間帯
                    hourly_predictions.append({
                        "hour": hour,
                        "average_occupancy_rate": None,
                        "average_available_seats": None,
                        "status": "no_data",
                        "confidence": "none",
                        "data_points": 0,
                        "message": "この時間帯のデータが不足しています"
                    })
            
            # 曜日全体の統計（データがある時間帯のみ）
            valid_predictions = [h for h in hourly_predictions if h['average_occupancy_rate'] is not None]
            
            if valid_predictions:
                daily_occupancy_rates = [h['average_occupancy_rate'] for h in valid_predictions]
                daily_avg = sum(daily_occupancy_rates) / len(daily_occupancy_rates)
                peak_hour = max(valid_predictions, key=lambda x: x['average_occupancy_rate'])['hour']
                lowest_hour = min(valid_predictions, key=lambda x: x['average_occupancy_rate'])['hour']
            else:
                daily_avg = None
                peak_hour = None
                lowest_hour = None
            
            weekly_averages.append({
                "day_of_week": weekday,
                "day_name": weekday_names[weekday],
                "hourly_predictions": hourly_predictions,
                "daily_average_occupancy": round(daily_avg, 2) if daily_avg is not None else None,
                "daily_average_available_seats": int(100 * (1 - daily_avg)) if daily_avg is not None else None,
                "peak_hour": peak_hour,
                "lowest_hour": lowest_hour,
                "total_data_points": total_data_points,
                "has_sufficient_data": total_data_points >= 10
            })
        
        return weekly_averages
    
    def get_weekly_summary(self, weekly_averages):
        """週間サマリーを生成"""
        # データがある曜日のみを対象
        valid_days = [day for day in weekly_averages if day['daily_average_occupancy'] is not None]
        
        if not valid_days:
            return {
                "error": "週間データが不足しています",
                "message": "各曜日のデータを蓄積してから再度お試しください",
                "total_valid_days": 0
            }
        
        # 最も混雑する曜日
        busiest_day = max(valid_days, key=lambda x: x['daily_average_occupancy'])
        
        # 最も空いている曜日
        quietest_day = min(valid_days, key=lambda x: x['daily_average_occupancy'])
        
        # 全体の平均
        overall_avg = sum(day['daily_average_occupancy'] for day in valid_days) / len(valid_days)
        
        # 推奨時間帯（全曜日で最も空いている時間）
        all_hourly_data = []
        for day in valid_days:
            for hour_data in day['hourly_predictions']:
                if hour_data['average_occupancy_rate'] is not None:
                    all_hourly_data.append({
                        'hour': hour_data['hour'],
                        'occupancy': hour_data['average_occupancy_rate']
                    })
        
        # 時間帯別平均
        hourly_averages = {}
        for hour in range(9, 19):
            hour_occupancies = [d['occupancy'] for d in all_hourly_data if d['hour'] == hour]
            if hour_occupancies:
                hourly_averages[hour] = sum(hour_occupancies) / len(hour_occupancies)
        
        if hourly_averages:
            best_hours = sorted(hourly_averages.items(), key=lambda x: x[1])[:3]
        else:
            best_hours = []
        
        return {
            "busiest_day": {
                "day": busiest_day['day_name'],
                "occupancy_rate": busiest_day['daily_average_occupancy']
            },
            "quietest_day": {
                "day": quietest_day['day_name'],
                "occupancy_rate": quietest_day['daily_average_occupancy']
            },
            "overall_weekly_average": round(overall_avg, 2),
            "recommended_hours": [
                {"hour": hour, "average_occupancy": round(occ, 2)} 
                for hour, occ in best_hours
            ],
            "insights": [
                f"{busiest_day['day_name']}が最も混雑します（平均{busiest_day['daily_average_occupancy']*100:.0f}%）",
                f"{quietest_day['day_name']}が最も空いています（平均{quietest_day['daily_average_occupancy']*100:.0f}%）",
                f"おすすめ時間帯: {best_hours[0][0]}時頃（平均{best_hours[0][1]*100:.0f}%）" if best_hours else "データ不足のため推奨時間を算出できません"
            ],
            "data_quality": {
                "total_valid_days": len(valid_days),
                "total_days_analyzed": len(weekly_averages),
                "data_coverage": f"{len(valid_days)}/7曜日"
            }
        } 