# フロントエンド - API 連携ガイド

リアルタイム座席アプリのフロントエンドと ML API の連携に関する包括的なドキュメントです。

## 📋 目次

1. [API 概要](#api概要)
2. [ベース URL](#ベースurl)
3. [認証](#認証)
4. [エラーハンドリング](#エラーハンドリング)
5. [データ取得エンドポイント](#データ取得エンドポイント)
6. [分析エンドポイント](#分析エンドポイント)
7. [機械学習予測エンドポイント](#機械学習予測エンドポイント)
8. [フロントエンド統合例](#フロントエンド統合例)
9. [TypeScript/Next.js 実装例](#typescriptnextjs実装例)

## 🌐 API 概要

**API 名**: Real-time Seating App ML API  
**バージョン**: 1.0.0  
**説明**: リアルタイム座席アプリの機械学習予測とデータ分析 API

## 🔗 ベース URL

```
http://localhost:8000  (開発環境)
```

## 🔐 認証

現在、認証は不要です。全てのエンドポイントはパブリックアクセス可能です。

## ⚠️ エラーハンドリング

API は標準的な HTTP ステータスコードを使用します：

- `200`: 成功
- `400`: 不正なリクエスト
- `404`: リソースが見つからない
- `500`: サーバー内部エラー
- `503`: サービス利用不可

エラーレスポンス例：

```json
{
  "detail": {
    "success": false,
    "error": "エラーの種類",
    "message": "詳細なエラーメッセージ"
  }
}
```

---

## 🗄️ データ取得エンドポイント

### 1. ヘルスチェック

**エンドポイント**: `GET /health`  
**目的**: API 及びデータベースの接続状況確認

**リクエスト例**:

```javascript
fetch("http://localhost:8000/health");
```

**レスポンス例**:

```json
{
  "status": "healthy",
  "database": "connected",
  "models_loaded": true,
  "available_models": ["density_model", "seats_model"],
  "message": "APIとデータベースが正常に動作しています"
}
```

### 2. 全密度履歴データ取得

**エンドポイント**: `GET /density_history`  
**目的**: Supabase から全ての密度履歴データを取得

**リクエスト例**:

```javascript
fetch("http://localhost:8000/density_history");
```

**レスポンス例**:

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

### 3. 最新データ取得

**エンドポイント**: `GET /density_history/recent/{limit}`  
**パラメータ**:

- `limit` (int): 取得件数（デフォルト: 10）

**リクエスト例**:

```javascript
fetch("http://localhost:8000/density_history/recent/5");
```

**レスポンス例**:

```json
{
  "success": true,
  "count": 5,
  "limit": 5,
  "data": [
    {
      "id": 110,
      "occupied_seats": 8,
      "density_rate": 30.0,
      "created_at": "2025-06-11T08:19:08+00:00",
      "day_of_week": 3
    }
  ],
  "message": "最新 5 件のデータを取得しました"
}
```

### 4. データ件数取得

**エンドポイント**: `GET /density_history/count`

**リクエスト例**:

```javascript
fetch("http://localhost:8000/density_history/count");
```

**レスポンス例**:

```json
{
  "success": true,
  "count": 54,
  "message": "density_historyテーブルには 54 件のレコードがあります"
}
```

---

## 📊 分析エンドポイント

### 1. 基本統計情報

**エンドポイント**: `GET /analysis/basic_statistics`  
**目的**: データの基本統計情報を取得

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/basic_statistics");
```

**レスポンス例**:

```json
{
  "success": true,
  "data": {
    "total_records": 54,
    "weekday_records": 54,
    "date_range": {
      "start": "2025-04-01",
      "end": "2025-06-11"
    },
    "density_rate_stats": {
      "mean": 32.78,
      "median": 38.0,
      "std": 14.92,
      "min": 10.0,
      "max": 50.0
    },
    "occupied_seats_stats": {
      "mean": 2.94,
      "median": 3.0,
      "std": 1.34,
      "min": 1,
      "max": 8
    }
  },
  "message": "基本統計情報を取得しました"
}
```

### 2. 曜日別分析

**エンドポイント**: `GET /analysis/weekday_analysis`  
**目的**: 曜日別の詳細分析結果

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/weekday_analysis");
```

### 3. 月別分析

**エンドポイント**: `GET /analysis/monthly`  
**目的**: 月別の統計情報

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/monthly");
```

**レスポンス例**:

```json
{
  "success": true,
  "data": {
    "2025-04": {
      "レコード数": 18,
      "density_rate": {
        "平均": 35.22,
        "中央値": 38.0,
        "標準偏差": 13.85,
        "最小": 13.0,
        "最大": 50.0
      },
      "occupied_seats": {
        "平均": 2.89,
        "中央値": 3.0,
        "標準偏差": 1.28,
        "最小": 1,
        "最大": 4
      }
    }
  },
  "message": "月別分析を実行しました"
}
```

### 4. 月別平均値

**エンドポイント**: `GET /analysis/monthly_averages`  
**目的**: 月別の平均値データ

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/monthly_averages");
```

### 5. 曜日別可視化データ

**エンドポイント**: `GET /analysis/weekday_visualization`  
**目的**: フロントエンドでのグラフ作成用データ

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/weekday_visualization");
```

### 6. 相関分析

**エンドポイント**: `GET /analysis/correlation`  
**目的**: 変数間の相関分析結果

**リクエスト例**:

```javascript
fetch("http://localhost:8000/analysis/correlation");
```

---

## 🤖 機械学習予測エンドポイント

### 1. 曜日予測

**エンドポイント**: `GET /ml/predict?day_of_week={0-4}`  
**パラメータ**:

- `day_of_week` (int): 曜日（0=月曜, 1=火曜, 2=水曜, 3=木曜, 4=金曜）

**リクエスト例**:

```javascript
// 火曜日の予測
fetch("http://localhost:8000/ml/predict?day_of_week=1");
```

**レスポンス例**:

```json
{
  "success": true,
  "day_of_week": 1,
  "weekday_name": "火曜",
  "predictions": {
    "density_rate": 35.42,
    "occupied_seats": 3
  },
  "message": "火曜の予測を生成しました"
}
```

### 2. 日別予測スケジュール

**エンドポイント**: `GET /ml/predict_schedule?day_of_week={0-4}`  
**パラメータ**:

- `day_of_week` (int): 曜日（0-4）

**リクエスト例**:

```javascript
// 水曜日の24時間予測
fetch("http://localhost:8000/ml/predict_schedule?day_of_week=2");
```

**レスポンス例**:

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
          "density_rate": 32.15,
          "occupied_seats": 3
        }
      },
      {
        "hour": 1,
        "time": "01:00",
        "predictions": {
          "density_rate": 32.15,
          "occupied_seats": 3
        }
      }
      // ... 24時間分
    ]
  },
  "message": "水曜の1日予測スケジュールを作成しました"
}
```

### 3. モデル情報取得

**エンドポイント**: `GET /ml/model_info`  
**目的**: 学習済みモデルの詳細情報

**リクエスト例**:

```javascript
fetch("http://localhost:8000/ml/model_info");
```

### 4. 包括的フロントエンドデータ生成

**エンドポイント**: `POST /generate_frontend_data`  
**目的**: 分析結果、予測データ、可視化データの一括取得

**リクエスト例**:

```javascript
fetch("http://localhost:8000/generate_frontend_data", {
  method: "POST",
});
```

---

## 🔧 TypeScript/Next.js 実装例

### API 型定義

```typescript
// types/api.ts
export interface DensityHistoryRecord {
  id: number;
  occupied_seats: number;
  density_rate: number;
  created_at: string;
  day_of_week: number;
}

export interface PredictionResponse {
  success: boolean;
  day_of_week: number;
  weekday_name: string;
  predictions: {
    density_rate: number;
    occupied_seats: number;
  };
  message: string;
}

export interface SchedulePrediction {
  hour: number;
  time: string;
  predictions: {
    density_rate: number;
    occupied_seats: number;
  };
}

export interface ScheduleResponse {
  success: boolean;
  data: {
    day_of_week: number;
    weekday_name: string;
    schedule: SchedulePrediction[];
  };
  message: string;
}

export interface MonthlyAnalysis {
  [yearMonth: string]: {
    レコード数: number;
    density_rate: {
      平均: number;
      中央値: number;
      標準偏差: number;
      最小: number;
      最大: number;
    };
    occupied_seats: {
      平均: number;
      中央値: number;
      標準偏差: number;
      最小: number;
      最大: number;
    };
  };
}
```

### API クライアント実装

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class SeatingAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // ヘルスチェック
  async checkHealth() {
    const response = await fetch(`${this.baseURL}/health`);
    return response.json();
  }

  // 密度履歴データ取得
  async getDensityHistory(): Promise<DensityHistoryRecord[]> {
    const response = await fetch(`${this.baseURL}/density_history`);
    return response.json();
  }

  // 最新データ取得
  async getRecentData(limit: number = 10) {
    const response = await fetch(
      `${this.baseURL}/density_history/recent/${limit}`
    );
    return response.json();
  }

  // 曜日予測取得
  async getPrediction(dayOfWeek: number): Promise<PredictionResponse> {
    const response = await fetch(
      `${this.baseURL}/ml/predict?day_of_week=${dayOfWeek}`
    );
    return response.json();
  }

  // 日別スケジュール予測
  async getSchedulePrediction(dayOfWeek: number): Promise<ScheduleResponse> {
    const response = await fetch(
      `${this.baseURL}/ml/predict_schedule?day_of_week=${dayOfWeek}`
    );
    return response.json();
  }

  // 基本統計情報
  async getBasicStatistics() {
    const response = await fetch(`${this.baseURL}/analysis/basic_statistics`);
    return response.json();
  }

  // 月別分析
  async getMonthlyAnalysis() {
    const response = await fetch(`${this.baseURL}/analysis/monthly`);
    return response.json();
  }

  // 月別平均値
  async getMonthlyAverages() {
    const response = await fetch(`${this.baseURL}/analysis/monthly_averages`);
    return response.json();
  }

  // 曜日別可視化データ
  async getWeekdayVisualization() {
    const response = await fetch(
      `${this.baseURL}/analysis/weekday_visualization`
    );
    return response.json();
  }

  // 包括的データ生成
  async generateFrontendData() {
    const response = await fetch(`${this.baseURL}/generate_frontend_data`, {
      method: "POST",
    });
    return response.json();
  }
}

export const api = new SeatingAPI();
```

### React Hook 実装

```typescript
// hooks/useSeatingData.ts
import { useState, useEffect } from "react";
import { api } from "../lib/api";
import type { PredictionResponse, MonthlyAnalysis } from "../types/api";

export const useSeatingPrediction = (dayOfWeek: number) => {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPrediction = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getPrediction(dayOfWeek);
        setPrediction(data);
      } catch (err) {
        setError("予測データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    };

    if (dayOfWeek >= 0 && dayOfWeek <= 4) {
      fetchPrediction();
    }
  }, [dayOfWeek]);

  return { prediction, loading, error };
};

export const useMonthlyAnalysis = () => {
  const [data, setData] = useState<MonthlyAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.getMonthlyAnalysis();
        setData(response.data);
      } catch (err) {
        setError("月別分析データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};
```

### コンポーネント使用例

```typescript
// components/PredictionDisplay.tsx
import React from "react";
import { useSeatingPrediction } from "../hooks/useSeatingData";

interface Props {
  selectedDay: number;
}

const PredictionDisplay: React.FC<Props> = ({ selectedDay }) => {
  const { prediction, loading, error } = useSeatingPrediction(selectedDay);

  if (loading) return <div>予測を読み込み中...</div>;
  if (error) return <div>エラー: {error}</div>;
  if (!prediction) return <div>予測データがありません</div>;

  return (
    <div className="prediction-card">
      <h3>{prediction.weekday_name}の予測</h3>
      <div className="prediction-values">
        <div>
          <label>密度率:</label>
          <span>{prediction.predictions.density_rate}%</span>
        </div>
        <div>
          <label>占有座席数:</label>
          <span>{prediction.predictions.occupied_seats}席</span>
        </div>
      </div>
    </div>
  );
};

export default PredictionDisplay;
```

---

## 📈 フロントエンド統合シナリオ

### 1. ダッシュボード初期化時

```javascript
// ページロード時の処理
async function initializeDashboard() {
  try {
    // 1. ヘルスチェック
    const health = await api.checkHealth();
    console.log("API Status:", health.status);

    // 2. 基本統計情報取得
    const stats = await api.getBasicStatistics();

    // 3. 最新データ取得
    const recentData = await api.getRecentData(10);

    // 4. 今日の曜日で予測取得
    const today = new Date().getDay(); // 0=日曜, 1=月曜...
    const weekday = today === 0 ? 4 : today - 1; // 土日は金曜の予測
    const prediction = await api.getPrediction(weekday);

    // ダッシュボードに反映
    updateDashboard({ stats, recentData, prediction });
  } catch (error) {
    console.error("Dashboard initialization failed:", error);
  }
}
```

### 2. 曜日別分析表示

```javascript
// 曜日切り替え時の処理
async function displayWeekdayAnalysis(dayOfWeek) {
  try {
    // 予測データ取得
    const prediction = await api.getPrediction(dayOfWeek);

    // スケジュール取得
    const schedule = await api.getSchedulePrediction(dayOfWeek);

    // グラフ用データ取得
    const visualizationData = await api.getWeekdayVisualization();

    // UI更新
    updateWeekdayDisplay({ prediction, schedule, visualizationData });
  } catch (error) {
    console.error("Failed to load weekday data:", error);
  }
}
```

### 3. 月別レポート生成

```javascript
// 月別レポート表示
async function generateMonthlyReport() {
  try {
    // 月別分析取得
    const monthlyAnalysis = await api.getMonthlyAnalysis();

    // 月別平均値取得
    const monthlyAverages = await api.getMonthlyAverages();

    // レポート生成
    generateReport({ monthlyAnalysis, monthlyAverages });
  } catch (error) {
    console.error("Failed to generate monthly report:", error);
  }
}
```

---

## 🚀 パフォーマンス最適化

### キャッシュ戦略

```javascript
// データキャッシュ実装例
class DataCache {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5分
  }

  async get(key, fetchFunction) {
    const cached = this.cache.get(key);
    const now = Date.now();

    if (cached && now - cached.timestamp < this.ttl) {
      return cached.data;
    }

    const data = await fetchFunction();
    this.cache.set(key, { data, timestamp: now });
    return data;
  }
}

const cache = new DataCache();

// 使用例
const getBasicStats = () =>
  cache.get("basic_stats", () => api.getBasicStatistics());
```

---

## 📝 まとめ

この API は以下の主要機能を提供します：

1. **データ取得**: 履歴データ、統計情報、分析結果
2. **機械学習予測**: 曜日別の密度率・占有座席数予測
3. **分析機能**: 月別、曜日別、相関分析
4. **可視化サポート**: グラフ作成用データ提供

フロントエンドでは、これらの API を組み合わせることで：

- リアルタイムダッシュボード
- 予測表示
- 分析レポート
- 可視化グラフ

を実現できます。

すべてのエンドポイントは TypeScript の型安全性をサポートし、エラーハンドリングとパフォーマンス最適化も考慮された設計となっています。
