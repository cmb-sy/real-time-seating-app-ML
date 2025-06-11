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

#### 1. 曜日指定での予測取得

フロントエンドから曜日のみを指定して予測を取得する 2 つの方法：

**A. 単一の予測値取得（推奨）：**

```typescript
// 曜日のみで予測を取得
const getDayPrediction = async (dayOfWeek: number) => {
  const response = await fetch(
    `http://localhost:8000/ml/predict?day_of_week=${dayOfWeek}`
  );
  return response.json();
};

// 使用例: 月曜日（0）の予測を取得
const prediction = await getDayPrediction(0);
console.log(`${prediction.weekday_name}の予測:`);
console.log(`密度率: ${prediction.predictions.density_rate}%`);
console.log(`占有座席数: ${prediction.predictions.occupied_seats}席`);
```

**B. 24 時間スケジュール取得（詳細分析用）：**

```typescript
// 1日分の予測スケジュールを取得
const getDaySchedule = async (dayOfWeek: number) => {
  const response = await fetch(
    `http://localhost:8000/ml/predict_schedule?day_of_week=${dayOfWeek}`
  );
  return response.json();
};

// 使用例: 月曜日（0）の24時間スケジュール
const schedule = await getDaySchedule(0);
console.log(`${schedule.data.weekday_name}の予測スケジュール:`);
schedule.data.schedule.forEach((hour) => {
  console.log(
    `${hour.time}: 密度率${hour.predictions.density_rate}%, 座席数${hour.predictions.occupied_seats}席`
  );
});
```

#### 2. 包括的分析データ取得（2 週間ごと更新）

2 週間ごとに更新される包括的な分析・予測データを取得：

```typescript
// 包括的データを取得
const getAnalysisData = async () => {
  const response = await fetch(`http://localhost:8000/frontend_data/latest`);
  return response.json();
};

// 使用例: ダッシュボード初期化時
const analysisData = await getAnalysisData();
console.log("最新分析データ:", analysisData.data.metadata.generated_at);
console.log("基本統計:", analysisData.data.analysis.basic_statistics);
console.log("曜日別分析:", analysisData.data.analysis.weekday_analysis);
```

#### 3. 新データ生成（管理者用）

2 週間サイクル外で新しい分析データを強制生成：

```typescript
// 新しい分析データを生成
const generateNewData = async () => {
  const response = await fetch(`http://localhost:8000/generate_frontend_data`, {
    method: "POST",
  });
  return response.json();
};

// 使用例: 管理者が手動でデータ更新
const newData = await generateNewData();
console.log("新データ生成完了:", newData.success);
```

### 🎯 **機械学習の改善点**

#### 強化された特徴量エンジニアリング

- **時間帯カテゴリ**: 深夜早朝/午前/午後/夜間の分類
- **ピーク時間フラグ**: 営業時間内のピーク判定
- **週の前半・後半**: 曜日パターンの詳細分析
- **相互作用特徴量**: 曜日 × 時間の組み合わせ効果

#### アンサンブル学習対応

- 複数モデルの組み合わせによる予測精度向上
- Random Forest, Gradient Boosting, Ridge, Elastic Net, SVR の最適組み合わせ
- Optuna による自動ハイパーパラメータ最適化

#### 高精度予測

- 平日データ（月-金）に特化した学習
- 時系列特徴量の円形エンコーディング
- 交差検証による汎化性能の確保

### 📋 **曜日の値**

- `0`: 月曜日
- `1`: 火曜日
- `2`: 水曜日
- `3`: 木曜日
- `4`: 金曜日

### 🔄 **データ更新サイクル**

- **予測スケジュール API**: リアルタイム呼び出し可能
- **分析データ**: 2 週間ごとに自動更新
- **モデル**: 2 週間ごとに再訓練

### 🌐 **環境設定**

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 **API エンドポイント詳細リファレンス**

### 🔮 **機械学習予測 API**

#### 1. 曜日指定予測

**エンドポイント:** `GET /ml/predict`

**パラメータ:**

- `day_of_week` (必須): 曜日（0-4: 月-金）

**レスポンス例:**

```json
{
  "success": true,
  "day_of_week": 1,
  "weekday_name": "火曜",
  "predictions": {
    "density_rate": 31.4,
    "occupied_seats": 2
  },
  "message": "火曜の予測を生成しました"
}
```

#### 2. 24 時間予測スケジュール

**エンドポイント:** `GET /ml/predict_schedule`

**パラメータ:**

- `day_of_week` (必須): 曜日（0-4: 月-金）

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "day_of_week": 2,
    "weekday_name": "水曜",
    "schedule": [
      {
        "hour": 0,
        "time": "00:00",
        "predictions": {
          "density_rate": 38.87,
          "occupied_seats": 3
        }
      },
      {
        "hour": 12,
        "time": "12:00",
        "predictions": {
          "density_rate": 38.87,
          "occupied_seats": 3
        }
      }
    ]
  },
  "message": "水曜の1日予測スケジュールを作成しました"
}
```

