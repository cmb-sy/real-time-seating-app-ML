# フロントエンド・バックエンド接続ガイド

## 🌐 API エンドポイント

### 本番環境（Vercel）

```
https://your-vercel-app.vercel.app/
```

### ローカル開発環境

```
http://localhost:8080/
```

## 📡 利用可能な API

### 1. 今日・明日の予測 API

**エンドポイント:**

- `/predictions/today-tomorrow`
- `/api/predictions/today-tomorrow`

**メソッド:** GET

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "today": {
      "date": "2024-01-15",
      "day_of_week": "月",
      "occupancy_rate": 0.65,
      "occupied_seats": 5
    },
    "tomorrow": {
      "date": "2024-01-16",
      "day_of_week": "火",
      "occupancy_rate": 0.75,
      "occupied_seats": 6
    }
  }
}
```

### 2. 週間平均予測 API

**エンドポイント:**

- `/predictions/weekly-average`
- `/api/predictions/weekly-average`

**メソッド:** GET

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "weekly_averages": [
      {
        "day_of_week": "月",
        "occupancy_rate": 0.6,
        "occupied_seats": 5
      },
      {
        "day_of_week": "火",
        "occupancy_rate": 0.7,
        "occupied_seats": 6
      }
    ]
  }
}
```

## 💻 フロントエンド実装例

### JavaScript (Vanilla)

```javascript
// 今日・明日の予測を取得
async function getTodayTomorrowPrediction() {
  try {
    const response = await fetch("/api/predictions/today-tomorrow");
    const data = await response.json();

    if (data.success) {
      console.log("今日の占有席数:", data.data.today.occupied_seats);
      console.log("明日の占有席数:", data.data.tomorrow?.occupied_seats);
      return data.data;
    } else {
      console.error("エラー:", data.error);
    }
  } catch (error) {
    console.error("API呼び出しエラー:", error);
  }
}

// 週間平均を取得
async function getWeeklyAverage() {
  try {
    const response = await fetch("/api/predictions/weekly-average");
    const data = await response.json();

    if (data.success) {
      data.data.weekly_averages.forEach((day) => {
        console.log(`${day.day_of_week}: ${day.occupied_seats}席占有`);
      });
      return data.data.weekly_averages;
    }
  } catch (error) {
    console.error("API呼び出しエラー:", error);
  }
}

// 使用例
getTodayTomorrowPrediction().then((data) => {
  // UIを更新
  updateSeatingDisplay(data);
});
```

### React

```jsx
import React, { useState, useEffect } from "react";

const SeatingPrediction = () => {
  const [todayTomorrow, setTodayTomorrow] = useState(null);
  const [weeklyAverage, setWeeklyAverage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);

      // 今日・明日の予測
      const todayResponse = await fetch("/api/predictions/today-tomorrow");
      const todayData = await todayResponse.json();

      // 週間平均
      const weeklyResponse = await fetch("/api/predictions/weekly-average");
      const weeklyData = await weeklyResponse.json();

      if (todayData.success) setTodayTomorrow(todayData.data);
      if (weeklyData.success) setWeeklyAverage(weeklyData.data.weekly_averages);
    } catch (error) {
      console.error("予測データの取得に失敗:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>読み込み中...</div>;

  return (
    <div className="seating-prediction">
      <h2>座席予測</h2>

      {/* 今日・明日の予測 */}
      {todayTomorrow && (
        <div className="today-tomorrow">
          <h3>今日・明日の予測</h3>
          <div className="prediction-card">
            <h4>今日 ({todayTomorrow.today.day_of_week})</h4>
            <p>占有席数: {todayTomorrow.today.occupied_seats}/8席</p>
            <p>
              占有率: {(todayTomorrow.today.occupancy_rate * 100).toFixed(1)}%
            </p>
          </div>

          {todayTomorrow.tomorrow && (
            <div className="prediction-card">
              <h4>明日 ({todayTomorrow.tomorrow.day_of_week})</h4>
              <p>占有席数: {todayTomorrow.tomorrow.occupied_seats}/8席</p>
              <p>
                占有率:{" "}
                {(todayTomorrow.tomorrow.occupancy_rate * 100).toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* 週間平均 */}
      {weeklyAverage && (
        <div className="weekly-average">
          <h3>週間平均</h3>
          {weeklyAverage.map((day) => (
            <div key={day.day_of_week} className="day-card">
              <span>{day.day_of_week}曜日</span>
              <span>{day.occupied_seats}/8席</span>
              <span>{(day.occupancy_rate * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SeatingPrediction;
```

