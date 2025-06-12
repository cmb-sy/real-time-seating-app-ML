"""
週間平均予測データを提供するVercelサーバーレス関数（機械学習モデル使用）
"""
import json
import os
import sys
import joblib
import numpy as np
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
from pathlib import Path

# ルートディレクトリをシステムパスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

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
        """週間平均予測データを返す（機械学習モデル使用）"""
        try:
            # モデルをロード
            try:
                model_data = self.load_ml_models()
                if not model_data:
                    self.send_error_response("ML予測モデルをロードできませんでした。")
                    return
            except Exception as e:
                self.send_error_response(f"モデルロードエラー: {str(e)}")
                return
            
            # MLモデルを使用した週間平均計算
            weekly_averages = self.calculate_weekly_averages_with_ml(model_data)
            
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
                    "model_version": model_data.get("version", "1.0.0"),
                    "last_updated": now.isoformat(),
                    "model_type": "gradient_boosting",
                    "features_used": ["day_of_week"],
                    "confidence": self.get_model_confidence(model_data),
                    "data_source": "ml_model",
                    "prediction_type": "ml_weekly_average"
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
            "message": "モデルファイルが見つからないか、予測実行中にエラーが発生しました。"
        }
        
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def load_ml_models(self):
        """機械学習モデルをロード"""
        try:
            # モデルファイルのパス
            base_dir = Path(__file__).resolve().parent.parent
            models_dir = base_dir / "models"
            
            # 必要なモデルファイル
            density_model_path = models_dir / "density_model.joblib"
            seats_model_path = models_dir / "seats_model.joblib"
            best_params_path = models_dir / "best_params.joblib"
            model_performance_path = models_dir / "model_performance.joblib"
            
            # ファイルの存在確認
            if not all(f.exists() for f in [density_model_path, seats_model_path, best_params_path, model_performance_path]):
                return None
            
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
    
    def predict_with_ml_model(self, model_data, day_of_week):
        """MLモデルで予測を実行"""
        try:
            # 特徴量として曜日のみを使用
            features = np.array([[day_of_week]])
            
            # 密度率と座席数の予測
            density_model = model_data.get("density_model")
            seats_model = model_data.get("seats_model")
            
            if density_model and seats_model:
                density_pred = density_model.predict(features)[0]
                seats_pred = seats_model.predict(features)[0]
                
                # 予測値を適切な範囲に調整
                density_pred = max(0, min(100, density_pred))
                seats_pred = max(0, min(int(seats_pred), 100))
                
                return {
                    "density_rate": round(density_pred, 2),
                    "occupied_seats": int(seats_pred)
                }
            else:
                return {
                    "density_rate": None,
                    "occupied_seats": None
                }
        except Exception as e:
            print(f"予測エラー: {str(e)}")
            return {
                "density_rate": None,
                "occupied_seats": None
            }
    
    def get_model_confidence(self, model_data):
        """モデルの信頼度を取得"""
        try:
            # パフォーマンス情報
            model_performance = model_data.get("model_performance", {})
            density_rmse = model_performance.get("density", {}).get("test_rmse", 0)
            seats_rmse = model_performance.get("seats", {}).get("test_rmse", 0)
            
            # 信頼度の計算
            confidence = "medium"  # デフォルト
            if density_rmse < 10 and seats_rmse < 1:
                confidence = "high"
            elif density_rmse > 15 or seats_rmse > 1.5:
                confidence = "low"
            
            return confidence
        except:
            return "medium"
    
    def calculate_weekly_averages_with_ml(self, model_data):
        """機械学習モデルを使用した週間平均計算（平日のみ）"""
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        weekly_averages = []
        
        # パフォーマンス情報
        model_performance = model_data.get("model_performance", {})
        density_rmse = model_performance.get("density", {}).get("test_rmse", 0)
        seats_rmse = model_performance.get("seats", {}).get("test_rmse", 0)
        
        # 平日のみ（0-4: 月曜日から金曜日）
        for weekday in range(5):
            # 曜日ごとの予測
            weekday_prediction = self.predict_with_ml_model(model_data, weekday)
            
            if weekday_prediction["density_rate"] is None:
                # 予測エラーの場合はスキップ
                continue
            
            # 曜日全体の平均占有率
            day_avg_occupancy = weekday_prediction["density_rate"] / 100.0
            available_seats = 100 - int(weekday_prediction["occupied_seats"])
            
            # 混雑状況の判定
            status = "busy" if day_avg_occupancy > 0.8 else "moderate" if day_avg_occupancy > 0.5 else "available"
            
            # 信頼度
            confidence = self.get_model_confidence(model_data)
            
            # 曜日データを追加
            weekly_averages.append({
                "weekday": weekday,
                "weekday_name": weekday_names[weekday],
                "prediction": {
                    "occupancy_rate": round(day_avg_occupancy, 2),
                    "available_seats": available_seats,
                    "status": status,
                    "confidence": confidence,
                    "data_points": 55,  # 訓練データのサンプル数（固定値）
                    "prediction_type": "ml_model",
                    "model_details": {
                        "density_rmse": round(density_rmse, 2) if density_rmse else None,
                        "seats_rmse": round(seats_rmse, 2) if seats_rmse else None,
                        "model_type": model_data.get("best_params", {}).get("density", {}).get("model_type", "gradient_boosting")
                    }
                }
            })
        
        return weekly_averages
    
    def get_weekly_summary(self, weekly_averages):
        """週間サマリーを生成"""
        if not weekly_averages:
            return {
                "most_busy_day": None,
                "least_busy_day": None,
                "average_occupancy": None,
                "recommendation": "データが不足しています"
            }
        
        # 各曜日の平均占有率を抽出
        day_occupancies = [(day["weekday"], day["weekday_name"], day["prediction"]["occupancy_rate"]) for day in weekly_averages]
        
        # 最も混雑する曜日と最も空いている曜日を特定
        day_occupancies.sort(key=lambda x: x[2], reverse=True)
        most_busy = day_occupancies[0]
        least_busy = day_occupancies[-1]
        
        # 全体の平均占有率
        all_rates = [day[2] for day in day_occupancies]
        avg_occupancy = sum(all_rates) / len(all_rates) if all_rates else 0
        
        # レコメンデーション生成
        if avg_occupancy > 0.7:
            recommendation = f"全体的に混雑しています。特に{most_busy[1]}は避けることをお勧めします。{least_busy[1]}の方が比較的空いています。"
        elif avg_occupancy > 0.5:
            recommendation = f"混雑する日があります。{most_busy[1]}は特に混雑するので注意してください。"
        else:
            recommendation = f"全体的に空いています。最も混雑するのは{most_busy[1]}ですが、それでも比較的余裕があります。"
        
        return {
            "most_busy_day": {
                "weekday": most_busy[0],
                "weekday_name": most_busy[1],
                "occupancy_rate": most_busy[2]
            },
            "least_busy_day": {
                "weekday": least_busy[0],
                "weekday_name": least_busy[1],
                "occupancy_rate": least_busy[2]
            },
            "average_occupancy": round(avg_occupancy, 2),
            "recommendation": recommendation,
            "prediction_type": "ml_model"
        } 