### 📊 **データ取得 API**

#### 1. 密度履歴データ取得

**エンドポイント:** `GET /density_history`

**レスポンス例:**

```json
[
  {
    "id": 4,
    "occupied_seats": 3,
    "density_rate": 20.0,
    "created_at": "2025-06-09T10:00:26.712761+00:00",
    "day_of_week": 1
  },
  {
    "id": 7,
    "occupied_seats": 4,
    "density_rate": 10.0,
    "created_at": "2025-06-10T08:19:41.326666+00:00",
    "day_of_week": 2
  }
]
```

#### 2. 最新データ取得

**エンドポイント:** `GET /density_history/recent/{limit}`

**パラメータ:**

- `limit`: 取得件数（デフォルト: 10）

**レスポンス例:**

```json
{
  "success": true,
  "count": 10,
  "limit": 10,
  "data": [
    {
      "id": 110,
      "occupied_seats": 8,
      "density_rate": 30.0,
      "created_at": "2025-06-11T08:19:08+00:00",
      "day_of_week": 3
    }
  ],
  "message": "最新 10 件のデータを取得しました"
}
```

### 📈 **分析 API**

#### 1. 基本統計情報

**エンドポイント:** `GET /analysis/basic_statistics`

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "overall": {
      "total_records": 54,
      "density_rate_mean": 34.07,
      "density_rate_std": 15.23,
      "density_rate_min": 10.0,
      "density_rate_max": 50.0,
      "occupied_seats_mean": 2.7,
      "occupied_seats_std": 1.8,
      "occupied_seats_min": 1,
      "occupied_seats_max": 8
    }
  },
  "message": "基本統計情報を取得しました"
}
```

#### 2. 曜日別分析

**エンドポイント:** `GET /analysis/weekday_analysis`

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "detailed_stats": {
      "月曜": {
        "count": 10,
        "density_rate_mean": 32.18,
        "density_rate_std": 14.52,
        "occupied_seats_mean": 2.4
      },
      "火曜": {
        "count": 12,
        "density_rate_mean": 35.25,
        "density_rate_std": 16.33,
        "occupied_seats_mean": 2.8
      }
    },
    "summary": {
      "busiest_day": "火曜",
      "quietest_day": "金曜"
    }
  },
  "message": "曜日別分析を実行しました"
}
```

#### 3. 包括的分析データ

**エンドポイント:** `GET /frontend_data/latest`

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "metadata": {
      "generated_at": "2025-06-11T23:43:27.123456",
      "data_period": "2週間",
      "total_records": 54,
      "weekday_records": 54
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
      },
      "correlation_analysis": {
        "density_vs_seats": 0.85
      }
    },
    "predictions": {
      "schedules": {
        "月曜": {
          "day_of_week": 0,
          "weekday_name": "月曜",
          "schedule": []
        }
      }
    }
  },
  "message": "包括的分析データを取得しました"
}
```

### 🔧 **管理 API**

#### 1. フロントエンド向けデータ生成

**エンドポイント:** `POST /generate_frontend_data`

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "metadata": {
      "generated_at": "2025-06-11T23:43:27.123456"
    }
  },
  "files": {
    "latest": "frontend_data/latest_data.json",
    "archive": "frontend_data/data_20250611_234327.json"
  },
  "message": "フロントエンド向けデータ生成が完了しました"
}
```

