# Real-time Seating App ML API

リアルタイム座席アプリの ML 用 API プロジェクト

## 概要

このプロジェクトは、FastAPI と Supabase を使用して、`density_history`テーブルからデータを取得する API を提供します。

## 技術スタック

- **Python**: 3.13.2
- **FastAPI**: Web API フレームワーク
- **Supabase**: データベース（PostgreSQL）
- **UV**: Python プロジェクト管理ツール
- **Uvicorn**: ASGI サーバー

## セットアップ

### 1. 依存関係のインストール

```bash
uv sync
```

### 2. 仮想環境の有効化

```bash
source .venv/bin/activate
```

### 3. サーバーの起動

```bash
python start_server.py
```

または

```bash
uvicorn main:app --reload
```

## API エンドポイント

### 基本エンドポイント

- `GET /` - ルートエンドポイント
- `GET /health` - ヘルスチェック（データベース接続確認）

### データ取得エンドポイント

- `GET /density_history` - 全ての密度履歴データを取得
- `GET /density_history/recent/{limit}` - 最新の密度履歴データを指定件数取得
- `GET /density_history/count` - 密度履歴データの総件数を取得

### レスポンス例

```json
{
  "success": true,
  "count": 150,
  "data": [
    {
      "id": 1,
      "density": 0.75,
      "timestamp": "2024-01-15T10:30:00Z",
      "location": "area_1"
    }
  ],
  "message": "density_historyテーブルから 150 件のデータを取得しました"
}
```

## プロジェクト構造

```
.
├── main.py           # FastAPIメインアプリケーション
├── database.py       # Supabaseクライアント設定
├── config.py         # 設定ファイル
├── start_server.py   # サーバー起動スクリプト
├── pyproject.toml    # プロジェクト依存関係
└── README.md         # このファイル
```

## 開発者向け情報

### コードの説明

#### 1. config.py

Supabase の接続情報（URL、API キー）を管理するファイルです。

#### 2. database.py

Supabase クライアントを初期化し、データベース接続を管理します。

#### 3. main.py

FastAPI アプリケーションのメインファイルで、以下の機能を提供します：

- API エンドポイントの定義
- データベースからのデータ取得
- エラーハンドリング

### 主要な機能

1. **全データ取得** (`/density_history`)

   - `density_history`テーブルから全てのレコードを取得
   - Supabase Python クライアントの`select("*")`を使用

2. **最新データ取得** (`/density_history/recent/{limit}`)

   - 指定した件数の最新データを取得
   - `order("created_at", desc=True)`で降順ソート

3. **データ件数取得** (`/density_history/count`)
   - テーブルの総レコード数を取得
   - `count="exact"`オプションを使用

### エラーハンドリング

- データベース接続エラー
- クエリ実行エラー
- HTTP 例外処理

API 実行時にエラーが発生した場合は、適切な HTTP ステータスコードとエラーメッセージが返されます。

## 注意事項

- 本番環境では、設定情報を環境変数から読み込むことを推奨します
- API キーなどの機密情報は適切に管理してください
- 大量のデータを取得する際は、ページネーション機能の実装を検討してください

## フロントエンド連携（TypeScript + Next.js）

### 🔗 **基本的な API 呼び出し**

#### 1. 曜日指定予測（リアルタイム）

フロントエンドから曜日と時間を指定して予測を取得：

```typescript
// API呼び出し関数
const predictDensity = async (dayOfWeek: number, hour: number) => {
  const response = await fetch(
    `http://localhost:8000/ml/predict?day_of_week=${dayOfWeek}&hour=${hour}`
  );
  return response.json();
};

// 使用例: 月曜日（0）の12時の予測
const prediction = await predictDensity(0, 12);
console.log(`${prediction.weekday_name} ${prediction.time}`);
console.log(`密度率: ${prediction.density_rate}%`);
console.log(`占有座席数: ${prediction.occupied_seats}席`);
```

#### 2. 1 日の予測スケジュール取得

```typescript
// 1日分の予測スケジュールを取得
const getDaySchedule = async (dayOfWeek: number) => {
  const response = await fetch(
    `http://localhost:8000/ml/predict_day_schedule?day_of_week=${dayOfWeek}`
  );
  return response.json();
};

// 使用例: 月曜日（0）の24時間スケジュール
const schedule = await getDaySchedule(0);
schedule.schedule.forEach((hour) => {
  console.log(`${hour.time}: 密度率${hour.predictions.density_rate}%`);
});
```

#### 3. 分析データ取得（2 週間ごと更新）

```typescript
// 最新の分析データを取得
const getAnalysisData = async () => {
  const response = await fetch("http://localhost:8000/frontend_data/latest");
  return response.json();
};

// 使用例: ダッシュボード表示用
const data = await getAnalysisData();
console.log(`総レコード数: ${data.metadata.total_records}`);
console.log(
  `平均密度率: ${data.analysis.basic_statistics.overall.density_rate_mean}%`
);
```

### 📋 **曜日の値**

- `0`: 月曜日
- `1`: 火曜日
- `2`: 水曜日
- `3`: 木曜日
- `4`: 金曜日

### 🔄 **データ更新サイクル**

- **予測 API**: リアルタイム呼び出し可能
- **分析データ**: 2 週間ごとに自動更新
- **モデル**: 2 週間ごとに再訓練

### 🌐 **環境設定**

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```typescript
// API BASE URLの設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

### 📱 **レスポンス例**

**予測結果:**

```json
{
  "success": true,
  "day_of_week": 0,
  "weekday_name": "月曜",
  "hour": 12,
  "time": "12:00",
  "density_rate": 32.5,
  "occupied_seats": 2
}
```

**分析データ:**

```json
{
  "metadata": {
    "generated_at": "2025-06-11T23:43:27.123456",
    "total_records": 54
  },
  "analysis": {
    "basic_statistics": {
      "overall": {
        "density_rate_mean": 34.07,
        "occupied_seats_mean": 2.7
      }
    },
    "weekday_analysis": {
      "月曜": { "density_rate_mean": 32.18 },
      "火曜": { "density_rate_mean": 35.25 }
    }
  }
}
```