### Vue.js

```vue
<template>
  <div class="seating-prediction">
    <h2>座席予測</h2>

    <div v-if="loading">読み込み中...</div>

    <!-- 今日・明日の予測 -->
    <div v-if="todayTomorrow" class="today-tomorrow">
      <h3>今日・明日の予測</h3>
      <div class="prediction-card">
        <h4>今日 ({{ todayTomorrow.today.day_of_week }})</h4>
        <p>占有席数: {{ todayTomorrow.today.occupied_seats }}/8席</p>
        <p>
          占有率: {{ (todayTomorrow.today.occupancy_rate * 100).toFixed(1) }}%
        </p>
      </div>

      <div v-if="todayTomorrow.tomorrow" class="prediction-card">
        <h4>明日 ({{ todayTomorrow.tomorrow.day_of_week }})</h4>
        <p>占有席数: {{ todayTomorrow.tomorrow.occupied_seats }}/8席</p>
        <p>
          占有率:
          {{ (todayTomorrow.tomorrow.occupancy_rate * 100).toFixed(1) }}%
        </p>
      </div>
    </div>

    <!-- 週間平均 -->
    <div v-if="weeklyAverage" class="weekly-average">
      <h3>週間平均</h3>
      <div v-for="day in weeklyAverage" :key="day.day_of_week" class="day-card">
        <span>{{ day.day_of_week }}曜日</span>
        <span>{{ day.occupied_seats }}/8席</span>
        <span>{{ (day.occupancy_rate * 100).toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "SeatingPrediction",
  data() {
    return {
      todayTomorrow: null,
      weeklyAverage: null,
      loading: true,
    };
  },
  async mounted() {
    await this.fetchPredictions();
  },
  methods: {
    async fetchPredictions() {
      try {
        this.loading = true;

        // 今日・明日の予測
        const todayResponse = await fetch("/api/predictions/today-tomorrow");
        const todayData = await todayResponse.json();

        // 週間平均
        const weeklyResponse = await fetch("/api/predictions/weekly-average");
        const weeklyData = await weeklyResponse.json();

        if (todayData.success) this.todayTomorrow = todayData.data;
        if (weeklyData.success)
          this.weeklyAverage = weeklyData.data.weekly_averages;
      } catch (error) {
        console.error("予測データの取得に失敗:", error);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
```

## 🎨 CSS 例

```css
.seating-prediction {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.prediction-card,
.day-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.day-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.today-tomorrow {
  margin-bottom: 32px;
}

.weekly-average {
  margin-top: 32px;
}

/* 占有率に応じた色分け */
.occupancy-low {
  color: #4caf50;
} /* 緑: 空いている */
.occupancy-medium {
  color: #ff9800;
} /* オレンジ: 普通 */
.occupancy-high {
  color: #f44336;
} /* 赤: 混雑 */
```

## 🔧 開発環境での接続

### 1. ローカル API サーバー起動

```bash
# 今日・明日の予測API
python3 src/api/predictions_today_tomorrow.py --port 8080

# 週間平均予測API
python3 src/api/predictions_weekly_average.py --port 8081
```

### 2. プロキシ設定（開発時）

**Next.js (next.config.js):**

```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8080/:path*",
      },
    ];
  },
};
```

**Vite (vite.config.js):**

```javascript
export default {
  server: {
    proxy: {
      "/api": "http://localhost:8080",
    },
  },
};
```

## 🚀 本番環境デプロイ

1. **Vercel にデプロイ**
2. **フロントエンドから相対パスで API 呼び出し**
3. **CORS 設定は既に対応済み**

## 📊 データ形式の理解

- **occupancy_rate**: 0.0-1.0 の小数（0.65 = 65%）
- **occupied_seats**: 0-8 の整数（実際の占有席数）
- **day_of_week**: 日本語の曜日名（月、火、水、木、金）
- **平日のみ対応**: 土日は営業していません

これで、フロントエンドからバックエンド API に簡単に接続できます！
