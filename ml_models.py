"""
機械学習モデルモジュール
Optunaを使ったハイパーパラメータ最適化と予測機能
アンサンブル学習と高度な特徴量エンジニアリング対応
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
import optuna
import joblib
import logging
from typing import Dict, Tuple, List, Any
from data_analysis import DataAnalyzer
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
        self.data_analyzer = DataAnalyzer()
        
        # 使用するモデル一覧（アンサンブル学習対応）
        self.model_types = {
            'random_forest': RandomForestRegressor,
            'gradient_boosting': GradientBoostingRegressor,
            'ridge': Ridge,
            'elastic_net': ElasticNet,
            'svr': SVR
        }
        
        # 特徴量エンジニアリング用
        self.poly_features = None
        self.use_polynomial = False
    
    def create_advanced_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        高度な特徴量エンジニアリング
        
        Args:
            X: 基本特徴量データ
            
        Returns:
            pd.DataFrame: 拡張された特徴量データ
        """
        X_enhanced = X.copy()
        
        # 時間ベースの特徴量
        if 'hour' in X_enhanced.columns:
            # 時間帯カテゴリ
            X_enhanced['time_category'] = pd.cut(
                X_enhanced['hour'], 
                bins=[0, 6, 12, 18, 24], 
                labels=['深夜早朝', '午前', '午後', '夜間'],
                include_lowest=True
            ).cat.codes
            
            # ピーク時間フラグ
            X_enhanced['is_peak_hour'] = X_enhanced['hour'].apply(
                lambda x: 1 if x in [9, 10, 11, 12, 13, 14, 15, 16, 17] else 0
            )
        
        # 曜日ベースの特徴量
        if 'day_of_week' in X_enhanced.columns:
            # 週の前半・後半
            X_enhanced['week_half'] = X_enhanced['day_of_week'].apply(
                lambda x: 0 if x in [0, 1] else 1  # 0,1=前半, 2,3,4=後半
            )
            
        # 相互作用特徴量
        if 'hour' in X_enhanced.columns and 'day_of_week' in X_enhanced.columns:
            X_enhanced['hour_weekday_interaction'] = X_enhanced['hour'] * X_enhanced['day_of_week']
        
        return X_enhanced
    
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
                n_estimators=trial.suggest_int('n_estimators', 50, 300),
                max_depth=trial.suggest_int('max_depth', 3, 20),
                min_samples_split=trial.suggest_int('min_samples_split', 2, 10),
                min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 10),
                random_state=42
            )
        elif model_name == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=trial.suggest_int('n_estimators', 50, 300),
                max_depth=trial.suggest_int('max_depth', 3, 20),
                learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3),
                subsample=trial.suggest_float('subsample', 0.8, 1.0),
                random_state=42
            )
        elif model_name == 'ridge':
            model = Ridge(
                alpha=trial.suggest_float('alpha', 1e-3, 1e3, log=True)
            )
        elif model_name == 'elastic_net':
            model = ElasticNet(
                alpha=trial.suggest_float('alpha', 1e-3, 1e3, log=True),
                l1_ratio=trial.suggest_float('l1_ratio', 0.0, 1.0),
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
        return rmse
    
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
    
    def optimize_hyperparameters(self, target_type: str = 'both', n_trials: int = 100) -> Dict:
        """
        Optunaを使ってハイパーパラメータを最適化
        
        Args:
            target_type: 'density', 'seats', 'both'
            n_trials: 最適化試行回数
            
        Returns:
            Dict: 最適化結果
        """
        logger.info("ハイパーパラメータ最適化を開始...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_analyzer.prepare_ml_data()
        
        results = {}
        
        if target_type in ['density', 'both']:
            logger.info("密度率予測モデルの最適化中...")
            # 密度率予測の最適化
            X_train, X_val, y_train_density, y_val_density = train_test_split(
                X, y_density, test_size=0.2, random_state=42
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
            # 占有座席数予測の最適化
            X_train, X_val, y_train_seats, y_val_seats = train_test_split(
                X, y_seats, test_size=0.2, random_state=42
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
    
    def train_best_models(self) -> Dict:
        """
        最適なパラメータでモデルを訓練
        
        Returns:
            Dict: モデル性能評価結果
        """
        logger.info("最適パラメータでモデルを訓練中...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_analyzer.prepare_ml_data()
        
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
            
            # 訓練・テストデータ分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_density, test_size=0.2, random_state=42
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
            
            # クロスバリデーション
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            
            results['density'] = {
                'model_type': model_type,
                'test_rmse': rmse,
                'test_mae': mae,
                'test_r2': r2,
                'cv_rmse': cv_rmse,
                'cv_std': np.sqrt(-cv_scores).std()
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
            
            # 訓練・テストデータ分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_seats, test_size=0.2, random_state=42
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
            
            # クロスバリデーション
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            
            results['seats'] = {
                'model_type': model_type,
                'test_rmse': rmse,
                'test_mae': mae,
                'test_r2': r2,
                'cv_rmse': cv_rmse,
                'cv_std': np.sqrt(-cv_scores).std()
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
        
        # 曜日のみから特徴量作成（時間は除去）
        day_sin = np.sin(2 * np.pi * day_of_week / 7)
        day_cos = np.cos(2 * np.pi * day_of_week / 7)
        
        # 既存モデルとの互換性のため、時間関連特徴量を0で埋める
        # 注意: 再訓練時には時間特徴量を完全に除去することを推奨
        hour_sin = 0.0  # 時間情報を無効化
        hour_cos = 1.0  # 12時に相当する値で固定
        
        features = np.array([[day_of_week, 12, day_sin, day_cos, hour_sin, hour_cos]])
        
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
            'feature_names': ['day_of_week', 'day_of_week_sin', 'day_of_week_cos'],
            'note': '曜日（0-4: 月-金）のみから予測を実行します。時間情報は使用しません。'
        }
        
        return info 