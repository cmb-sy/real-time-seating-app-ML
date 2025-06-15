"""
週間平均予測データを提供するVercelサーバーレス関数（Supabase連携）
"""
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# ルートディレクトリをシステムパスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.utils.database import get_supabase_client
from src.utils.response_helper import send_success_response, send_error_response, send_options_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        send_options_response(self)
    
    def do_GET(self):
        """週間平均予測データを返す"""
        try:
            weekly_averages = self.calculate_weekly_averages()
            
            response_data = {
                "success": True,
                "data": {
                    "weekly_averages": weekly_averages
                }
            }
            
            send_success_response(self, response_data)
            
        except Exception as e:
            send_error_response(self, f"週間平均データの取得中にエラーが発生しました: {str(e)}")
    
    def calculate_weekly_averages(self):
        """Supabaseから週間平均データを計算"""
        try:
            supabase = get_supabase_client()
            
            # 過去4週間のデータを取得
            response = supabase.table('seating_data').select('*').order('timestamp', desc=True).limit(1000).execute()
            
            if not response.data:
                return self.get_default_weekly_averages()
            
            # 曜日別にデータを集計
            weekday_data = {i: [] for i in range(5)}
            
            for record in response.data:
                try:
                    # timestampから曜日を取得
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    weekday = timestamp.weekday()
                    
                    # 平日のみ処理
                    if weekday < 5:
                        occupancy_rate = record.get('occupancy_rate')
                        occupied_seats = record.get('occupied_seats')
                        
                        # データの妥当性チェック
                        if occupancy_rate is not None and occupied_seats is not None:
                            # NaNやNoneでない値のみを追加
                            if not (str(occupancy_rate).lower() in ['nan', 'none', ''] or 
                                   str(occupied_seats).lower() in ['nan', 'none', '']):
                                # 値の範囲チェック
                                if 0 <= float(occupancy_rate) <= 1 and 0 <= int(occupied_seats) <= 8:
                                    weekday_data[weekday].append({
                                        'occupancy_rate': float(occupancy_rate),
                                        'occupied_seats': int(occupied_seats)
                                    })
                except Exception as e:
                    # 個別レコードのエラーは無視して続行
                    continue
            
            # 曜日別平均を計算
            weekly_averages = []
            weekday_names = ["月", "火", "水", "木", "金"]
            
            for weekday in range(5):
                data = weekday_data[weekday]
                
                avg_occupancy_rate = sum(d['occupancy_rate'] for d in data) / len(data)
                avg_occupied_seats = sum(d['occupied_seats'] for d in data) / len(data)
                    
                # 席数8に基づく調整
                avg_occupied_seats = min(8, max(0, round(avg_occupied_seats)))
                avg_occupancy_rate = min(1.0, max(0.0, avg_occupancy_rate))
                    
                weekly_averages.append({
                    "day_of_week": weekday_names[weekday],
                    "occupancy_rate": round(avg_occupancy_rate, 2),
                    "occupied_seats": int(avg_occupied_seats)
                })
            print(weekly_averages)
            
            return weekly_averages
            
        except Exception as e:
            print(f"週間平均計算エラー: {str(e)}")

if __name__ == "__main__":
    handler().calculate_weekly_averages()