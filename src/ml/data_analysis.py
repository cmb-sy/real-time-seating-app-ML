#!/usr/bin/env python3

"""
データ分析モジュール - Supabaseから取得したdensity_historyデータの分析を行う

主な機能:
- 基本統計の取得
- 曜日別分析
- 相関分析  
- 可視化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple
import logging
import sys
from supabase import create_client
from src.utils import config

# 日本語フォントの設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """データ分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.df = None
        self.df_weekdays = None
        
        # Supabaseクライアント
        self.supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        # 曜日名マッピング（0-4: 月-金）
        self.weekday_names = {
            0: "月曜", 1: "火曜", 2: "水曜", 3: "木曜", 4: "金曜"
        }
        
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
    
    def get_basic_statistics(self) -> Dict:
        """
        基本統計情報を取得
        
        Returns:
            Dict: 統計情報
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        stats = {
            "全体統計": {
                "レコード数": len(self.df),
                "期間": f"{self.df['created_at'].min()} ～ {self.df['created_at'].max()}",
                "density_rate": {
                    "平均": float(self.df['density_rate'].mean()),
                    "中央値": float(self.df['density_rate'].median()),
                    "標準偏差": float(self.df['density_rate'].std()),
                    "最小": float(self.df['density_rate'].min()),
                    "最大": float(self.df['density_rate'].max())
                },
                "occupied_seats": {
                    "平均": float(self.df['occupied_seats'].mean()),
                    "中央値": float(self.df['occupied_seats'].median()),
                    "標準偏差": float(self.df['occupied_seats'].std()),
                    "最小": int(self.df['occupied_seats'].min()),
                    "最大": int(self.df['occupied_seats'].max())
                }
            },
            "平日統計": {
                "レコード数": len(self.df_weekdays),
                "density_rate": {
                    "平均": float(self.df_weekdays['density_rate'].mean()),
                    "中央値": float(self.df_weekdays['density_rate'].median()),
                    "標準偏差": float(self.df_weekdays['density_rate'].std()),
                },
                "occupied_seats": {
                    "平均": float(self.df_weekdays['occupied_seats'].mean()),
                    "中央値": float(self.df_weekdays['occupied_seats'].median()),
                    "標準偏差": float(self.df_weekdays['occupied_seats'].std()),
                }
            }
        }
        
        return stats
    
    def analyze_by_weekday(self) -> Dict:
        """
        曜日別分析
        
        Returns:
            Dict: 曜日別統計
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 平日データ（0-4: 月-金）で分析
        weekday_stats = {}
        
        for day in [0, 1, 2, 3, 4]:  # 月-金
            day_data = self.df_weekdays[self.df_weekdays['day_of_week'] == day]
            
            if len(day_data) > 0:
                weekday_stats[self.weekday_names[day]] = {
                    "レコード数": len(day_data),
                    "density_rate": {
                        "平均": float(day_data['density_rate'].mean()),
                        "中央値": float(day_data['density_rate'].median()),
                        "標準偏差": float(day_data['density_rate'].std()),
                        "最小": float(day_data['density_rate'].min()),
                        "最大": float(day_data['density_rate'].max())
                    },
                    "occupied_seats": {
                        "平均": float(day_data['occupied_seats'].mean()),
                        "中央値": float(day_data['occupied_seats'].median()),
                        "標準偏差": float(day_data['occupied_seats'].std()),
                        "最小": int(day_data['occupied_seats'].min()),
                        "最大": int(day_data['occupied_seats'].max())
                    }
                }
        
        return weekday_stats
    
    def create_visualizations(self) -> Dict[str, str]:
        """
        可視化グラフを作成
        
        Returns:
            Dict[str, str]: 保存されたグラフファイルのパス
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        saved_plots = {}
        
        # 1. 曜日別density_rate箱ひげ図
        plt.figure(figsize=(12, 6))
        weekday_data = self.df_weekdays.copy()
        weekday_data['曜日'] = weekday_data['day_of_week'].map(self.weekday_names)
        
        sns.boxplot(data=weekday_data, x='曜日', y='density_rate')
        plt.title('曜日別 密度率 (Density Rate) 分布')
        plt.ylabel('密度率 (%)')
        plt.xlabel('曜日')
        plt.xticks(rotation=45)
        
        density_plot_path = 'plots/weekday_density_rate_boxplot.png'
        plt.tight_layout()
        plt.savefig(density_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        saved_plots['density_rate_boxplot'] = density_plot_path
        
        # 2. 曜日別occupied_seats箱ひげ図
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=weekday_data, x='曜日', y='occupied_seats')
        plt.title('曜日別 占有座席数 (Occupied Seats) 分布')
        plt.ylabel('占有座席数')
        plt.xlabel('曜日')
        plt.xticks(rotation=45)
        
        seats_plot_path = 'plots/weekday_occupied_seats_boxplot.png'
        plt.tight_layout()
        plt.savefig(seats_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        saved_plots['occupied_seats_boxplot'] = seats_plot_path
        
        # 3. 相関関係散布図
        plt.figure(figsize=(10, 8))
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, day in enumerate([0, 1, 2, 3, 4]):
            day_data = weekday_data[weekday_data['day_of_week'] == day]
            plt.scatter(day_data['occupied_seats'], day_data['density_rate'], 
                       label=self.weekday_names[day], color=colors[i], alpha=0.7)
        
        plt.xlabel('占有座席数')
        plt.ylabel('密度率 (%)')
        plt.title('占有座席数と密度率の相関関係（曜日別）')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        correlation_plot_path = 'plots/seats_density_correlation.png'
        plt.tight_layout()
        plt.savefig(correlation_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        saved_plots['correlation_plot'] = correlation_plot_path
        
        # 4. 時系列プロット
        plt.figure(figsize=(15, 6))
        plt.plot(self.df_weekdays['created_at'], self.df_weekdays['density_rate'], 
                marker='o', markersize=3, alpha=0.7, label='密度率')
        plt.xlabel('日時')
        plt.ylabel('密度率 (%)')
        plt.title('密度率の時系列変化（平日のみ）')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        timeseries_plot_path = 'plots/density_rate_timeseries.png'
        plt.tight_layout()
        plt.savefig(timeseries_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        saved_plots['timeseries_plot'] = timeseries_plot_path
        
        logger.info(f"可視化グラフを保存しました: {saved_plots}")
        
        return saved_plots
    
    def get_weekday_summary(self) -> Dict:
        """
        平日データの要約統計を取得
        
        Returns:
            Dict: 要約統計
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 曜日別の平均値
        weekday_means = self.df_weekdays.groupby('day_of_week').agg({
            'density_rate': ['mean', 'std', 'count'],
            'occupied_seats': ['mean', 'std', 'count']
        }).round(2)
        
        # 結果を整理
        summary = {}
        for day in [0, 1, 2, 3, 4]:
            if day in weekday_means.index:
                summary[self.weekday_names[day]] = {
                    'density_rate_mean': float(weekday_means.loc[day, ('density_rate', 'mean')]),
                    'density_rate_std': float(weekday_means.loc[day, ('density_rate', 'std')]),
                    'occupied_seats_mean': float(weekday_means.loc[day, ('occupied_seats', 'mean')]),
                    'occupied_seats_std': float(weekday_means.loc[day, ('occupied_seats', 'std')]),
                    'record_count': int(weekday_means.loc[day, ('density_rate', 'count')])
                }
        
        return summary
    
    def get_correlation_analysis(self) -> Dict:
        """
        相関分析を実行
        
        Returns:
            Dict: 相関分析結果
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 数値カラムのみで相関分析
        numerical_cols = ['density_rate', 'occupied_seats', 'day_of_week']
        correlation_matrix = self.df_weekdays[numerical_cols].corr()
        
        # 相関分析結果
        analysis = {
            'correlation_matrix': correlation_matrix.to_dict(),
            'density_occupied_correlation': float(correlation_matrix.loc['density_rate', 'occupied_seats']),
            'density_dayofweek_correlation': float(correlation_matrix.loc['density_rate', 'day_of_week']),
            'occupied_dayofweek_correlation': float(correlation_matrix.loc['occupied_seats', 'day_of_week'])
        }
        
        return analysis
    
    def analyze_by_month(self) -> Dict:
        """
        月別分析を実行
        
        Returns:
            Dict: 月別統計
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 月情報を追加
        df_with_month = self.df_weekdays.copy()
        df_with_month['month'] = df_with_month['created_at'].dt.month
        df_with_month['year_month'] = df_with_month['created_at'].dt.strftime('%Y-%m')
        
        # 月別の統計情報
        monthly_stats = {}
        
        # 年月別の分析
        for year_month in sorted(df_with_month['year_month'].unique()):
            month_data = df_with_month[df_with_month['year_month'] == year_month]
            
            if len(month_data) > 0:
                monthly_stats[year_month] = {
                    "レコード数": len(month_data),
                    "density_rate": {
                        "平均": float(month_data['density_rate'].mean()),
                        "中央値": float(month_data['density_rate'].median()),
                        "標準偏差": float(month_data['density_rate'].std()),
                        "最小": float(month_data['density_rate'].min()),
                        "最大": float(month_data['density_rate'].max())
                    },
                    "occupied_seats": {
                        "平均": float(month_data['occupied_seats'].mean()),
                        "中央値": float(month_data['occupied_seats'].median()),
                        "標準偏差": float(month_data['occupied_seats'].std()),
                        "最小": int(month_data['occupied_seats'].min()),
                        "最大": int(month_data['occupied_seats'].max())
                    }
                }
        
        return monthly_stats
    
    def get_weekday_visualization_data(self) -> Dict:
        """
        曜日別可視化用のデータを取得
        
        Returns:
            Dict: 可視化用データ
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 曜日別データの準備
        weekday_data = self.df_weekdays.copy()
        weekday_data['weekday_name'] = weekday_data['day_of_week'].map(self.weekday_names)
        
        # 曜日別の統計データ
        visualization_data = {
            "weekday_density_rate": {},
            "weekday_occupied_seats": {},
            "weekday_averages": {}
        }
        
        for day in [0, 1, 2, 3, 4]:  # 月-金
            day_data = weekday_data[weekday_data['day_of_week'] == day]
            day_name = self.weekday_names[day]
            
            if len(day_data) > 0:
                # 密度率データ
                visualization_data["weekday_density_rate"][day_name] = {
                    "values": day_data['density_rate'].tolist(),
                    "mean": float(day_data['density_rate'].mean()),
                    "median": float(day_data['density_rate'].median()),
                    "std": float(day_data['density_rate'].std())
                }
                
                # 占有座席数データ
                visualization_data["weekday_occupied_seats"][day_name] = {
                    "values": day_data['occupied_seats'].tolist(),
                    "mean": float(day_data['occupied_seats'].mean()),
                    "median": float(day_data['occupied_seats'].median()),
                    "std": float(day_data['occupied_seats'].std())
                }
                
                # 平均値
                visualization_data["weekday_averages"][day_name] = {
                    "density_rate_avg": float(day_data['density_rate'].mean()),
                    "occupied_seats_avg": float(day_data['occupied_seats'].mean()),
                    "record_count": len(day_data)
                }
        
        return visualization_data
    
    def get_monthly_averages(self) -> Dict:
        """
        月別平均値を取得
        
        Returns:
            Dict: 月別平均値
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 月情報を追加
        df_with_month = self.df_weekdays.copy()
        df_with_month['year_month'] = df_with_month['created_at'].dt.strftime('%Y-%m')
        
        # 月別平均値
        monthly_averages = {}
        
        for year_month in sorted(df_with_month['year_month'].unique()):
            month_data = df_with_month[df_with_month['year_month'] == year_month]
            
            if len(month_data) > 0:
                monthly_averages[year_month] = {
                    "density_rate_avg": float(month_data['density_rate'].mean()),
                    "occupied_seats_avg": float(month_data['occupied_seats'].mean()),
                    "record_count": len(month_data)
                }
        
        return monthly_averages
    
    def prepare_ml_data(self) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
        """
        機械学習用のデータを準備（時間特徴量なし）
        
        Returns:
            Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]: (全データ, 特徴量, 密度率目的変数, 座席数目的変数)
        """
        if self.df is None:
            self.load_data_from_supabase()
        
        # 平日データのみを使用
        ml_data = self.df_weekdays.copy()
        
        # 特徴量：曜日のみ使用（時間特徴量は除去）
        feature_cols = ['day_of_week']
        
        X = ml_data[feature_cols].values
        y_density = ml_data['density_rate'].values
        y_seats = ml_data['occupied_seats'].values
        
        logger.info(f"機械学習用データ準備完了（時間特徴量なし）: 特徴量 {X.shape}, 密度率目的変数 {y_density.shape}, 座席数目的変数 {y_seats.shape}")
        
        return ml_data, X, y_density, y_seats 