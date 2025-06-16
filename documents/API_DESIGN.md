# Real-time Seating Prediction API 設計書

## 概要

リアルタイム座席予測 API は、機械学習モデルと Supabase データベースを使用して座席の占有率と空席数を予測するシステムです。

## 技術スタック

- **バックエンド**: Python (Vercel Serverless Functions)
- **機械学習**: scikit-learn (Gradient Boosting Regressor)
- **データベース**: Supabase
- **デプロイ**: Vercel
- **データ形式**: JSON

## API エンドポイント

### 1. 今日・明日の予測 (機械学習モデル)

```
GET /api/predictions/today-tomorrow
GET /predictions/today-tomorrow
```

**説明**: 機械学習モデルを使用して今日と明日の座席予測を提供

**レスポンス例**:

```json
{
  "success": true,
  "data": {
    "today": {
      "date": "2024-01-15",
      "day_of_week": "月",
      "occupancy_rate": 0.65,
      "available_seats": 35
    },
    "tomorrow": {
      "date": "2024-01-16",
      "day_of_week": "火",
      "occupancy_rate": 0.75,
      "available_seats": 25
    }
  }
}
```

**特徴**:

- 平日のみ対応（月-金）
- 機械学習モデル（Gradient Boosting）使用
- 曜日のみを特徴量として使用

### 2. 週間平均予測 (Supabase データ)

```
GET /api/predictions/weekly-average
GET /predictions/weekly-average
```

**説明**: Supabase から取得した全データの単純平均を計算して週間予測を提供

**レスポンス例**:

```json
{
  "success": true,
  "data": {
    "weekly_averages": [
      {
        "weekday": 0,
        "weekday_name": "月曜",
        "occupancy_rate": 0.65,
        "available_seats": 35
      },
      {
        "weekday": 1,
        "weekday_name": "火曜",
        "occupancy_rate": 0.75,
        "available_seats": 25
      }
    ]
  }
}
```

**特徴**:

- Supabase の`density_history`テーブルから全データを取得
- 曜日ごとの単純平均計算
- 平日のみ対応（月-金）

### 3. Supabase 同期 (既存)

```
GET /api/supabase/sync
GET /supabase/sync
```

**説明**: Supabase 用のデータ同期エンドポイント（既存機能）

## データ構造

### 共通レスポンス形式

**成功時**:

```json
{
  "success": true,
  "data": {
    // エンドポイント固有のデータ
  }
}
```

**エラー時**:

```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

### 予測データ形式

各予測には以下の 2 つの値のみを含む：

- `occupancy_rate`: 占有率（0.0-1.0 の範囲）
- `available_seats`: 空席数（整数）

## アーキテクチャ

### ファイル構成

```
src/
├── api/
│   ├── predictions_today_tomorrow.py    # 今日・明日予測（ML）
│   ├── predictions_weekly_average.py    # 週間平均（Supabase）
│   └── supabase_sync.py                 # Supabase同期
├── utils/
│   ├── response_helper.py               # 共通レスポンス処理
│   ├── database.py                      # Supabaseクライアント
│   └── config.py                        # 設定管理
└── ml/
    ├── ml_models.py                     # MLモデル定義
    ├── train.py               # モデル訓練
    └── data_analysis.py                 # データ分析
```

### 共通機能

**レスポンス処理** (`src/utils/response_helper.py`):

- `send_success_response()`: 成功レスポンス送信
- `send_error_response()`: エラーレスポンス送信
- `send_options_response()`: CORS 対応

**データベース接続** (`src/utils/database.py`):

- `get_supabase_client()`: Supabase クライアント取得

## 機械学習モデル

### モデル仕様

- **アルゴリズム**: Gradient Boosting Regressor
- **特徴量**: 曜日のみ（0-4: 月-金）
- **予測対象**:
  - 密度率（density_rate）
  - 占有座席数（occupied_seats）

### モデルファイル

- `density_model.joblib`: 密度率予測モデル
- `seats_model.joblib`: 座席数予測モデル
- `best_params.joblib`: 最適パラメータ
- `model_performance.joblib`: モデル性能指標

## データベース

### Supabase テーブル

**density_history**:

- `density_rate`: 密度率（float）
- `occupied_seats`: 占有座席数（int）
- `day_of_week`: 曜日（0-4: 月-金）
- `created_at`: 作成日時

## デプロイメント

### Vercel 設定

**vercel.json**:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/api/*.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "10mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/predictions/today-tomorrow",
      "dest": "src/api/predictions_today_tomorrow.py"
    },
    {
      "src": "/api/predictions/today-tomorrow",
      "dest": "src/api/predictions_today_tomorrow.py"
    },
    {
      "src": "/predictions/weekly-average",
      "dest": "src/api/predictions_weekly_average.py"
    },
    {
      "src": "/api/predictions/weekly-average",
      "dest": "src/api/predictions_weekly_average.py"
    },
    {
      "src": "/supabase/sync",
      "dest": "src/api/supabase_sync.py"
    },
    {
      "src": "/api/supabase/sync",
      "dest": "src/api/supabase_sync.py"
    }
  ]
}
```

## 環境変数

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_URL=your-anon-key
```

## エラーハンドリング

### 共通エラー

- **土日アクセス**: "土日は営業していません。平日（月-金）のみ予測を提供しています。"
- **モデルロードエラー**: "ML 予測モデルをロードできませんでした。"
- **データ取得エラー**: "Supabase からデータを取得できませんでした。"

### CORS 対応

全エンドポイントで以下の CORS ヘッダーを設定：

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization, Origin`

## 設計原則

1. **シンプルさ**: 必要最小限のデータ（occupancy_rate, available_seats）のみ返却
2. **一貫性**: 全エンドポイントで統一されたレスポンス形式
3. **保守性**: 共通処理の関数化によるコード重複の排除
4. **拡張性**: 新しいエンドポイント追加時の共通処理再利用
