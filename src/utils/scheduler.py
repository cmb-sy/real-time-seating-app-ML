#!/usr/bin/env python3
"""
定期実行スケジューラー - 2週間ごとにフロントエンド向けデータを生成

使用方法:
1. 直接実行: python scheduler.py
2. バックグラウンド実行: nohup python scheduler.py &
3. cron設定: 0 2 */14 * * /path/to/scheduler.py
"""

import time
import logging
import requests
import json
import sys
from datetime import datetime, timedelta
import schedule
import os
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BiweeklyScheduler:
    """2週間ごとのデータ生成スケジューラー"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.last_run_file = "last_run.txt"
        
    def should_run(self) -> bool:
        """2週間経過したかチェック"""
        if not os.path.exists(self.last_run_file):
            return True
            
        try:
            with open(self.last_run_file, 'r') as f:
                last_run_str = f.read().strip()
                
            last_run = datetime.fromisoformat(last_run_str)
            now = datetime.now()
            
            # 2週間 = 14日
            return (now - last_run).days >= 14
            
        except Exception as e:
            logger.error(f"前回実行日時の確認エラー: {e}")
            return True
    
    def update_last_run(self):
        """最終実行日時を更新"""
        try:
            with open(self.last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
            logger.info("最終実行日時を更新しました")
        except Exception as e:
            logger.error(f"最終実行日時の更新エラー: {e}")
    
    def run_ml_pipeline(self) -> bool:
        """機械学習パイプラインを実行"""
        try:
            logger.info("機械学習パイプライン開始")
            
            # 1. ハイパーパラメータ最適化
            logger.info("ハイパーパラメータ最適化実行中...")
            response = requests.post(
                f"{self.api_base_url}/ml/optimize_hyperparameters",
                json={"n_trials": 50},
                timeout=300  # 5分タイムアウト
            )
            
            if not response.ok:
                logger.error(f"ハイパーパラメータ最適化失敗: {response.status_code}")
                return False
                
            logger.info("ハイパーパラメータ最適化完了")
            
            # 2. モデル訓練
            logger.info("モデル訓練実行中...")
            response = requests.post(
                f"{self.api_base_url}/ml/train_models",
                timeout=180  # 3分タイムアウト
            )
            
            if not response.ok:
                logger.error(f"モデル訓練失敗: {response.status_code}")
                return False
                
            logger.info("モデル訓練完了")
            return True
            
        except Exception as e:
            logger.error(f"機械学習パイプラインエラー: {e}")
            return False
    
    def generate_frontend_data(self) -> bool:
        """フロントエンド向けデータ生成"""
        try:
            logger.info("フロントエンド向けデータ生成開始")
            
            response = requests.post(
                f"{self.api_base_url}/generate_frontend_data",
                timeout=300  # 5分タイムアウト
            )
            
            if not response.ok:
                logger.error(f"データ生成失敗: {response.status_code}")
                return False
                
            result = response.json()
            if not result.get("success", False):
                logger.error(f"データ生成失敗: {result.get('error', 'Unknown error')}")
                return False
                
            logger.info("フロントエンド向けデータ生成完了")
            
            # 生成されたファイル情報をログ出力
            files = result.get("files", {})
            if files:
                logger.info(f"生成ファイル: {files}")
                
            return True
            
        except Exception as e:
            logger.error(f"フロントエンド向けデータ生成エラー: {e}")
            return False
    
    def run_full_pipeline(self):
        """完全なパイプラインを実行"""
        logger.info("=== 2週間ごとの定期実行開始 ===")
        
        try:
            # APIサーバーの疎通確認
            response = requests.get(f"{self.api_base_url}/health", timeout=30)
            if not response.ok:
                logger.error("APIサーバーに接続できません")
                return
                
            logger.info("APIサーバー接続確認完了")
            
            # 1. 機械学習パイプライン実行
            if not self.run_ml_pipeline():
                logger.error("機械学習パイプラインが失敗しました")
                return
                
            # 2. フロントエンド向けデータ生成
            if not self.generate_frontend_data():
                logger.error("フロントエンド向けデータ生成が失敗しました")
                return
                
            # 3. 最終実行日時更新
            self.update_last_run()
            
            logger.info("=== 2週間ごとの定期実行完了 ===")
            
        except Exception as e:
            logger.error(f"定期実行でエラーが発生しました: {e}")
    
    def check_and_run(self):
        """2週間経過チェックして実行"""
        if self.should_run():
            logger.info("2週間経過しました。定期実行を開始します")
            self.run_full_pipeline()
        else:
            logger.info("まだ2週間経過していません。次回実行まで待機中...")
    
    def start_continuous_monitoring(self):
        """継続的な監視を開始（1日1回チェック）"""
        logger.info("継続的監視モードを開始します（1日1回チェック）")
        
        # 毎日午前2時にチェック
        schedule.every().day.at("02:00").do(self.check_and_run)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(3600)  # 1時間待機
            except KeyboardInterrupt:
                logger.info("スケジューラーを停止します")
                break
            except Exception as e:
                logger.error(f"スケジューラーでエラー: {e}")
                time.sleep(300)  # エラー時は5分待機

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='2週間ごとのデータ生成スケジューラー')
    parser.add_argument('--mode', choices=['check', 'force', 'monitor'], default='check',
                      help='実行モード: check=チェックして実行, force=強制実行, monitor=継続監視')
    parser.add_argument('--api-url', default='http://localhost:8000',
                      help='APIサーバーのURL')
    
    args = parser.parse_args()
    
    scheduler = BiweeklyScheduler(api_base_url=args.api_url)
    
    if args.mode == 'check':
        scheduler.check_and_run()
    elif args.mode == 'force':
        logger.info("強制実行モードで開始します")
        scheduler.run_full_pipeline()
    elif args.mode == 'monitor':
        scheduler.start_continuous_monitoring()

if __name__ == "__main__":
    main() 