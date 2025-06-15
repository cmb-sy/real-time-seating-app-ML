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
            send_error_response(self, f"週間平均データの生成中にエラーが発生しました: {str(e)}")
    
    def calculate_weekly_averages(self):
        """Supabaseから取得したデータで週間平均計算（平日のみ）"""
        weekday_names = ["月曜", "火曜", "水曜", "木曜", "金曜"]
        weekly_averages = []
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # density_historyテーブルから平日データ（day_of_week: 0-4）を取得
        response = supabase.table("density_history").select("*").in_("day_of_week", [0, 1, 2, 3, 4]).execute()
        
        if not response.data:
            raise Exception("Supabaseからデータを取得できませんでした")
        
        # 曜日ごとにデータを集計
        weekday_data = {}
        
        for record in response.data:
            day_of_week = record['day_of_week']
            if day_of_week not in weekday_data:
                weekday_data[day_of_week] = {
                    'density_rates': [],
                    'occupied_seats': []
                }
            
            weekday_data[day_of_week]['density_rates'].append(float(record['density_rate']))
            weekday_data[day_of_week]['occupied_seats'].append(int(record['occupied_seats']))
        
        # 平日のみ（0-4: 月曜日から金曜日）
        for weekday in range(5):
            if weekday in weekday_data:
                # 平均を計算
                density_rates = weekday_data[weekday]['density_rates']
                occupied_seats = weekday_data[weekday]['occupied_seats']
                
                avg_density_rate = sum(density_rates) / len(density_rates)
                avg_occupied_seats = sum(occupied_seats) / len(occupied_seats)
                
                # 占有率を0-1の範囲に正規化
                occupancy_rate = avg_density_rate / 100.0
                available_seats = 100 - int(avg_occupied_seats)
            else:
                # データがない曜日はスキップ
                continue
            
            weekly_averages.append({
                "weekday": weekday,
                "weekday_name": weekday_names[weekday],
                "occupancy_rate": round(occupancy_rate, 2),
                "available_seats": available_seats
            })
        
        return weekly_averages 