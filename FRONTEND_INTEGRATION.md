# フロントエンド連携ガイド

## 概要

このガイドでは、2 週間ごとに更新される分析・予測データをフロントエンドアプリケーションと連携する方法について説明します。

## アーキテクチャ

```
[バックエンド API] ←→ [定期実行スケジューラー] ←→ [静的JSONファイル] ←→ [フロントエンド]
```

### データフロー

1. **定期実行（2 週間ごと）**

   - スケジューラーが API を呼び出し
   - 最新データで ML 模型を再訓練
   - 包括的な分析・予測データを生成
   - JSON ファイルとして保存

2. **フロントエンド読み込み**
   - 最新 JSON ファイルを取得
   - ダッシュボードに表示
   - 2 週間ごとに自動更新

## API エンドポイント

### 1. 包括データ生成

```http
POST /generate_frontend_data
```

**説明**: すべての分析結果と予測データを生成し、JSON ファイルとして保存

**レスポンス**:

```json
{
  "success": true,
  "data": {
    "metadata": {
      "generated_at": "2025-06-11T23:45:00.123456",
      "data_period": "2週間",
      "total_records": 54,
      "weekday_records": 54
    },
    "analysis": {
      "basic_statistics": {...},
      "weekday_analysis": {...},
      "correlation_analysis": {...},
      "daily_summary": {...}
    },
    "predictions": {
      "schedules": {...},
      "model_performance": {...}
    },
    "visualizations": {
      "file_paths": {...},
      "available": true
    }
  },
  "files": {
    "latest": "frontend_data/latest_data.json",
    "archive": "frontend_data/data_20250611_234500.json"
  },
  "message": "フロントエンド向けデータ生成が完了しました"
}
```

### 2. 最新データ取得

```http
GET /frontend_data/latest
```

**説明**: フロントエンドが最新のデータを取得するためのエンドポイント

**レスポンス**: 上記と同じデータ構造

## データ構造詳細

### メタデータ

```json
{
  "metadata": {
    "generated_at": "ISO8601形式の生成日時",
    "data_period": "データ期間（2週間）",
    "total_records": "総レコード数",
    "weekday_records": "平日レコード数"
  }
}
```

### 分析データ

```json
{
  "analysis": {
    "basic_statistics": {
      "overall": {
        "total_records": 54,
        "density_rate_mean": 34.07,
        "density_rate_std": 14.36,
        "occupied_seats_mean": 2.7,
        "occupied_seats_std": 1.19
      },
      "weekday": {...}
    },
    "weekday_analysis": {
      "月曜": {
        "count": 11,
        "density_rate_mean": 32.18,
        "occupied_seats_mean": 2.55
      },
      ...
    },
    "correlation_analysis": {
      "density_occupied_correlation": 0.749,
      "day_density_correlation": 0.123,
      "day_seats_correlation": 0.234
    },
    "daily_summary": {
      "月曜": {
        "day_of_week": 0,
        "average_density_rate": 32.5,
        "average_occupied_seats": 2.3,
        "peak_hour": {...},
        "low_hour": {...}
      },
      ...
    }
  }
}
```

### 予測データ

```json
{
  "predictions": {
    "schedules": {
      "月曜": {
        "day_of_week": 0,
        "weekday_name": "月曜",
        "schedule": [
          {
            "hour": 0,
            "time": "00:00",
            "predictions": {
              "density_rate": 32.5,
              "occupied_seats": 2
            }
          },
          ...
        ]
      },
      ...
    },
    "model_performance": {
      "density_model": {
        "test_rmse": 14.02,
        "test_r2": -0.012,
        "model_type": "random_forest"
      },
      "seats_model": {
        "test_rmse": 1.13,
        "test_r2": -0.001,
        "model_type": "random_forest"
      }
    }
  }
}
```

## 定期実行設定

### 1. 手動実行

```bash
# 強制実行（すぐにデータ生成）
python scheduler.py --mode force

# チェック実行（2週間経過していれば実行）
python scheduler.py --mode check
```

### 2. 継続監視

```bash
# バックグラウンドで継続監視（1日1回チェック）
nohup python scheduler.py --mode monitor &
```

### 3. cron 設定

```bash
# crontabに追加（2週間ごとの午前2時に実行）
0 2 */14 * * cd /path/to/project && python scheduler.py --mode check
```

## フロントエンド実装例

### React.js 例

