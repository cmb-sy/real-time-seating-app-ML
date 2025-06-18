"""
機械学習モデルモジュール
Optunaを使ったハイパーパラメータ最適化とアンサンブル予測機能
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import optuna
import joblib
import logging
from typing import Dict, Tuple, List, Any
from data_processor import MLDataProcessor
import os
import sys
sys.path.append('src/ml')

logger = logging.getLogger(__name__)

class MLPredictor:
    """機械学習予測クラス（アンサンブル学習対応）"""
    
    def __init__(self):
        """初期化"""
        self.models = {}
        self.ensemble_models = {}
        self.best_params = {}
        self.model_performance = {}
        self.data_processor = MLDataProcessor()
        
        # 使用するモデル一覧（精度向上のためXGBoostを追加検討）
        self.model_types = {
            'random_forest': RandomForestRegressor,
            'gradient_boosting': GradientBoostingRegressor,
            'ridge': Ridge,
            'elastic_net': ElasticNet
        }
    
    def _create_model_with_params(self, model_name: str, params: dict):
        """パラメータでモデルを作成"""
        clean_params = params.copy()
        clean_params.pop('model_type', None)
        
        if model_name == 'random_forest':
            return RandomForestRegressor(**clean_params, random_state=42, n_jobs=-1)
        elif model_name == 'gradient_boosting':
            return GradientBoostingRegressor(**clean_params, random_state=42)
        elif model_name == 'ridge':
            return Ridge(**clean_params)
        elif model_name == 'elastic_net':
            return ElasticNet(**clean_params, random_state=42)
        else:
            raise ValueError(f"未対応のモデルタイプ: {model_name}")
    
    def objective_function(self, trial, X_train, y_train, X_val, y_val):
        """
        統一された最適化目的関数（精度向上のため改良）
        
        Args:
            trial: Optunaトライアル
            X_train, y_train: 訓練データ
            X_val, y_val: 検証データ
            
        Returns:
            float: 検証スコア（RMSE + 正則化項）
        """
        # モデルタイプを選択
        model_name = trial.suggest_categorical('model_type', 
                                              ['random_forest', 'gradient_boosting', 'ridge', 'elastic_net'])
        
        # より厳密なハイパーパラメータ範囲で精度向上
        if model_name == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=trial.suggest_int('n_estimators', 100, 500),  # 範囲拡大
                max_depth=trial.suggest_int('max_depth', 3, 20),  # 範囲拡大
                min_samples_split=trial.suggest_int('min_samples_split', 2, 15),  
                min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 8),  
                max_features=trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.3, 0.5, 0.8]),  
                bootstrap=trial.suggest_categorical('bootstrap', [True, False]),  # 新規追加
                random_state=42,
                n_jobs=-1
            )
        elif model_name == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=trial.suggest_int('n_estimators', 100, 500),  # 範囲拡大
                max_depth=trial.suggest_int('max_depth', 3, 10),  
                learning_rate=trial.suggest_float('learning_rate', 0.005, 0.3, log=True),  # log scaleで最適化
                subsample=trial.suggest_float('subsample', 0.5, 1.0),  
                max_features=trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.3, 0.5, 0.8]),
                validation_fraction=0.15,  # 検証データ割合を調整
                n_iter_no_change=15,  # 早期停止を緩和
                random_state=42
            )
        elif model_name == 'ridge':
            model = Ridge(
                alpha=trial.suggest_float('alpha', 1e-3, 1e3, log=True),  # 範囲拡大
                max_iter=trial.suggest_int('max_iter', 2000, 8000),  # 範囲拡大
                solver=trial.suggest_categorical('solver', ['auto', 'svd', 'cholesky', 'lsqr'])  # ソルバー最適化
            )
        elif model_name == 'elastic_net':
            model = ElasticNet(
                alpha=trial.suggest_float('alpha', 1e-3, 1e3, log=True),  # 範囲拡大
                l1_ratio=trial.suggest_float('l1_ratio', 0.01, 0.99),  # 範囲拡大
                max_iter=trial.suggest_int('max_iter', 2000, 10000),  # 範囲拡大
                selection=trial.suggest_categorical('selection', ['cyclic', 'random']),  # 新規追加
                random_state=42
            )
        
        # モデル訓練（線形モデルは統一スケーラーを使用）
        if model_name in ['ridge', 'elastic_net']:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_val_scaled)
            y_train_pred = model.predict(X_train_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            y_train_pred = model.predict(X_train)
        
        # 評価指標計算
        val_rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        
        # 過学習ペナルティ（より厳密に）
        overfitting_penalty = max(0, (train_rmse - val_rmse) / (val_rmse + 1e-8)) * 0.2
        
        # 予測値の妥当性チェック（異常値ペナルティ）
        anomaly_penalty = 0
        if np.any(y_pred < 0) or np.any(y_pred > 200):  # 異常値検出
            anomaly_penalty = 0.5
        
        return val_rmse + overfitting_penalty + anomaly_penalty
    
    def optimize_hyperparameters(self, target_type: str = 'both', n_trials: int = 200) -> Dict:
        """
        Optunaを使ってハイパーパラメータを最適化
        
        Args:
            target_type: 'density', 'seats', 'both'
            n_trials: 最適化試行回数
            
        Returns:
            Dict: 最適化結果
        """
        logger.info("高精度ハイパーパラメータ最適化を開始...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_processor.prepare_ml_data()
        
        results = {}
        
        if target_type in ['density', 'both']:
            logger.info("密度率予測モデルの最適化中...")
            
            # 分割
            X_train, X_val, y_train_density, y_val_density = train_test_split(
                X, y_density, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Optuna最適化
            study_density = optuna.create_study(
                direction='minimize',
                sampler=optuna.samplers.TPESampler(seed=42),  # TPEサンプラーで精度向上
                pruner=optuna.pruners.MedianPruner(n_startup_trials=20)  # 早期プルーニング
            )
            study_density.optimize(
                lambda trial: self.objective_function(trial, X_train, y_train_density, X_val, y_val_density),
                n_trials=n_trials,
                timeout=3600  # 1時間のタイムアウト
            )
            
            results['density'] = {
                'best_params': study_density.best_params,
                'best_score': study_density.best_value,
                'n_trials': len(study_density.trials),
                'best_trial': study_density.best_trial.number
            }
            
            self.best_params['density'] = study_density.best_params
            logger.info(f"密度率予測最適化完了 - Best RMSE: {study_density.best_value:.4f}")
        
        if target_type in ['seats', 'both']:
            logger.info("占有座席数予測モデルの最適化中...")
            
            X_train, X_val, y_train_seats, y_val_seats = train_test_split(
                X, y_seats, test_size=0.2, random_state=42, shuffle=True
            )
            
            study_seats = optuna.create_study(
                direction='minimize',
                sampler=optuna.samplers.TPESampler(seed=42),
                pruner=optuna.pruners.MedianPruner(n_startup_trials=20)
            )
            study_seats.optimize(
                lambda trial: self.objective_function(trial, X_train, y_train_seats, X_val, y_val_seats),
                n_trials=n_trials,
                timeout=3600
            )
            
            results['seats'] = {
                'best_params': study_seats.best_params,
                'best_score': study_seats.best_value,
                'n_trials': len(study_seats.trials),
                'best_trial': study_seats.best_trial.number
            }
            
            self.best_params['seats'] = study_seats.best_params
            logger.info(f"占有座席数予測最適化完了 - Best RMSE: {study_seats.best_value:.4f}")
        
        return results
    
    def train_best_models(self) -> Dict:
        """
        最適なパラメータでモデルを訓練（アンサンブル学習対応）
            
        Returns:
            Dict: モデル性能評価結果
        """
        logger.info("アンサンブルモデルを最適パラメータで訓練中...")
        
        # データ準備
        ml_data, X, y_density, y_seats = self.data_processor.prepare_ml_data()
        
        results = {}
        
        # 密度率予測モデル
        if 'density' in self.best_params:
            try:
                model_params = self.best_params['density'].copy()
                model_type = model_params.pop('model_type')
                
                # 基本モデル作成
                base_model = self._create_model_with_params(model_type, self.best_params['density'])
                
                # アンサンブルモデルのコンポーネント作成（多様性のため異なるモデル）
                rf_model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42)
                gb_model = GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42)
                ridge_model = Pipeline([('scaler', StandardScaler()), ('ridge', Ridge(alpha=1.0))])
                
                # アンサンブルモデル作成
                ensemble_model = VotingRegressor([
                    ('best', base_model),
                    ('rf', rf_model),
                    ('gb', gb_model),
                    ('ridge', ridge_model)
                ], weights=[2, 1, 1, 1])  # 最適モデルに重み付け
                
                # 訓練・テストデータ分割
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_density, test_size=0.2, random_state=42, shuffle=True
                )
                
                # モデル訓練
                ensemble_model.fit(X_train, y_train)
                y_pred = ensemble_model.predict(X_test)
                
                # 評価指標計算
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # クロスバリデーション
                kfold = KFold(n_splits=10, shuffle=True, random_state=42)
                cv_scores = cross_val_score(ensemble_model, X_train, y_train, cv=kfold, scoring='neg_mean_squared_error')
                cv_rmse = np.sqrt(-cv_scores.mean())
                cv_std = np.sqrt(-cv_scores).std()
                
                # 過学習判定
                overfitting_detected = (rmse - cv_rmse) > cv_std * 1.5
                
                if overfitting_detected:
                    logger.warning(f"密度率予測モデルで過学習の可能性があります。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
                else:
                    logger.info(f"密度率予測モデルの汎化性能は良好です。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
                
                results['density'] = {
                    'model_type': f'{model_type}_ensemble',
                    'test_rmse': rmse,
                    'test_mae': mae,
                    'test_r2': r2,
                    'cv_rmse': cv_rmse,
                    'cv_std': cv_std,
                    'overfitting_detected': overfitting_detected
                }
                
                self.ensemble_models['density'] = ensemble_model
                logger.info(f"密度率予測アンサンブルモデル訓練完了 - Test RMSE: {rmse:.4f}, R²: {r2:.4f}")
                
            except Exception as e:
                logger.error(f"密度率予測モデルの訓練中にエラーが発生しました: {str(e)}")
                results['density'] = {'error': str(e)}
        
        # 占有座席数予測モデル
        if 'seats' in self.best_params:
            try:
                model_params = self.best_params['seats'].copy()
                model_type = model_params.pop('model_type')
                
                # 基本モデル作成
                base_model = self._create_model_with_params(model_type, self.best_params['seats'])
                
                # アンサンブルモデル作成
                rf_model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42)
                gb_model = GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42)
                ridge_model = Pipeline([('scaler', StandardScaler()), ('ridge', Ridge(alpha=1.0))])
                
                ensemble_model = VotingRegressor([
                    ('best', base_model),
                    ('rf', rf_model),
                    ('gb', gb_model),
                    ('ridge', ridge_model)
                ], weights=[2, 1, 1, 1])
                
                # 訓練・テストデータ分割
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_seats, test_size=0.2, random_state=42, shuffle=True
                )
                
                # モデル訓練
                ensemble_model.fit(X_train, y_train)
                y_pred = ensemble_model.predict(X_test)
                
                # 評価指標計算
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # クロスバリデーション
                kfold = KFold(n_splits=10, shuffle=True, random_state=42)
                cv_scores = cross_val_score(ensemble_model, X_train, y_train, cv=kfold, scoring='neg_mean_squared_error')
                cv_rmse = np.sqrt(-cv_scores.mean())
                cv_std = np.sqrt(-cv_scores).std()
                
                # 過学習判定
                overfitting_detected = (rmse - cv_rmse) > cv_std * 1.5
                
                if overfitting_detected:
                    logger.warning(f"占有座席数予測モデルで過学習の可能性があります。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
                else:
                    logger.info(f"占有座席数予測モデルの汎化性能は良好です。Test RMSE: {rmse:.4f}, CV RMSE: {cv_rmse:.4f}")
                
                results['seats'] = {
                    'model_type': f'{model_type}_ensemble',
                    'test_rmse': rmse,
                    'test_mae': mae,
                    'test_r2': r2,
                    'cv_rmse': cv_rmse,
                    'cv_std': cv_std,
                    'overfitting_detected': overfitting_detected
                }
                
                self.ensemble_models['seats'] = ensemble_model
                logger.info(f"占有座席数予測アンサンブルモデル訓練完了 - Test RMSE: {rmse:.4f}, R²: {r2:.4f}")
                
            except Exception as e:
                logger.error(f"占有座席数予測モデルの訓練中にエラーが発生しました: {str(e)}")
                results['seats'] = {'error': str(e)}
        
        self.model_performance = results
        return results
    
    def predict(self, day_of_week: int) -> Dict:
        """
        曜日から密度率と占有座席数を予測（アンサンブルモデル使用）
        
        Args:
            day_of_week: 曜日（0-4: 月-金）
            
        Returns:
            Dict: 予測結果
        """
        # prediction.pyのPredictionServiceを使用して予測を行う
        from utils.prediction import PredictionService
        
        prediction_service = PredictionService()
        result = prediction_service.predict_with_models(day_of_week)
        
        # PredictionServiceの戻り値形式をMLPredictorの戻り値形式に変換
        predictions = {
            'density_rate': result['occupancy_rate'] * 100,  # 0-1のスケールを0-100に変換
            'occupied_seats': result['occupied_seats']
        }
        
        return predictions
    
    def save_models(self, model_dir: str = 'utils/joblib') -> Dict[str, str]:
        """
        訓練済みモデルと性能情報を保存
        
        Args:
            model_dir: 保存ディレクトリ
            
        Returns:
            Dict[str, str]: 保存されたファイルパス
        """
        os.makedirs(model_dir, exist_ok=True)
        saved_files = {}
        
        # アンサンブルモデル保存（実際に使用されるもののみ）
        for target, model in self.ensemble_models.items():
            model_path = os.path.join(model_dir, f'{target}_model.joblib')
            joblib.dump(model, model_path)
            saved_files[f'{target}_model'] = model_path
        
        # モデル性能情報を保存
        if self.model_performance:
            performance_path = os.path.join(model_dir, 'model_performance.joblib')
            joblib.dump(self.model_performance, performance_path)
            saved_files['model_performance'] = performance_path
        
        logger.info(f"アンサンブルモデルと性能情報を保存しました: {saved_files}")
        return saved_files
    
    def load_models(self, model_dir: str = 'utils/joblib') -> bool:
        """
        保存済みモデルと性能情報を読み込み
        
        Args:
            model_dir: モデルディレクトリ
            
        Returns:
            bool: 読み込み成功可否
        """
        try:
            # アンサンブルモデル読み込み（実際に使用されるもののみ）
            for target in ['density', 'seats']:
                model_path = os.path.join(model_dir, f'{target}_model.joblib')
                if os.path.exists(model_path):
                    self.ensemble_models[target] = joblib.load(model_path)
                else:
                    logger.warning(f"モデルファイルが見つかりません: {model_path}")
                    return False
            
            # モデル性能情報を読み込み（存在する場合）
            performance_path = os.path.join(model_dir, 'model_performance.joblib')
            if os.path.exists(performance_path):
                self.model_performance = joblib.load(performance_path)
                logger.info("モデル性能情報を読み込みました")
            else:
                logger.warning("モデル性能情報ファイルが見つかりません")
                self.model_performance = {}
            
            logger.info("アンサンブルモデルと性能情報の読み込みが完了しました")
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
        return {
            'available_models': list(self.ensemble_models.keys()),
            'best_parameters': self.best_params,
            'model_performance': self.model_performance,
            'model_type': 'ensemble_learning',
            'feature_names': self.data_processor.get_feature_columns() if hasattr(self.data_processor, 'get_feature_columns') else ['day_of_week'],
            'usage_info': {
                'prediction_range': {
                    'density_rate': {'min': 0.0, 'max': 100.0, 'unit': '%'},
                    'occupied_seats': {'min': 0, 'max': 8, 'unit': '席'}
                },
                'ensemble_components': ['best_model', 'random_forest', 'gradient_boosting', 'ridge_regression'],
                'optimization_method': 'TPE_sampling_with_pruning'
            }
        }