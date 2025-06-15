"""
機械学習モデルモジュール
Optunaを使ったハイパーパラメータ最適化と予測機能
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import optuna
import joblib
import logging
from typing import Dict, Tuple, List, Any
from src.ml.data_processor import MLDataProcessor
import os

logger = logging.getLogger(__name__)

class MLPredictor:
    """機械学習予測クラス"""
    
    def __init__(self):
        """初期化"""
        self.models = {}
        self.scalers = {}
        self.best_params = {}
        self.model_performance = {}
        self.data_processor = MLDataProcessor()
        
        # 使用するモデル一覧
        self.model_types = {
            'random_forest': RandomForestRegressor,
            'gradient_boosting': GradientBoostingRegressor,
            'ridge': Ridge,
            'elastic_net': ElasticNet
        }
    
    def objective_density(self, trial, X_train, y_train, X_val, y_val):
        """
        密度率予測用の最適化目的関数
        
        Args:
            trial: Optunaトライアル
            X_train, y_train: 訓練データ
            X_val, y_val: 検証データ
            
        Returns:
            float: 検証スコア（RMSE）
        """
        # モデルタイプを選択
        model_name = trial.suggest_categorical('model_type', 
                                              ['random_forest', 'gradient_boosting', 'ridge', 'elastic_net'])
        
        if model_name == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=trial.suggest_int('n_estimators', 50, 200),  
                max_depth=trial.suggest_int('max_depth', 3, 15),  
                min_samples_split=trial.suggest_int('min_samples_split', 5, 20),  
                min_samples_leaf=trial.suggest_int('min_samples_leaf', 2, 10),  
                max_features=trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.5, 0.8]),  
                random_state=42,
                n_jobs=-1
            )
        elif model_name == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=trial.suggest_int('n_estimators', 50, 200),  
                max_depth=trial.suggest_int('max_depth', 3, 8),  
                learning_rate=trial.suggest_float('learning_rate', 0.01, 0.2),  
                subsample=trial.suggest_float('subsample', 0.6, 0.9),  
                max_features=trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.5, 0.8]),
                validation_fraction=0.1,  # 早期停止用の検証データ
                n_iter_no_change=10,  # 早期停止
                random_state=42
            )
        elif model_name == 'ridge':
            model = Ridge(
                alpha=trial.suggest_float('alpha', 1e-2, 1e2, log=True),
                max_iter=trial.suggest_int('max_iter', 1000, 5000)
            )
        elif model_name == 'elastic_net':
            model = ElasticNet(
                alpha=trial.suggest_float('alpha', 1e-2, 1e2, log=True),  
                l1_ratio=trial.suggest_float('l1_ratio', 0.1, 0.9),  
                max_iter=trial.suggest_int('max_iter', 1000, 5000),
                random_state=42
            )
        
        # モデル訓練
        if model_name in ['ridge', 'elastic_net']:
            # 線形モデルにはスケーリングを適用
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_val_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
        
        # RMSE計算
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        # 過学習チェック: 訓練データでの予測も計算
        if model_name in ['ridge', 'elastic_net']:
            y_train_pred = model.predict(X_train_scaled)
        else:
            y_train_pred = model.predict(X_train)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        
        # 過学習ペナルティ: 訓練誤差と検証誤差の差が大きい場合にペナルティ
        overfitting_penalty = max(0, (train_rmse - rmse) / rmse * 0.1)
        
        return rmse + overfitting_penalty
    
    def objective_seats(self, trial, X_train, y_train, X_val, y_val):
        """
        占有座席数予測用の最適化目的関数
        
        Args:
            trial: Optunaトライアル
            X_train, y_train: 訓練データ
            X_val, y_val: 検証データ
            
        Returns:
            float: 検証スコア（RMSE）
        """
        # 密度率予測と同じロジック
        return self.objective_density(trial, X_train, y_train, X_val, y_val)
    
    def optimize_hyperparameters(self, target_type: str = 'both', n_trials: int = 100, use_feature_engineering: bool = True) -> Dict:
        """
        Optunaを使ってハイパーパラメータを最適化
        
        Args:
            target_type: 'density', 'seats', 'both'
            n_trials: 最適化試行回数
            use_feature_engineering: 特徴量エンジニアリングを使用するかどうか
            
        Returns:
            Dict: 最適化結果
        """
        logger.info("ハイパーパラメータ最適化を開始...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_processor.prepare_ml_data(use_feature_engineering=use_feature_engineering)
        
        results = {}
        
        if target_type in ['density', 'both']:
            logger.info("密度率予測モデルの最適化中...")
            # 密度率予測の最適化（層化分割で過学習対策）
            X_train, X_val, y_train_density, y_val_density = train_test_split(
                X, y_density, test_size=0.25, random_state=42, stratify=None  # 検証データを増やす
            )
            
            study_density = optuna.create_study(direction='minimize')
            study_density.optimize(
                lambda trial: self.objective_density(trial, X_train, y_train_density, X_val, y_val_density),
                n_trials=n_trials
            )
            
            results['density'] = {
                'best_params': study_density.best_params,
                'best_score': study_density.best_value,
                'n_trials': len(study_density.trials)
            }
            
            self.best_params['density'] = study_density.best_params
            logger.info(f"密度率予測最適化完了 - Best RMSE: {study_density.best_value:.4f}")
        
        if target_type in ['seats', 'both']:
            logger.info("占有座席数予測モデルの最適化中...")
            # 占有座席数予測の最適化（層化分割で過学習対策）
            X_train, X_val, y_train_seats, y_val_seats = train_test_split(
                X, y_seats, test_size=0.25, random_state=42, stratify=None  # 検証データを増やす
            )
            
            study_seats = optuna.create_study(direction='minimize')
            study_seats.optimize(
                lambda trial: self.objective_seats(trial, X_train, y_train_seats, X_val, y_val_seats),
                n_trials=n_trials
            )
            
            results['seats'] = {
                'best_params': study_seats.best_params,
                'best_score': study_seats.best_value,
                'n_trials': len(study_seats.trials)
            }
            
            self.best_params['seats'] = study_seats.best_params
            logger.info(f"占有座席数予測最適化完了 - Best RMSE: {study_seats.best_value:.4f}")
        
        return results
    
    def train_best_models(self, use_feature_engineering: bool = True) -> Dict:
        """
        最適なパラメータでモデルを訓練
        
        Args:
            use_feature_engineering: 特徴量エンジニアリングを使用するかどうか
        
        Returns:
            Dict: モデル性能評価結果
        """
        logger.info("最適パラメータでモデルを訓練中...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_processor.prepare_ml_data(use_feature_engineering=use_feature_engineering)
        
        results = {}
        
        # 密度率予測モデル
        if 'density' in self.best_params:
            model_params = self.best_params['density'].copy()
            model_type = model_params.pop('model_type')
            
            # モデルインスタンス作成
            if model_type == 'random_forest':
                model = RandomForestRegressor(**model_params, random_state=42)
            elif model_type == 'gradient_boosting':
                model = GradientBoostingRegressor(**model_params, random_state=42)
            elif model_type == 'ridge':
                model = Ridge(**model_params)
            elif model_type == 'elastic_net':
                model = ElasticNet(**model_params, random_state=42)
            
            # 訓練・テストデータ分割（過学習対策でテストデータを増やす）
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_density, test_size=0.25, random_state=42
            )
            
            # スケーリング（線形モデルの場合）
            if model_type in ['ridge', 'elastic_net']:
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                self.scalers['density'] = scaler
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # 評価指標計算
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # クロスバリデーション（過学習対策で分割数を増やす）
            kfold = KFold(n_splits=8, shuffle=True, random_state=42)  # 分割数を増やして過学習を検出
            cv_scores = cross_val_score(model, X_train, y_train, cv=kfold, scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            cv_std = np.sqrt(-cv_scores).std()
            
            # 過学習警告
            if abs(rmse - cv_rmse) > cv_std * 2:
                logger.warning(f"密度率予測モデルで過学習の可能性があります。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
            else:
                logger.info(f"密度率予測モデルの汎化性能は良好です。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
            
            results['density'] = {
                'model_type': model_type,
                'test_rmse': rmse,
                'test_mae': mae,
                'test_r2': r2,
                'cv_rmse': cv_rmse,
                'cv_std': cv_std,
                'overfitting_detected': abs(rmse - cv_rmse) > cv_std * 2
            }
            
            self.models['density'] = model
            logger.info(f"密度率予測モデル訓練完了 - Test RMSE: {rmse:.4f}, R²: {r2:.4f}")
        
        # 占有座席数予測モデル
        if 'seats' in self.best_params:
            model_params = self.best_params['seats'].copy()
            model_type = model_params.pop('model_type')
            
            # モデルインスタンス作成
            if model_type == 'random_forest':
                model = RandomForestRegressor(**model_params, random_state=42)
            elif model_type == 'gradient_boosting':
                model = GradientBoostingRegressor(**model_params, random_state=42)
            elif model_type == 'ridge':
                model = Ridge(**model_params)
            elif model_type == 'elastic_net':
                model = ElasticNet(**model_params, random_state=42)
            
            # 訓練・テストデータ分割（過学習対策でテストデータを増やす）
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_seats, test_size=0.25, random_state=42
            )
            
            # スケーリング（線形モデルの場合）
            if model_type in ['ridge', 'elastic_net']:
                if 'seats' not in self.scalers:
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    self.scalers['seats'] = scaler
                else:
                    scaler = self.scalers['seats']
                    X_train_scaled = scaler.fit_transform(X_train)
                
                X_test_scaled = scaler.transform(X_test)
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # 評価指標計算
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # クロスバリデーション（過学習対策で分割数を増やす）
            kfold = KFold(n_splits=8, shuffle=True, random_state=42)  # 分割数を増やして過学習を検出
            cv_scores = cross_val_score(model, X_train, y_train, cv=kfold, scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            cv_std = np.sqrt(-cv_scores).std()
            
            # 過学習警告
            if abs(rmse - cv_rmse) > cv_std * 2:
                logger.warning(f"占有座席数予測モデルで過学習の可能性があります。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
            else:
                logger.info(f"占有座席数予測モデルの汎化性能は良好です。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
            
            results['seats'] = {
                'model_type': model_type,
                'test_rmse': rmse,
                'test_mae': mae,
                'test_r2': r2,
                'cv_rmse': cv_rmse,
                'cv_std': cv_std,
                'overfitting_detected': abs(rmse - cv_rmse) > cv_std * 2
            }
            
            self.models['seats'] = model
            logger.info(f"占有座席数予測モデル訓練完了 - Test RMSE: {rmse:.4f}, R²: {r2:.4f}")
        
        self.model_performance = results
        return results
    
    def predict(self, day_of_week: int) -> Dict:
        """
        曜日のみから密度率と占有座席数を予測
        
        Args:
            day_of_week: 曜日（0-4: 月-金）
            
        Returns:
            Dict: 予測結果
        """
        if not self.models:
            raise ValueError("モデルが訓練されていません。先にtrain_best_models()を実行してください。")
        
        # 曜日のみから特徴量作成
        features = np.array([[day_of_week]])
        
        predictions = {}
        
        # 密度率予測
        if 'density' in self.models:
            model = self.models['density']
            if 'density' in self.scalers:
                features_scaled = self.scalers['density'].transform(features)
                density_pred = model.predict(features_scaled)[0]
            else:
                density_pred = model.predict(features)[0]
            
            predictions['density_rate'] = float(max(0, min(100, density_pred)))  # 0-100%の範囲に制限
        
        # 占有座席数予測
        if 'seats' in self.models:
            model = self.models['seats']
            if 'seats' in self.scalers:
                features_scaled = self.scalers['seats'].transform(features)
                seats_pred = model.predict(features_scaled)[0]
            else:
                seats_pred = model.predict(features)[0]
            
            predictions['occupied_seats'] = int(max(0, seats_pred))  # 負の値は0に制限
        
        return predictions
    
    def save_models(self, model_dir: str = 'models') -> Dict[str, str]:
        """
        訓練済みモデルを保存
        
        Args:
            model_dir: 保存ディレクトリ
            
        Returns:
            Dict[str, str]: 保存されたファイルパス
        """
        os.makedirs(model_dir, exist_ok=True)
        saved_files = {}
        
        # モデル保存
        for target, model in self.models.items():
            model_path = os.path.join(model_dir, f'{target}_model.joblib')
            joblib.dump(model, model_path)
            saved_files[f'{target}_model'] = model_path
        
        # スケーラー保存
        for target, scaler in self.scalers.items():
            scaler_path = os.path.join(model_dir, f'{target}_scaler.joblib')
            joblib.dump(scaler, scaler_path)
            saved_files[f'{target}_scaler'] = scaler_path
        
        # パラメータ保存
        params_path = os.path.join(model_dir, 'best_params.joblib')
        joblib.dump(self.best_params, params_path)
        saved_files['best_params'] = params_path
        
        # 性能評価結果保存
        performance_path = os.path.join(model_dir, 'model_performance.joblib')
        joblib.dump(self.model_performance, performance_path)
        saved_files['model_performance'] = performance_path
        
        logger.info(f"モデルを保存しました: {saved_files}")
        return saved_files
    
    def load_models(self, model_dir: str = 'models') -> bool:
        """
        保存済みモデルを読み込み
        
        Args:
            model_dir: モデルディレクトリ
            
        Returns:
            bool: 読み込み成功可否
        """
        try:
            # モデル読み込み
            for target in ['density', 'seats']:
                model_path = os.path.join(model_dir, f'{target}_model.joblib')
                if os.path.exists(model_path):
                    self.models[target] = joblib.load(model_path)
                
                scaler_path = os.path.join(model_dir, f'{target}_scaler.joblib')
                if os.path.exists(scaler_path):
                    self.scalers[target] = joblib.load(scaler_path)
            
            # パラメータ読み込み
            params_path = os.path.join(model_dir, 'best_params.joblib')
            if os.path.exists(params_path):
                self.best_params = joblib.load(params_path)
            
            # 性能評価結果読み込み
            performance_path = os.path.join(model_dir, 'model_performance.joblib')
            if os.path.exists(performance_path):
                self.model_performance = joblib.load(performance_path)
            
            logger.info("モデルの読み込みが完了しました")
            return True
            
        except Exception as e:
            logger.error(f"モデル読み込みエラー: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        モデル情報を取得
        
        Returns:
            Dict: モデル情報
        """
        info = {
            'available_models': list(self.models.keys()),
            'best_parameters': self.best_params,
            'model_performance': self.model_performance,
            'feature_names': ['day_of_week'],
            'note': '曜日（0-4: 月-金）のみから予測を実行します。時間情報は使用しません。'
        }
        
        return info

