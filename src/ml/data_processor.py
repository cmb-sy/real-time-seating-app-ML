#!/usr/bin/env python3

"""
- ML用データ準備
- 特徴量エンジニアリング
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
import sys
from supabase import create_client
from src.utils import config

logger = logging.getLogger(__name__)

class MLDataProcessor:
    """機械学習用データ処理クラス"""
    def __init__(self):
        self.df = None
        self.df_weekdays = None
        # Supabaseクライアント
        self.supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
    def load_data_from_supabase(self) -> pd.DataFrame:
        """
        Supabaseからデータを取得してDataFrameに変換
        
        Returns:
            pd.DataFrame: 取得したデータ
        """
        try:
            logger.info("Supabaseからデータを取得中...")
            response = self.supabase_client.table("density_history").select("*").execute()
            
            # DataFrameに変換
            self.df = pd.DataFrame(response.data)
            
            # データ型の変換（日付フォーマットが混在しているため、mixed形式で処理）
            self.df['created_at'] = pd.to_datetime(self.df['created_at'], format='mixed')
            self.df['density_rate'] = pd.to_numeric(self.df['density_rate'])
            self.df['occupied_seats'] = pd.to_numeric(self.df['occupied_seats'])
            self.df['day_of_week'] = pd.to_numeric(self.df['day_of_week'])
            
            # 平日データのみを抽出（0-4: 月-金）
            self.df_weekdays = self.df[self.df['day_of_week'].isin([0, 1, 2, 3, 4])].copy()
            
            logger.info(f"データ取得完了: 全体 {len(self.df)} 件, 平日 {len(self.df_weekdays)} 件")
            
            return self.df
            
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            raise
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量エンジニアリング
        
        Args:
            df: 元データ
            
        Returns:
            pd.DataFrame: 特徴量エンジニアリング後のデータ
        """
        logger.info("特徴量エンジニアリングを実行中...")
        
        feature_df = df.copy()
        
        # 2. 曜日関連特徴量
        feature_df['is_monday'] = (feature_df['day_of_week'] == 0).astype(int)
        feature_df['is_tuesday'] = (feature_df['day_of_week'] == 1).astype(int)
        feature_df['is_wednesday'] = (feature_df['day_of_week'] == 2).astype(int)
        feature_df['is_thursday'] = (feature_df['day_of_week'] == 3).astype(int)
        feature_df['is_friday'] = (feature_df['day_of_week'] == 4).astype(int)
        
        # 3. 週の前半・後半
        feature_df['is_early_week'] = (feature_df['day_of_week'] <= 2).astype(int)  # 月火水
        feature_df['is_late_week'] = (feature_df['day_of_week'] >= 3).astype(int)   # 木金
        
        # 6. 統計的特徴量（移動平均など）
        # 曜日別の移動平均（過去3回の同じ曜日の平均）
        for day in range(5):
            day_data = feature_df[feature_df['day_of_week'] == day].copy()
            if len(day_data) > 0:
                day_data = day_data.sort_values('created_at')
                day_data[f'density_ma3_day{day}'] = day_data['density_rate'].rolling(window=3, min_periods=1).mean()
                day_data[f'seats_ma3_day{day}'] = day_data['occupied_seats'].rolling(window=3, min_periods=1).mean()
                
                # 元のDataFrameに結合
                feature_df = feature_df.merge(
                    day_data[['id', f'density_ma3_day{day}', f'seats_ma3_day{day}']],
                    on='id', how='left'
                )
                
                # NaNを0で埋める
                feature_df[f'density_ma3_day{day}'] = feature_df[f'density_ma3_day{day}'].fillna(0)
                feature_df[f'seats_ma3_day{day}'] = feature_df[f'seats_ma3_day{day}'].fillna(0)
        
        # 7. 交互作用特徴量
        feature_df['density_seats_ratio'] = feature_df['density_rate'] / (feature_df['occupied_seats'] + 1)  # ゼロ除算回避
        
        # 8. ラグ特徴量（前回の値）
        feature_df = feature_df.sort_values(['day_of_week', 'created_at'])
        feature_df['prev_density'] = feature_df.groupby('day_of_week')['density_rate'].shift(1).fillna(0)
        feature_df['prev_seats'] = feature_df.groupby('day_of_week')['occupied_seats'].shift(1).fillna(0)
        
        # 9. 差分特徴量
        feature_df['density_diff'] = feature_df['density_rate'] - feature_df['prev_density']
        feature_df['seats_diff'] = feature_df['occupied_seats'] - feature_df['prev_seats']
        
        logger.info(f"特徴量エンジニアリング完了: {len(feature_df.columns)} 個の特徴量を生成")
        
        return feature_df
    
    def get_feature_columns(self) -> List[str]:
        """
        機械学習で使用する特徴量カラムのリストを取得
        
        Returns:
            List[str]: 特徴量カラム名のリスト
        """
        base_features = [   
            'day_of_week', 'density_seats_ratio',
            'prev_density', 'prev_seats', 'density_diff', 'seats_diff',
            'is_monday', 'is_tuesday', 'is_wednesday', 'is_thursday', 'is_friday',
            'is_early_week', 'is_late_week',
        ]
        
        # 移動平均特徴量を追加
        ma_features = []
        for day in range(5):
            ma_features.extend([f'density_ma3_day{day}', f'seats_ma3_day{day}'])
        
        return base_features + ma_features
    
    def prepare_ml_data(self, use_feature_engineering: bool = True) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
        """
        機械学習用のデータを準備
        
        Args:
            use_feature_engineering: 特徴量エンジニアリングを使用するかどうか
        
        Returns:
            Tuple: (元データ, 特徴量X, 密度率y, 占有座席数y)
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 平日データのみ使用
        ml_data = self.df_weekdays.copy()
        
        if use_feature_engineering:
            # 特徴量エンジニアリングを実行
            ml_data = self.create_advanced_features(ml_data)
            
            # 高度な特徴量を使用
            feature_columns = self.get_feature_columns()
            
            # 存在する特徴量のみを選択（エラー回避）
            available_features = [col for col in feature_columns if col in ml_data.columns]
            X = ml_data[available_features].values
            
            logger.info(f"特徴量エンジニアリング使用: {len(available_features)} 個の特徴量")
            logger.info(f"使用特徴量: {available_features}")
        else:
            # 基本特徴量: 曜日のみ
            X = ml_data[['day_of_week']].values
            logger.info("基本特徴量のみ使用: day_of_week")
        
        # ターゲット変数
        y_density = ml_data['density_rate'].values
        y_seats = ml_data['occupied_seats'].values
        
        logger.info(f"ML用データ準備完了: {len(ml_data)} 件のデータ")
        logger.info(f"特徴量: {X.shape}, 密度率: {y_density.shape}, 占有座席数: {y_seats.shape}")
        
        return ml_data, X, y_density, y_seats


if __name__ == "__main__":
    import logging
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # データ処理テスト
    processor = MLDataProcessor()
    
    try:
        # 基本データ準備
        print("=== 基本データ準備テスト ===")
        ml_data, X_basic, y_density, y_seats = processor.prepare_ml_data(use_feature_engineering=False)
        print(f"基本特徴量: {X_basic.shape}")
        
        # 特徴量エンジニアリング
        print("\n=== 特徴量エンジニアリングテスト ===")
        ml_data_fe, X_advanced, y_density_fe, y_seats_fe = processor.prepare_ml_data(use_feature_engineering=True)
        print(f"高度な特徴量: {X_advanced.shape}")
        
        # 特徴量リスト表示
        feature_columns = processor.get_feature_columns()
        print(f"\n利用可能な特徴量数: {len(feature_columns)}")
        print("特徴量一覧:")
        for i, feature in enumerate(feature_columns[:10]):  # 最初の10個のみ表示
            print(f"  {i+1}. {feature}")
        if len(feature_columns) > 10:
            print(f"  ... 他 {len(feature_columns) - 10} 個")
        
        print("\n✅ データ処理テスト完了")
        
    except Exception as e:
        print(f"❌ データ処理テストエラー: {e}")
        import traceback
        traceback.print_exc() 