```jsx
import React, { useState, useEffect } from "react";

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/frontend_data/latest");
        const result = await response.json();

        if (result.success) {
          setData(result.data);
          setLastUpdated(new Date(result.data.metadata.generated_at));
        }
      } catch (error) {
        console.error("データ取得エラー:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // 1時間ごとにチェック（ファイル更新確認）
    const interval = setInterval(fetchData, 60 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>読み込み中...</div>;

  return (
    <div className="dashboard">
      <h1>座席密度ダッシュボード</h1>
      <p>最終更新: {lastUpdated?.toLocaleString()}</p>

      {/* 基本統計 */}
      <section>
        <h2>基本統計</h2>
        <div>
          <p>
            平均密度率:{" "}
            {data?.analysis?.basic_statistics?.overall?.density_rate_mean}%
          </p>
          <p>
            平均占有座席数:{" "}
            {data?.analysis?.basic_statistics?.overall?.occupied_seats_mean}
          </p>
        </div>
      </section>

      {/* 曜日別予測 */}
      <section>
        <h2>今週の予測</h2>
        {Object.entries(data?.predictions?.schedules || {}).map(
          ([day, schedule]) => (
            <div key={day}>
              <h3>{day}</h3>
              <p>
                平均密度率:{" "}
                {data?.analysis?.daily_summary?.[day]?.average_density_rate}%
              </p>
              {/* 時間別グラフなどを表示 */}
            </div>
          )
        )}
      </section>
    </div>
  );
};

export default Dashboard;
```

### Vue.js 例

```vue
<template>
  <div class="dashboard">
    <h1>座席密度ダッシュボード</h1>
    <p>最終更新: {{ formatDate(lastUpdated) }}</p>

    <div v-if="loading">読み込み中...</div>

    <div v-else-if="data">
      <!-- 基本統計 -->
      <section>
        <h2>基本統計</h2>
        <div class="stats">
          <div>
            平均密度率:
            {{ data.analysis.basic_statistics.overall.density_rate_mean }}%
          </div>
          <div>
            平均占有座席数:
            {{ data.analysis.basic_statistics.overall.occupied_seats_mean }}
          </div>
        </div>
      </section>

      <!-- 曜日別サマリー -->
      <section>
        <h2>曜日別サマリー</h2>
        <div
          v-for="(summary, day) in data.analysis.daily_summary"
          :key="day"
          class="day-summary"
        >
          <h3>{{ day }}</h3>
          <p>平均密度率: {{ summary.average_density_rate }}%</p>
          <p>平均占有座席数: {{ summary.average_occupied_seats }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  name: "Dashboard",
  data() {
    return {
      data: null,
      loading: true,
      lastUpdated: null,
    };
  },
  async mounted() {
    await this.fetchData();

    // 1時間ごとにデータチェック
    setInterval(this.fetchData, 60 * 60 * 1000);
  },
  methods: {
    async fetchData() {
      try {
        const response = await fetch("/api/frontend_data/latest");
        const result = await response.json();

        if (result.success) {
          this.data = result.data;
          this.lastUpdated = new Date(result.data.metadata.generated_at);
        }
      } catch (error) {
        console.error("データ取得エラー:", error);
      } finally {
        this.loading = false;
      }
    },
    formatDate(date) {
      return date ? date.toLocaleString("ja-JP") : "";
    },
  },
};
</script>
```