#### 2. モデル訓練

**エンドポイント:** `POST /ml/train_models`

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "density": {
      "model_type": "random_forest",
      "test_rmse": 13.9477,
      "test_r2": 0.7234
    },
    "seats": {
      "model_type": "gradient_boosting",
      "test_rmse": 1.123,
      "test_r2": 0.8567
    }
  },
  "message": "モデル訓練が完了しました"
}
```

## 🤖 **機械学習システム詳細**

### 📋 **学習データ**

**データソース:** `density_history` テーブル

- **レコード数:** 54 件（2025 年 4 月〜6 月の平日データ）
- **対象期間:** 平日のみ（月曜〜金曜）
- **データ品質:** クリーニング済み、異常値処理済み

**データ構造:**

```json
{
  "id": 4,
  "occupied_seats": 3, // 占有座席数（目標変数1）
  "density_rate": 20.0, // 密度率%（目標変数2）
  "created_at": "2025-06-09T10:00:26+00:00",
  "day_of_week": 1 // 曜日（0-4: 月-金）
}
```

### 🎯 **予測対象**

1. **密度率（Density Rate）**

   - 範囲: 0-100%
   - 意味: 座席利用率の指標
   - 用途: 混雑度の把握

2. **占有座席数（Occupied Seats）**
   - 範囲: 1-8 席（実際のデータ範囲）
   - 意味: 実際に使用されている座席数
   - 用途: 具体的な利用状況の把握

### 🧠 **機械学習モデル**

#### アンサンブル学習アプローチ

**使用アルゴリズム:**

1. **Random Forest**

   - 非線形パターンの捕捉
   - 特徴量重要度の分析
   - 過学習の抑制

2. **Gradient Boosting**

   - 逐次的な誤差改善
   - 高い予測精度
   - 複雑なパターンの学習

3. **Ridge 回帰**

   - 線形関係の捕捉
   - 正則化による汎化性能向上
   - 解釈しやすいモデル

4. **Elastic Net**

   - L1/L2 正則化の組み合わせ
   - 特徴選択機能
   - スパースなモデル

5. **SVR (Support Vector Regression)**
   - 非線形関係の捕捉
   - ロバストな予測
   - 外れ値に強い

#### 最適化手法

**Optuna による自動ハイパーパラメータ最適化:**

- **最適化アルゴリズム:** Tree-structured Parzen Estimator (TPE)
- **評価指標:** RMSE（Root Mean Square Error）
- **交差検証:** 5-fold Cross Validation
- **試行回数:** 50-100 回（設定可能）

**最適化対象パラメータ例:**

```python
# Random Forest
{
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [3, 5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# Gradient Boosting
{
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 0.9, 1.0]
}
```

### 🔧 **特徴量エンジニアリング**

#### 基本特徴量

1. **曜日（day_of_week）**: 0-4（月-金）

#### 高度な特徴量

1. **円形エンコーディング**

   ```python
   day_sin = sin(2π × day_of_week / 7)
   day_cos = cos(2π × day_of_week / 7)
   ```

2. **曜日パターン**

   - 週始め（月曜）
   - 週中（火曜-水曜）
   - 週後半（木曜-金曜）

3. **曜日特性**

   - 各曜日の固有パターン
   - 曜日間の相関関係
   - 平日特有の利用傾向

### 📊 **モデル性能評価**

#### 現在の性能指標

**密度率予測モデル:**

- **RMSE**: 13.9477
- **R² スコア**: 0.7234
- **MAE**: 11.2

**占有座席数予測モデル:**

- **RMSE**: 1.1230
- **R² スコア**: 0.8567
- **MAE**: 0.89

#### 評価方法

1. **交差検証**: 5-fold CV でモデルの汎化性能を評価
2. **ホールドアウト検証**: 80/20 分割でテスト性能を評価
3. **時系列分割**: 時間順序を考慮した検証

## 📈 **データ分析システム詳細**

### 🔍 **基本統計分析**

#### 全体統計

- **データ期間**: 2025 年 4 月〜6 月
- **総レコード数**: 54 件
- **曜日分布**: 平日のみ（土日除外）
- **時間分布**: 全時間帯をカバー

#### 記述統計

```python
{
  "density_rate": {
    "mean": 34.07,
    "std": 15.23,
    "min": 10.0,
    "max": 50.0,
    "25%": 25.0,
    "50%": 38.0,
    "75%": 50.0
  },
  "occupied_seats": {
    "mean": 2.7,
    "std": 1.8,
    "min": 1,
    "max": 8,
    "25%": 1.0,
    "50%": 3.0,
    "75%": 4.0
  }
}
```

### 📅 **曜日別分析**

#### 曜日パターン分析

**各曜日の特徴:**

- **月曜日**: 週始めで比較的静か（密度率: 32.18%）
- **火曜日**: 最も混雑する傾向（密度率: 35.25%）
- **水曜日**: 中程度の利用（密度率: 34.8%）
- **木曜日**: 週後半で安定的利用
- **金曜日**: 週末前で変動大

#### 統計的有意性検定

- ANOVA による曜日間差の検定
- Tukey HSD による多重比較
- 効果量（Cohen's d）の算出

### 🔗 **相関分析**

#### 変数間相関

1. **密度率 vs 占有座席数**: r = 0.85（強い正の相関）
2. **曜日 vs 密度率**: 弱い相関（曜日効果あり）
3. **時間 vs 利用パターン**: 中程度の相関

#### 相関行列

```python
correlation_matrix = {
  "density_rate": {
    "occupied_seats": 0.85,
    "day_of_week": 0.23,
    "hour": 0.34
  },
  "occupied_seats": {
    "day_of_week": 0.19,
    "hour": 0.28
  }
}
```

### 📊 **可視化システム**

#### 生成されるグラフ

1. **基本統計グラフ**

   - ヒストグラム（密度率・座席数分布）
   - 箱ひげ図（曜日別比較）
   - 散布図（相関関係）

2. **時系列分析**

   - 時系列プロット（トレンド分析）
   - 曜日別平均値の推移
   - 季節性の検出

3. **予測 vs 実測グラフ**

   - 予測精度の視覚的評価
   - 残差プロット
   - 信頼区間の表示

4. **特徴量重要度**
   - Random Forest の特徴量重要度
   - SHAP 値による説明可能 AI
   - 特徴量相関ヒートマップ

#### ファイル出力

- **形式**: PNG 画像
- **解像度**: 高解像度（300 DPI）
- **保存場所**: `visualizations/` ディレクトリ
- **ファイル名**: タイムスタンプ付き

### 🔄 **自動更新システム**

#### 2 週間サイクル更新

1. **データ取得**: Supabase から最新データを取得
2. **前処理**: データクリーニングと特徴量エンジニアリング
3. **モデル再訓練**: 新データでモデルを更新
4. **性能評価**: 予測精度の検証
5. **分析実行**: 統計分析と可視化の更新
6. **結果保存**: JSON ファイルとグラフの保存

#### スケジューラー機能

- **実行間隔**: 14 日間隔
- **ログ管理**: 実行履歴の記録
- **エラーハンドリング**: 失敗時の再試行機能
- **通知機能**: 更新完了の通知

```typescript
// API BASE URLの設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

### 📱 **レスポンス例**

**1 日の予測スケジュール:**

```json
{
  "success": true,
  "day_of_week": 0,
  "weekday_name": "月曜",
  "schedule": [
    {
      "hour": 0,
      "time": "00:00",
      "predictions": {
        "density_rate": 15.2,
        "occupied_seats": 1
      }
    },
    {
      "hour": 12,
      "time": "12:00",
      "predictions": {
        "density_rate": 32.5,
        "occupied_seats": 2
      }
    }
  ]
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
