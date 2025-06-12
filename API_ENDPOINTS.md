# リアルタイム座席予測 API（ML 版）エンドポイント仕様書

このドキュメントでは、機械学習モデルを使用したリアルタイム座席予測システムの API エンドポイントと各リクエスト/レスポンスの仕様を説明します。

## 基本情報

- ベース URL: `http://localhost:8000`
- 認証: 不要
- レスポンス形式: JSON
- サポート日: 平日（月曜日〜金曜日）のみ

## API 概要

本 API は機械学習モデル（Gradient Boosting）を使用して、曜日ごとの座席占有率と人口密度を予測します。特徴量としては曜日のみを使用しており、時間帯による変動は考慮していません。

## エンドポイント一覧

### 1. ヘルスチェック

```
GET /health
```

**レスポンス例:**

```json
{
  "status": "ok",
  "message": "API is running"
}
```

### 2. 特定曜日の予測取得

指定した曜日の予測データを取得します。

```
GET /ml/predict?day_of_week={day_of_week}
```

**パラメータ:**

- `day_of_week`: 曜日（0: 月曜, 1: 火曜, 2: 水曜, 3: 木曜, 4: 金曜）

**レスポンス例:**

```json
{
  "success": true,
  "day_of_week": 3,
  "weekday_name": "木",
  "predictions": {
    "density_rate": 28.06,
    "occupied_seats": 2
  },
  "message": "機械学習モデルによる予測"
}
```

### 3. 今日と明日の予測取得

現在の日付に基づいて、今日と明日（両方が平日の場合）の予測データを取得します。

```
GET /api/predictions/today-tomorrow
```

**レスポンス例:**

```json
{
  "success": true,
  "timestamp": "2025-06-12T20:45:11.596625",
  "data": {
    "today": {
      "date": "2025-06-12",
      "day_of_week": 3,
      "weekday_name": "木",
      "predictions": {
        "density_rate": 28.06,
        "occupied_seats": 2
      }
    },
    "tomorrow": {
      "date": "2025-06-13",
      "day_of_week": 4,
      "weekday_name": "金",
      "predictions": {
        "density_rate": 35.63,
        "occupied_seats": 2
      }
    }
  },
  "message": "機械学習モデルによる予測"
}
```

**明日が土日の場合のレスポンス例:**

```json
{
  "success": true,
  "timestamp": "2025-06-14T20:45:11.596625",
  "data": {
    "today": {
      "date": "2025-06-14",
      "day_of_week": 4,
      "weekday_name": "金",
      "predictions": {
        "density_rate": 35.63,
        "occupied_seats": 2
      }
    },
    "tomorrow": {
      "date": null,
      "day_of_week": null,
      "weekday_name": null,
      "predictions": null,
      "message": "明日は土日のため営業していません"
    }
  },
  "message": "機械学習モデルによる予測"
}
```

### 4. 曜日別分析データ取得

全曜日の予測および分析データを取得します。

```
GET /analysis/weekday_analysis
```

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "detailed_stats": {},
    "daily_predictions": {
      "月曜日": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 32.45,
          "occupied_seats": 2
        }
      },
      "火曜日": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 28.3,
          "occupied_seats": 2
        }
      },
      "水曜日": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 40.3,
          "occupied_seats": 3
        }
      },
      "木曜日": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 28.06,
          "occupied_seats": 2
        }
      },
      "金曜日": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 35.63,
          "occupied_seats": 2
        }
      }
    },
    "summary": {
      "全体": {
        "record_count": 55,
        "density_rate_mean": 32.95,
        "occupied_seats_mean": 2.2
      }
    }
  },
  "message": "機械学習モデルによる曜日別予測"
}
```

### 5. 週間平均予測取得

全曜日の予測データと週間サマリーを取得します。フロントエンド表示用に最適化されたフォーマット。

```
GET /api/predictions/weekly-average
```

**レスポンス例:**

```json
{
  "success": true,
  "timestamp": "2025-06-12T20:45:11.596625",
  "data": {
    "weekly_averages": [
      {
        "weekday": 0,
        "weekday_name": "月曜日",
        "prediction": {
          "occupancy_rate": 0.32,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55
        }
      },
      {
        "weekday": 1,
        "weekday_name": "火曜日",
        "prediction": {
          "occupancy_rate": 0.28,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55
        }
      },
      {
        "weekday": 2,
        "weekday_name": "水曜日",
        "prediction": {
          "occupancy_rate": 0.4,
          "available_seats": 97,
          "status": "available",
          "confidence": "medium",
          "data_points": 55
        }
      },
      {
        "weekday": 3,
        "weekday_name": "木曜日",
        "prediction": {
          "occupancy_rate": 0.28,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55
        }
      },
      {
        "weekday": 4,
        "weekday_name": "金曜日",
        "prediction": {
          "occupancy_rate": 0.36,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55
        }
      }
    ],
    "summary": {
      "most_busy_day": {
        "weekday": 2,
        "weekday_name": "水曜日",
        "occupancy_rate": 0.4
      },
      "least_busy_day": {
        "weekday": 3,
        "weekday_name": "木曜日",
        "occupancy_rate": 0.28
      },
      "average_occupancy": 0.33,
      "recommendation": "全体的に空いています。最も混雑するのは水曜日ですが、それでも比較的余裕があります。"
    }
  },
  "metadata": {
    "model_version": "1.0.0",
    "last_updated": "2025-06-12T20:45:11.596625",
    "features_used": ["day_of_week"],
    "data_source": "ml_model"
  }
}
```

## データ型定義

### 基本予測データ

- `density_rate`: 人口密度率（0-100%）
- `occupied_seats`: 占有座席数（整数）
- `occupancy_rate`: 占有率（0-1.0、density_rate を 100 で割った値）
- `available_seats`: 利用可能な座席数（100 - occupied_seats）
- `status`: 混雑状況（"available", "moderate", "busy"）
- `confidence`: 予測信頼度（"low", "medium", "high"）

### モデル情報

- `model_version`: モデルバージョン
- `features_used`: 予測に使用された特徴量
- `data_points`: 訓練に使用されたデータポイント数

## フロントエンドとの連携について

フロントエンドアプリケーションは主に `/api/predictions/today-tomorrow` と `/api/predictions/weekly-average` エンドポイントを使用して予測データを取得します。API の仕様に変更がある場合は、フロントエンドコードも合わせて更新する必要があります。

現在のフロントエンドは、各曜日の密度率と占有座席数を表示し、週間の傾向をグラフで可視化する機能を提供しています。
