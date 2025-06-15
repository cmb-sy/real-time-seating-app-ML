"""
今日と明日の予測データを提供するVercelサーバーレス関数（機械学習モデル）
"""
import os
import sys
import joblib
import numpy as np
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.utils.response_helper import send_success_response, send_error_response, send_options_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエストへの対応"""
        send_options_response(self)
    
    def do_GET(self):
        """今日・明日の座席予測データを返す"""
        try:
            # 現在の日時を取得
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            # 平日チェック（月-金のみ対応）
            if today.weekday() >= 5:  # 土日の場合
                send_error_response(self, "土日は対応していません。平日（月-金）のみ予測を提供しています。")
                return
            
            if tomorrow.weekday() >= 5:  # 明日が土日の場合
                # 今日のみの予測を提供
                tomorrow = None
            
            # モデルをロード
            model_data = self.load_ml_models()
            if not model_data:
                send_error_response(self, "ML予測モデルをロードできませんでした。")
                return
            
            # 今日の予測
            today_weekday = today.weekday()
            today_prediction = self.generate_prediction_with_ml(model_data, today_weekday)
            
            response_data = {
                "success": True,
                "data": {
                    "today": {
                        "date": today.isoformat(),
                        "day_of_week": ["月", "火", "水", "木", "金"][today.weekday()],
                        "occupancy_rate": today_prediction["occupancy_rate"],
                        "available_seats": today_prediction["available_seats"]
                    }
                }
            }
            
            # 明日が平日の場合のみ明日の予測を追加
            if tomorrow is not None:
                tomorrow_weekday = tomorrow.weekday()
                tomorrow_prediction = self.generate_prediction_with_ml(model_data, tomorrow_weekday)
                
                response_data["data"]["tomorrow"] = {
                    "date": tomorrow.isoformat(),
                    "day_of_week": ["月", "火", "水", "木", "金"][tomorrow.weekday()],
                    "occupancy_rate": tomorrow_prediction["occupancy_rate"],
                    "available_seats": tomorrow_prediction["available_seats"]
                }
            else:
                response_data["data"]["tomorrow"] = {
                    "date": None,
                    "day_of_week": None,
                    "occupancy_rate": None,
                    "available_seats": None,
                    "message": "明日は土日のため対応していません"
                }
            
            send_success_response(self, response_data)
            
        except Exception as e:
            send_error_response(self, f"予測データの生成中にエラーが発生しました: {str(e)}")
    
    def load_ml_models(self):
        """機械学習モデルをロード"""
        try:
            # モデルファイルのパス
            current_dir = Path(__file__).resolve().parent
            
            density_model_path = current_dir / "density_model.joblib"
            seats_model_path = current_dir / "seats_model.joblib"
            best_params_path = current_dir / "best_params.joblib"
            model_performance_path = current_dir / "model_performance.joblib"
            
            # モデルのロード
            density_model = joblib.load(density_model_path)
            seats_model = joblib.load(seats_model_path)
            best_params = joblib.load(best_params_path)
            model_performance = joblib.load(model_performance_path)
            
            return {
                "density_model": density_model,
                "seats_model": seats_model,
                "best_params": best_params,
                "model_performance": model_performance,
                "version": "1.0.0"
            }
        except Exception as e:
            print(f"モデルロードエラー: {str(e)}")
            return None
    
    
    def generate_prediction_with_ml(self, model_data, day_of_week):
        """曜日別の予測を生成"""
        features = np.array([[day_of_week]])
            
        density_model = model_data.get("density_model")
        seats_model = model_data.get("seats_model")
            
        if density_model and seats_model:
            density_pred = density_model.predict(features)[0]
            seats_pred = seats_model.predict(features)[0]
            
            base_prediction = {
                "density_rate": round(density_pred, 2),
                "occupied_seats": int(seats_pred)
            }
        else:
            base_prediction = {
                "density_rate": None,
                "occupied_seats": None
            }
        
        if base_prediction["density_rate"] is None or base_prediction["occupied_seats"] is None:
            raise Exception("予測モデルがエラーを返しました")
        
        # 密度率から占有率を計算
        density_rate = base_prediction["density_rate"]
        occupied_seats = base_prediction["occupied_seats"]
        
        # 占有率を0-1の範囲に正規化
        occupancy_rate = density_rate / 100.0
        available_seats = 100 - int(occupied_seats)
        
        return {
            "occupancy_rate": round(occupancy_rate, 2),
            "available_seats": available_seats
        } 