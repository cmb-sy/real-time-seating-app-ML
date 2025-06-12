"""
今日と明日の予測データを提供するVercelサーバーレス関数
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
        """今日・明日の座席予測データを返す"""
        try:
            # 現在の日時を取得
            now = datetime.now()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            # 平日チェック（月-金のみ対応）
            if today.weekday() >= 5:  # 土日の場合
                self.send_error_response("土日は営業していません。平日（月-金）のみ予測を提供しています。")
                return
            
            if tomorrow.weekday() >= 5:  # 明日が土日の場合
                # 今日のみの予測を提供
                tomorrow = None
            
            # モデルをロード
            try:
                model_data = self.load_ml_models()
                if not model_data:
                    self.send_error_response("ML予測モデルをロードできませんでした。")
                    return
            except Exception as e:
                self.send_error_response(f"モデルロードエラー: {str(e)}")
                return
            
            # 今日の予測
            today_weekday = today.weekday()  # 0: 月曜日, 1: 火曜日, ..., 4: 金曜日
            today_prediction = self.generate_hourly_predictions_with_ml(model_data, today_weekday, 0, is_today=True)
            
            # URLパスからAPIを判断
            path = self.path
            if path.startswith('/ml/predict'):
                # フロントエンド用のフォーマット（/ml/predict?day_of_week=3 のようなリクエスト）
                import urllib.parse
                params = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
                day_of_week = int(params.get('day_of_week', [today_weekday])[0])
                
                prediction = self.predict_with_ml_model(model_data, day_of_week)
                
                response_data = {
                    "success": True,
                    "day_of_week": day_of_week,
                    "weekday_name": ["月", "火", "水", "木", "金"][day_of_week] if 0 <= day_of_week < 5 else "不明",
                    "predictions": {
                        "density_rate": prediction["density_rate"],
                        "occupied_seats": prediction["occupied_seats"]
                    },
                    "message": "機械学習モデルによる予測"
                }
                
                self.send_success_response(response_data)
                return
            elif path.startswith('/analysis/weekday_analysis'):
                # 曜日別分析用のフォーマット
                # 曜日ごとの予測を準備
                weekday_analysis = {}
                daily_predictions = {}
                
                for weekday in range(5):  # 月〜金
                    prediction = self.predict_with_ml_model(model_data, weekday)
                    weekday_name = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"][weekday]
                    
                    daily_predictions[weekday_name] = {
                        "レコード数": 55,  # 訓練データ数（固定）
                        "predictions": {
                            "density_rate": prediction["density_rate"],
                            "occupied_seats": prediction["occupied_seats"]
                        }
                    }
                
                response_data = {
                    "success": True,
                    "data": {
                        "detailed_stats": {},  # フロントエンドの期待する形式に合わせて空にしておく
                        "daily_predictions": daily_predictions,
                        "summary": {  # 簡易サマリー
                            "全体": {
                                "record_count": 55,
                                "density_rate_mean": sum([pred["predictions"]["density_rate"] for pred in daily_predictions.values()]) / 5,
                                "occupied_seats_mean": sum([pred["predictions"]["occupied_seats"] for pred in daily_predictions.values()]) / 5
                            }
                        }
                    },
                    "message": "機械学習モデルによる曜日別予測"
                }
                
                self.send_success_response(response_data)
                return
            else:
                # 従来の形式（レスポンス構造変更なし）
                response_data = {
                    "success": True,
                    "timestamp": now.isoformat(),
                    "data": {
                        "today": {
                            "date": today.isoformat(),
                            "day_of_week": ["月", "火", "水", "木", "金"][today.weekday()],
                            "prediction": today_prediction
                        }
                    },
                    "metadata": {
                        "model_version": model_data.get("version", "1.0.0"),
                        "last_updated": now.isoformat(),
                        "model_type": "gradient_boosting",
                        "features_used": ["day_of_week"],
                        "confidence": self.get_model_confidence(model_data),
                        "data_source": "ml_model",
                        "weekday_only": True
                    }
                }
                
                # 明日が平日の場合のみ明日の予測を追加
                if tomorrow is not None:
                    tomorrow_weekday = tomorrow.weekday()
                    tomorrow_prediction = self.generate_hourly_predictions_with_ml(model_data, tomorrow_weekday, 0, is_today=False)
                    
                    response_data["data"]["tomorrow"] = {
                        "date": tomorrow.isoformat(),
                        "day_of_week": ["月", "火", "水", "木", "金"][tomorrow.weekday()],
                        "prediction": tomorrow_prediction
                    }
                else:
                    response_data["data"]["tomorrow"] = {
                        "date": None,
                        "day_of_week": None,
                        "prediction": None,
                        "message": "明日は土日のため営業していません"
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
    
    def generate_hourly_predictions_with_ml(self, model_data, day_of_week, start_hour, is_today=True):
        """曜日別の予測を生成（機械学習モデル使用）"""
        # 基本の予測値（曜日ベース）を取得
        base_prediction = self.predict_with_ml_model(model_data, day_of_week)
        
        if base_prediction["density_rate"] is None or base_prediction["occupied_seats"] is None:
            # 予測エラーの場合
            return {
                "occupancy_rate": None,
                "available_seats": None,
                "status": "error",
                "confidence": "none",
                "message": "予測モデルがエラーを返しました"
            }
        
        # 密度率から占有率を計算
        density_rate = base_prediction["density_rate"]
        occupied_seats = base_prediction["occupied_seats"]
        
        # 占有率を0-1の範囲に正規化
        occupancy_rate = density_rate / 100.0
        available_seats = 100 - int(occupied_seats)
        
        # 混雑状況の判定
        status = "busy" if occupancy_rate > 0.8 else "moderate" if occupancy_rate > 0.5 else "available"
        
        # 信頼度
        confidence = self.get_model_confidence(model_data)
        
        # パフォーマンス情報
        model_performance = model_data.get("model_performance", {})
        density_rmse = model_performance.get("density", {}).get("test_rmse", 0)
        seats_rmse = model_performance.get("seats", {}).get("test_rmse", 0)
        
        return {
            "occupancy_rate": round(occupancy_rate, 2),
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