## Nginx 設定例（静的ファイル配信）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # フロントエンドアプリ
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API プロキシ
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静的データファイル直接配信
    location /data/ {
        alias /path/to/backend/frontend_data/;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

## 運用上の注意点

1. **ファイルサイズ監視**: JSON ファイルが大きくなりすぎないよう監視
2. **バックアップ**: アーカイブファイルの定期バックアップ
3. **エラーハンドリング**: フロントエンドでのデータ取得失敗時の対応
4. **キャッシュ制御**: ブラウザキャッシュとデータ更新のタイミング調整
5. **ログ監視**: スケジューラーのログファイル定期確認

## トラブルシューティング

### よくある問題

1. **データが更新されない**

   - スケジューラーの動作状況確認
   - API サーバーの稼働確認
   - ファイル権限の確認

2. **フロントエンドでデータが表示されない**

   - JSON ファイルの存在確認
   - CORS 設定の確認
   - ネットワーク接続の確認

3. **パフォーマンス問題**
   - JSON ファイルサイズの確認
   - CDN 導入の検討
   - データ圧縮の検討

## 🎯 **フロントエンドとの具体的な連携方法**

### 1. **曜日指定予測 API（リアルタイム利用）**

フロントエンドから曜日を送信して予測を取得：

```javascript
// フロントエンドから曜日を指定して予測取得
const getPrediction = async (dayOfWeek, hour) => {
  const response = await fetch(
    `/api/ml/predict?day_of_week=${dayOfWeek}&hour=${hour}`
  );
  const result = await response.json();
  return result;
};

// 使用例: 月曜日の12時の予測
const prediction = await getPrediction(0, 12); // 0=月曜日
console.log(prediction);
// 出力例:
// {
//   "success": true,
//   "day_of_week": 0,
//   "weekday_name": "月曜",
//   "hour": 12,
//   "time": "12:00",
//   "density_rate": 32.5,
//   "occupied_seats": 2
// }
```

### 2. **包括的データ取得（ダッシュボード表示用）**

2 週間ごとに更新される分析結果を取得：

```javascript
// 最新の分析・予測データを取得
const getLatestData = async () => {
  const response = await fetch("/api/frontend_data/latest");
  const result = await response.json();
  return result.data;
};

// 使用例
const data = await getLatestData();
console.log(data.metadata.generated_at); // 最終更新日時
console.log(data.analysis.daily_summary); // 曜日別サマリー
console.log(data.predictions.schedules); // 24時間予測スケジュール
```

### 3. **フロントエンド実装例**

曜日選択機能付きのダッシュボード：

```jsx
import React, { useState, useEffect } from "react";

const WeekdayPredictor = () => {
  const [selectedDay, setSelectedDay] = useState(0); // 0=月曜日
  const [selectedHour, setSelectedHour] = useState(12);
  const [prediction, setPrediction] = useState(null);
  const [weeklyData, setWeeklyData] = useState(null);

  const weekdays = [
    { value: 0, name: "月曜日" },
    { value: 1, name: "火曜日" },
    { value: 2, name: "水曜日" },
    { value: 3, name: "木曜日" },
    { value: 4, name: "金曜日" },
  ];

  // 指定した曜日・時間の予測を取得
  const fetchPrediction = async () => {
    try {
      const response = await fetch(
        `/api/ml/predict?day_of_week=${selectedDay}&hour=${selectedHour}`
      );
      const result = await response.json();
      if (result.success) {
        setPrediction(result);
      }
    } catch (error) {
      console.error("予測取得エラー:", error);
    }
  };

  // 週間データを取得
  const fetchWeeklyData = async () => {
    try {
      const response = await fetch("/api/frontend_data/latest");
      const result = await response.json();
      if (result.success) {
        setWeeklyData(result.data);
      }
    } catch (error) {
      console.error("週間データ取得エラー:", error);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [selectedDay, selectedHour]);

  useEffect(() => {
    fetchWeeklyData();
  }, []);

  return (
    <div className="predictor">
      <h2>座席密度予測</h2>

      {/* 曜日選択 */}
      <div className="day-selector">
        <label>曜日選択:</label>
        <select
          value={selectedDay}
          onChange={(e) => setSelectedDay(parseInt(e.target.value))}
        >
          {weekdays.map((day) => (
            <option key={day.value} value={day.value}>
              {day.name}
            </option>
          ))}
        </select>
      </div>

      {/* 時間選択 */}
      <div className="hour-selector">
        <label>時間選択:</label>
        <input
          type="range"
          min="0"
          max="23"
          value={selectedHour}
          onChange={(e) => setSelectedHour(parseInt(e.target.value))}
        />
        <span>{selectedHour}:00</span>
      </div>

      {/* 予測結果表示 */}
      {prediction && (
        <div className="prediction-result">
          <h3>
            {prediction.weekday_name} {prediction.time}の予測
          </h3>
          <p>密度率: {prediction.density_rate.toFixed(1)}%</p>
          <p>占有座席数: {prediction.occupied_seats}席</p>
        </div>
      )}

      {/* 週間サマリー */}
      {weeklyData && (
        <div className="weekly-summary">
          <h3>今週のサマリー</h3>
          <p>
            最終更新:{" "}
            {new Date(weeklyData.metadata.generated_at).toLocaleString()}
          </p>

          {Object.entries(weeklyData.analysis.daily_summary).map(
            ([day, summary]) => (
              <div key={day} className="day-summary">
                <h4>{day}</h4>
                <p>平均密度率: {summary.predicted_average_density_rate}%</p>
                <p>平均座席数: {summary.predicted_average_occupied_seats}席</p>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default WeekdayPredictor;
```

### 4. **2 週間ごとの自動更新システム**

既に構築済みのスケジューラーが以下を自動実行：

```bash
# 2週間ごとの自動実行設定
# crontabに追加
0 2 */14 * * cd /path/to/project && python scheduler.py --mode check

# または継続監視モード
python scheduler.py --mode monitor
```

**実行内容:**

1. **新しいデータでモデル再訓練**
2. **ハイパーパラメータ最適化**
3. **分析結果の更新**
4. **予測データの更新**
5. **JSON ファイルの保存**

### 5. **データ構造（フロントエンドが受け取るデータ）**

```json
{
  "metadata": {
    "generated_at": "2025-06-11T23:42:54.148025",
    "data_period": "2週間",
    "total_records": 54,
    "weekday_records": 54
  },
  "analysis": {
    "daily_summary": {
      "月曜": {
        "day_of_week": 0,
        "predicted_average_density_rate": 32.5,
        "predicted_average_occupied_seats": 2.3
      },
      "火曜": { ... },
      "水曜": { ... },
      "木曜": { ... },
      "金曜": { ... }
    }
  },
  "predictions": {
    "schedules": {
      "月曜": {
        "day_of_week": 0,
        "schedule": [
          {
            "hour": 0,
            "time": "00:00",
            "predictions": {
              "density_rate": 32.5,
              "occupied_seats": 2
            }
          },
          // 24時間分のデータ
        ]
      }
      // 全曜日分のデータ
    }
  }
}
```

### 6. **運用フロー**

```
日常運用:
フロントエンド → 曜日指定 → リアルタイム予測取得

2週間ごと:
スケジューラー → データ更新 → モデル再訓練 → 新しい予測データ生成
               ↓
フロントエンド → 最新データ読み込み → ダッシュボード更新
```

この仕組みにより、フロントエンドから曜日を指定してリアルタイムで予測を取得でき、2 週間ごとにモデルと分析結果が自動更新される完全なシステムが構築されています！
