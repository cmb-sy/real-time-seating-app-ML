#!/usr/bin/env python3

"""
- 特徴量エンジニアリング
"""
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from supabase import create_client

# 現在のファイルのディレクトリを取得してパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # 同じ階層を最優先に

# utilsディレクトリもパスに追加
utils_dir = os.path.join(current_dir, 'utils')
if os.path.exists(utils_dir):
    sys.path.insert(0, utils_dir)
import config

# 独立した特徴量エンジニアリング関数
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    特徴量エンジニアリング（曜日情報と統計的特徴量）
    
    Args:
        df: 元データ（day_of_week, density_rate, occupied_seatsを含むDataFrame）
        
    Returns:
        pd.DataFrame: 特徴量エンジニアリング後のデータ
    """
    feature_df = df.copy()
    
    # 1. 曜日ダミー変数（基本的な特徴量）
    feature_df['is_monday'] = (feature_df['day_of_week'] == 0).astype(int)
    feature_df['is_tuesday'] = (feature_df['day_of_week'] == 1).astype(int)
    feature_df['is_wednesday'] = (feature_df['day_of_week'] == 2).astype(int)
    feature_df['is_thursday'] = (feature_df['day_of_week'] == 3).astype(int)
    feature_df['is_friday'] = (feature_df['day_of_week'] == 4).astype(int)
    
    # 2. 週の分類（月火・水・木金の3グループ）
    feature_df['is_early_week'] = (feature_df['day_of_week'].isin([0, 1])).astype(int)  # 月火
    feature_df['is_mid_week'] = (feature_df['day_of_week'] == 2).astype(int)           # 水
    feature_df['is_late_week'] = (feature_df['day_of_week'].isin([3, 4])).astype(int)  # 木金
    
    feature_df = feature_df.fillna(0)

    return feature_df

# 特徴量カラム名を取得する関数
def get_feature_columns() -> List[str]:
    """
    機械学習で使用する特徴量カラムのリスト
    
    Returns:
        List[str]: 特徴量カラム名のリスト
    """
    features = [   
        'day_of_week',           # 基本的な曜日情報
        'density_seats_ratio',   # 密度率と座席数の比率
        'is_monday',             # 曜日ダミー変数
        'is_tuesday',
        'is_wednesday', 
        'is_thursday',
        'is_friday',
        'is_early_week',         # 週前半フラグ（月火）
        'is_mid_week',           # 週中フラグ（水）
        'is_late_week',          # 週後半フラグ（木金）
    ]
    return features

class MLDataProcessor:
    """機械学習用データ処理クラス"""
    def __init__(self):
        self.df = None
        self.df_weekdays = None
        # Supabaseクライアント
        supabase_url = getattr(config, 'NEXT_PUBLIC_SUPABASE_URL', None)
        supabase_key = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', None)
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase接続情報が環境変数に設定されていません")
        
        self.supabase_client = create_client(supabase_url, supabase_key)

    def load_data_from_supabase(self) -> pd.DataFrame:
        """
        Supabaseからデータを取得してDataFrameに変換
        
        Returns:
            pd.DataFrame: 取得したデータ
        """
        try:
            response = self.supabase_client.table("density_history").select("*").execute()
            self.df = pd.DataFrame(response.data)
            
            # データ型の変換（日付フォーマットが混在しているため、mixed形式で処理）
            self.df['created_at'] = pd.to_datetime(self.df['created_at'], format='mixed')
            self.df['density_rate'] = pd.to_numeric(self.df['density_rate'])
            self.df['occupied_seats'] = pd.to_numeric(self.df['occupied_seats'])
            self.df['day_of_week'] = pd.to_numeric(self.df['day_of_week'])
        
            # 平日データのみを抽出（0-4: 月-金）
            self.df_weekdays = self.df[self.df['day_of_week'].isin([0, 1, 2, 3, 4])].copy()
            
            return self.df
            
        except Exception as e:
            raise Exception(f"データ取得エラー: {e}")
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量エンジニアリング（曜日情報と統計的特徴量）
        
        Args:
            df: 元データ
            
        Returns:
            pd.DataFrame: 特徴量エンジニアリング後のデータ
        """
        # 独立した関数を使用
        feature_df = engineer_features(df)
        
        return feature_df
    
    def get_feature_columns(self) -> List[str]:
        """
        機械学習で使用する特徴量カラムのリスト
        
        Returns:
            List[str]: 特徴量カラム名のリスト
        """
        # 独立した関数を使用
        return get_feature_columns()
    
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
            
            # 特徴量名を保存
            self.feature_names = available_features
            
        else:
            # 基本特徴量: 曜日のみ
            X = ml_data[['day_of_week']].values
            self.feature_names = ['day_of_week']
        
        # ターゲット変数
        y_density = ml_data['density_rate'].values
        y_seats = ml_data['occupied_seats'].values
        
        return ml_data, X, y_density, y_seats


if __name__ == "__main__":
    
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