# Supabase 設定ガイド

## 🔧 Vercel 環境変数の設定

### 1. Vercel ダッシュボードにアクセス

1. [Vercel Dashboard](https://vercel.com/dashboard)にログイン
2. `real-time-seating-app-ml`プロジェクトを選択
3. **Settings** → **Environment Variables**に移動

### 2. 環境変数を追加

以下の環境変数を追加してください：

| 変数名              | 値                                        | 説明                        |
| ------------------- | ----------------------------------------- | --------------------------- |
| `SUPABASE_URL`      | `https://your-project.supabase.co`        | Supabase プロジェクトの URL |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Supabase 匿名キー           |

### 3. Supabase 設定の確認

#### Supabase プロジェクト設定

1. [Supabase Dashboard](https://supabase.com/dashboard)にログイン
2. プロジェクトを選択
3. **Settings** → **API**で以下を確認：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

#### テーブル構造の確認

`density_history`テーブルが以下の構造になっていることを確認：

```sql
CREATE TABLE density_history (
    id SERIAL PRIMARY KEY,
    density FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. API テスト

環境変数設定後、以下のエンドポイントでテスト：

- **ヘルスチェック**: `https://real-time-seating-app-ml.vercel.app/health`
- **今日・明日予測**: `https://real-time-seating-app-ml.vercel.app/predictions/today-tomorrow`
- **週間平均**: `https://real-time-seating-app-ml.vercel.app/predictions/weekly-average`

### 5. データ確認

#### ✅ 正常な場合

API レスポンスの`metadata`セクションで以下を確認：

```json
{
  "success": true,
  "metadata": {
    "data_source": "supabase_historical_data", // ← これが表示されればOK
    "historical_records_used": 150, // ← 実際のデータ件数
    "confidence": "high" // ← データ品質
  }
}
```

#### ❌ エラーの場合

```json
{
  "success": false,
  "error": "Supabaseからデータを取得できませんでした",
  "message": "Supabaseデータベースの設定を確認してください"
}
```

## 🚨 トラブルシューティング

### データが取得できない場合

- **HTTP 500 エラー**: Supabase の設定に問題がある
- **データ不足エラー**: `density_history`テーブルにデータが不足している

### よくあるエラー

1. **401 Unauthorized**: `SUPABASE_ANON_KEY`が間違っている
2. **404 Not Found**: `SUPABASE_URL`が間違っている
3. **Timeout**: Supabase への接続がタイムアウト
4. **Empty Data**: テーブルにデータが存在しない

### 解決方法

1. 環境変数の値を再確認
2. Supabase プロジェクトが稼働中か確認
3. テーブル名とカラム名を確認
4. **重要**: `density_history`テーブルにデータが存在することを確認

## 📊 データ要件

### 必須データ構造

```sql
-- 最低限必要なデータ例
INSERT INTO density_history (density, created_at) VALUES
(45.5, '2024-01-15 09:00:00+00'),
(67.2, '2024-01-15 10:00:00+00'),
(82.1, '2024-01-15 11:00:00+00');
```

### データ品質の向上

#### より良い予測のために

1. **定期的なデータ収集**: 1 時間ごとに density_history テーブルにデータを挿入
2. **データの多様性**: 平日・週末、時間帯別のデータを蓄積
3. **データクリーニング**: 異常値や欠損値の処理

#### 推奨データ量

- **最低**: 各曜日・各時間帯で 3 件以上
- **理想**: 各曜日・各時間帯で 10 件以上
- **期間**: 過去 30 日間のデータ

### データ不足時の動作

#### 🔄 新しい仕様（シミュレーションなし）

- **データがない時間帯**: `"status": "no_data"`として表示
- **データがない曜日**: `"daily_average_occupancy": null`として表示
- **完全にデータがない場合**: HTTP 500 エラーを返す

#### 📈 信頼度レベル

- **high**: 10 件以上のデータ
- **medium**: 5-9 件のデータ
- **low**: 2-4 件のデータ
- **very_low**: 1 件のデータ
- **none**: データなし

## 🎯 運用開始の手順

### 1. 初期データの投入

```sql
-- サンプルデータの投入（テスト用）
INSERT INTO density_history (density, created_at)
SELECT
    RANDOM() * 100 as density,
    NOW() - INTERVAL '1 hour' * generate_series(1, 168) as created_at;
```

### 2. 定期データ収集の設定

実際の座席センサーやカメラからのデータを 1 時間ごとに`density_history`テーブルに挿入する仕組みを構築してください。

### 3. API 動作確認

全てのエンドポイントが正常に動作し、実データに基づく予測が生成されることを確認してください。
