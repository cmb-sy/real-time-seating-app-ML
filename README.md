# Real-time Seating Prediction ML API

This project provides real-time seating predictions using Supabase as a database and Vercel serverless functions for API delivery.

<img width="709" alt="SS 2025-06-12 22 12 25" src="https://github.com/user-attachments/assets/83e1e09b-b468-4856-8872-507d85b7c419" />

## Project Overview

The system consists of the following components:

1. **Machine Learning Model** - Prediction model using scikit-learn and Optuna
2. **Data Analysis Tools** - Analysis and visualization of historical data
3. **API Endpoints** - Implemented as Vercel serverless functions
4. **Scheduler** - Updates models every two weeks

## Features

- Density rate and occupied seat prediction
- Day-of-week usage pattern analysis
- Real-time API endpoints (today and tomorrow predictions)
- Machine learning predictions by day of week
- Weekly average prediction data
- Hyperparameter optimization with Optuna
- Data visualization tools

## Technical Architecture

The project uses a gradient boosting model to predict seating density and occupancy based on the day of the week. The model is trained on historical data and deployed as serverless functions on Vercel, which provide JSON API endpoints for frontend consumption.

Key technical components:

- **Machine Learning**: Gradient Boosting Regressor models from scikit-learn
- **Backend**: Python serverless functions
- **Deployment**: Vercel serverless environment
- **Database**: Supabase

## Environment Setup

### Prerequisites

- Python 3.10 or higher
- Supabase account and API information

### Installation

1. Clone the repository:

# リアルタイム座席予測 API（機械学習版）

Supabase データベースと機械学習モデルを使用したリアルタイム座席予測システムです。

## 🚀 プロジェクト概要

このシステムは以下の機能を提供します：

- **今日・明日の座席予測** - 機械学習モデルによる高精度予測
- **週間平均予測** - Supabase データの統計的平均
- **自動モデル再学習** - GitHub Actions による定期的なモデル更新
- **特徴量エンジニアリング** - 時間、曜日、季節などの高度な特徴量

## 📋 システム要件

- Python 3.8+
- Node.js 18+ (Vercel CLI 用)
- Supabase アカウント

## 🛠️ セットアップ

### 1. 依存関係のインストール

```bash
# Python依存関係
pip install -r requirements.txt

# Vercel CLI（オプション）
npm install -g vercel
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下を設定：

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 🖥️ バックエンドの起動

### 方法 1: Vercel ローカル開発サーバー（推奨）

```bash
# Vercelローカル開発サーバーを起動
vercel dev

# アクセス: http://localhost:3000
```

### 方法 2: Python 簡易 HTTP サーバー

```bash
# Pythonサーバーを起動
python -m http.server 8000

# アクセス: http://localhost:8000
```

### 方法 3: 個別 API テスト

```bash
# 今日・明日の予測API
python src/api/predictions_today_tomorrow.py

# 週間平均予測API
python src/api/predictions_weekly_average.py

# Supabase同期API
python src/api/supabase_sync.py
```

## 🤖 機械学習モデルの更新

### 基本的なモデル学習

```bash
# 特徴量エンジニアリング付きで学習（推奨）
python src/ml/train_ml_models.py
```

### 詳細なオプション

```bash
# 密度率のみ最適化
python src/ml/train_ml_models.py --mode train --target density --n-trials 30

# 座席数のみ最適化
python src/ml/train_ml_models.py --mode train --target seats --n-trials 30

# 高速学習（試行回数少なめ）
python src/ml/train_ml_models.py --mode train --n-trials 20

# 高精度学習（試行回数多め）
python src/ml/train_ml_models.py --mode train --n-trials 100
```

### モデルのテストと確認

```bash
# 予測テスト
python src/ml/train_ml_models.py --mode test

# モデル情報表示
python src/ml/train_ml_models.py --mode info
```

### 学習プロセスの詳細

1. **データ準備** - Supabase から平日データを取得
2. **特徴量エンジニアリング** - 時間、曜日、季節、移動平均などの特徴量を生成
3. **ハイパーパラメータ最適化** - Optuna を使用してモデルを最適化
4. **モデル訓練** - 最適パラメータでモデルを訓練
5. **モデル保存** - `src/api/`ディレクトリに訓練済みモデルを保存
6. **予測テスト** - 各曜日での予測精度を確認

## 📊 特徴量エンジニアリング

システムは以下の特徴量を自動生成します：

### 時間関連特徴量

- `hour`, `minute` - 時刻情報
- `is_morning`, `is_afternoon`, `is_evening` - 時間帯フラグ

### 曜日関連特徴量

- `is_monday` ～ `is_friday` - 各曜日フラグ
- `is_early_week`, `is_late_week` - 週前半・後半フラグ

### 日付・季節特徴量

- `month`, `day`, `week_of_year` - 日付情報
- `is_spring` ～ `is_winter` - 季節フラグ

### 統計的特徴量

- `density_ma3_day0` ～ `density_ma3_day4` - 曜日別移動平均
- `prev_density`, `prev_seats` - 前回の値
- `density_diff`, `seats_diff` - 前回からの差分

### 交互作用特徴量

- `day_hour_interaction` - 曜日 × 時間の交互作用
- `density_seats_ratio` - 密度率/座席数の比率

## 🔄 自動モデル再学習

GitHub Actions により、2 週間ごとに自動的にモデルが再学習されます：

- **実行タイミング**: 毎月第 1・第 3 日曜日 2:00 AM (UTC)
- **処理内容**: 最新データでモデル再学習 → 自動コミット・プッシュ
- **手動実行**: GitHub の Actions タブから手動実行可能

## 📡 API エンドポイント

### 今日・明日の予測

```
GET /api/predictions/today-tomorrow
```

### 週間平均予測

```
GET /api/predictions/weekly-average
```

### Supabase データ同期

```
POST /api/supabase/sync
```

## 🏗️ プロジェクト構造

```
src/
├── api/                    # APIエンドポイント
│   ├── predictions_today_tomorrow.py    # ML予測API
│   ├── predictions_weekly_average.py    # Supabase平均API
│   ├── supabase_sync.py               # データ同期API
│   └── *.joblib                       # 訓練済みモデル
├── ml/                     # 機械学習
│   ├── train_ml_models.py             # メイン学習スクリプト
│   ├── ml_models.py                   # MLモデルクラス
│   └── data_analysis.py               # データ処理クラス
└── utils/                  # ユーティリティ
    ├── response_helper.py             # 共通レスポンス処理
    ├── database.py                    # Supabase接続
    └── config.py                      # 設定管理
```

## 🚀 デプロイ

### Vercel デプロイ

```bash
# Vercelにデプロイ
vercel --prod

# 環境変数を設定
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
```

## 🔧 トラブルシューティング

### よくある問題

1. **Supabase 接続エラー**

   - `.env`ファイルの設定を確認
   - Supabase プロジェクトの状態を確認

2. **モデル学習エラー**

   - データが十分にあるか確認（最低 100 件以上推奨）
   - 依存関係が正しくインストールされているか確認

3. **予測精度が低い**
   - 特徴量エンジニアリングを有効にする
   - 試行回数を増やす（`--n-trials 100`）
   - より多くのデータを収集する

### ログの確認

```bash
# 学習ログの詳細表示
python src/ml/train_ml_models.py --mode train --n-trials 50 2>&1 | tee training.log
```

## 📈 パフォーマンス最適化

- **特徴量エンジニアリング**: 予測精度向上のため推奨
- **試行回数調整**: 精度と学習時間のバランスを調整
- **定期再学習**: 最新データでモデルを更新

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
