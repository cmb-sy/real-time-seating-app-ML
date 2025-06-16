"""
APIサーバー
"""
import sys
sys.path.append('utils') #先に呼ばないとダメ

from http.server import BaseHTTPRequestHandler

from prediction import PredictionService
from response_helper import send_json_response, send_error_response

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path = self.path
            if path == '/api/predictions/today-tomorrow':
                self.handle_today_tomorrow()
            elif path == '/api/predictions/weekly-average':
                self.handle_weekly_average()
            else:
                send_error_response(self, "Endpoint not found")
        except Exception as e:
            send_error_response(self, "Internal server error: " + str(e))
         
    def handle_today_tomorrow(self):
        """今日・明日予測API"""
        try:
            # PredictionServiceを使用
            prediction_service = PredictionService()
            predictions = prediction_service.predict_today_tomorrow()
            
            # レスポンスデータの構築
            response_data = {
                "success": True,
                "data": predictions,
                "prediction_method": "ml_model_with_supabase_fallback",
                "environment": "production"
            }
            
            send_json_response(self, response_data)
            
        except Exception as e:
            send_error_response(self, f"Failed to get predictions: {str(e)}")
    
    def handle_weekly_average(self):
        """週間平均予測API"""
        try:
            # PredictionServiceを使用
            prediction_service = PredictionService()
            weekly_predictions = prediction_service.predict_weekly_average()
            
            # レスポンスデータの構築
            response_data = {
                "success": True,
                "data": weekly_predictions,
                "prediction_method": "database_average",
                "environment": "production"
            }
            
            send_json_response(self, response_data)
            
        except Exception as e:
            send_error_response(self, f"Failed to calculate weekly averages: {str(e)}")