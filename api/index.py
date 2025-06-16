"""
APIサーバー
"""
import sys
sys.path.append('utils')

from http.server import BaseHTTPRequestHandler
from prediction import PredictionService
from response_helper import send_json_response, send_error_response, send_options_response, run_server

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストに対応"""
        send_options_response(self)
    
    def do_GET(self):
        try:
            path = self.path
            if path == '/api/predictions/today-tomorrow':
                self.handle_today_tomorrow()
            elif path == '/api/predictions/weekly-average':
                self.handle_weekly_average()
            elif path == '/docs' or path == '/':
                self.handle_docs()
            else:
                send_error_response(self, "Endpoint not found", 404)
        except Exception as e:
            send_error_response(self, f"Internal server error: {str(e)}")
    
    def handle_docs(self):
        """API ドキュメンテーション"""
        try:
            docs_data = {
                "title": "Prediction API",
                "version": "1.0.0",
                "endpoints": [
                    {
                        "path": "/api/predictions/today-tomorrow",
                        "method": "GET",
                        "description": "今日・明日の予測データを取得"
                    },
                    {
                        "path": "/api/predictions/weekly-average",
                        "method": "GET", 
                        "description": "週間平均予測データを取得"
                    }
                ]
            }
            send_json_response(self, docs_data)
        except Exception as e:
            send_error_response(self, f"Failed to load docs: {str(e)}")
         
    def handle_today_tomorrow(self):
        """今日・明日予測API"""
        try:
            prediction_service = PredictionService()
            predictions = prediction_service.predict_today_tomorrow()
            
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
            prediction_service = PredictionService()
            weekly_predictions = prediction_service.predict_weekly_average()
            
            response_data = {
                "success": True,
                "data": weekly_predictions,
                "prediction_method": "database_average",
                "environment": "production"
            }
            
            send_json_response(self, response_data)
        except Exception as e:
            send_error_response(self, f"Failed to calculate weekly averages: {str(e)}")

if __name__ == '__main__':
    run_server(handler, 8000, "Prediction API")