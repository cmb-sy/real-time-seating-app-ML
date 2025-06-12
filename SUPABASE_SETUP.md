# Supabase 設定ガイド（平日営業版）

## 🏢 営業時間・対応日

- **営業日**: 月曜日〜金曜日（平日のみ）
- **営業時間**: 9:00〜18:00
- **休業日**: 土曜日・日曜日

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

#### ✅ 正常な場合（平日）

API レスポンスの`metadata`セクションで以下を確認：

```json
{
  "success": true,
  "metadata": {
    "data_source": "supabase_historical_data", // ← これが表示されればOK
    "historical_records_used": 150, // ← 実際のデータ件数
    "confidence": "high", // ← データ品質
    "weekday_only": true // ← 平日のみ対応
  }
}
```

#### ❌ エラーの場合

```json
{
  "success": false,
  "error": "土日は営業していません。平日（月-金）のみ予測を提供しています。",
  "message": "Supabaseデータベースの設定を確認してください"
}
```

## 🚨 トラブルシューティング

### データが取得できない場合

- **HTTP 500 エラー**: Supabase の設定に問題がある
- **データ不足エラー**: `density_history`テーブルにデータが不足している
- **土日エラー**: 土日にアクセスした場合（仕様通り）

### よくあるエラー

1. **401 Unauthorized**: `SUPABASE_ANON_KEY`が間違っている
2. **404 Not Found**: `SUPABASE_URL`が間違っている
3. **Timeout**: Supabase への接続がタイムアウト
4. **Empty Data**: テーブルにデータが存在しない
5. **Weekend Access**: 土日にアクセスした場合

### 解決方法

1. 環境変数の値を再確認
2. Supabase プロジェクトが稼働中か確認
3. テーブル名とカラム名を確認
4. **重要**: `density_history`テーブルに**平日のデータ**が存在することを確認

## 📊 データ要件（平日のみ）

### 必須データ構造

```sql
-- 平日のデータ例（月曜日〜金曜日）
INSERT INTO density_history (density, created_at) VALUES
-- 月曜日のデータ
(45.5, '2024-01-15 09:00:00+00'),  -- 月曜日 9時
(67.2, '2024-01-15 10:00:00+00'),  -- 月曜日 10時
-- 火曜日のデータ
(52.1, '2024-01-16 09:00:00+00'),  -- 火曜日 9時
(71.8, '2024-01-16 10:00:00+00');  -- 火曜日 10時
```

### データ品質の向上

#### より良い予測のために

1. **定期的なデータ収集**: 平日の 1 時間ごとに density_history テーブルにデータを挿入
2. **データの多様性**: 月〜金の各曜日、時間帯別のデータを蓄積
3. **データクリーニング**: 異常値や欠損値の処理

#### 推奨データ量（平日のみ）

- **最低**: 各平日・各時間帯で 3 件以上
- **理想**: 各平日・各時間帯で 10 件以上
- **期間**: 過去 30 日間の平日データ

### データ不足時の動作

#### 🔄 新しい仕様（平日のみ、シミュレーションなし）

- **土日アクセス**: エラーメッセージを返す
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

### 1. 初期データの投入（平日のみ）

```sql
-- 平日のサンプルデータの投入（テスト用）
INSERT INTO density_history (density, created_at)
SELECT
    RANDOM() * 100 as density,
    generate_series(
        '2024-01-01 09:00:00'::timestamp,
        '2024-01-31 18:00:00'::timestamp,
        '1 hour'::interval
    ) as created_at
WHERE EXTRACT(dow FROM generate_series(
    '2024-01-01 09:00:00'::timestamp,
    '2024-01-31 18:00:00'::timestamp,
    '1 hour'::interval
)) BETWEEN 1 AND 5;  -- 月曜日(1)〜金曜日(5)のみ
```

### 2. 定期データ収集の設定

実際の座席センサーやカメラからのデータを**平日の 1 時間ごと**に`density_history`テーブルに挿入する仕組みを構築してください。

### 3. API 動作確認

- 平日にアクセスして正常に予測が生成されることを確認
- 土日にアクセスしてエラーメッセージが表示されることを確認
- 実データに基づく予測が生成されることを確認