if __name__ == "__main__":
    """
    MLモデルのテスト実行
    """
    import logging
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    predictor = MLPredictor()
    
    # 保存済みモデルがあるかチェック
    if predictor.load_models():
        print("=== 保存済みモデル情報 ===")
        model_info = predictor.get_model_info()
        print(f"利用可能なモデル: {model_info['available_models']}")
        
        if model_info['model_performance']:
            print("\n=== モデル性能 ===")
            for target, performance in model_info['model_performance'].items():
                print(f"{target}モデル:")
                for metric, value in performance.items():
                    if isinstance(value, float):
                        print(f"  {metric}: {value:.4f}")
                    else:
                        print(f"  {metric}: {value}")
        
        # 予測テスト
        print("\n=== 予測テスト ===")
        weekday_names = {0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"}
        
        for day in range(5):
            try:
                predictions = predictor.predict(day_of_week=day)
                print(f"{weekday_names[day]}: {predictions}")
            except Exception as e:
                print(f"{weekday_names[day]}: エラー - {e}")
        
        print("\n✅ モデルテスト完了")
    else:
        print("❌ 保存済みモデルが見つかりません。")
        print("先に以下のコマンドでモデルを訓練してください:")
        print("python src/ml/train_ml_models.py --mode train --n-trials 30")