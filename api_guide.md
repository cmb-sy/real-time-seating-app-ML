# フロントエンド API 連携ガイド

## はじめに

このガイドでは、フロントエンド（Next.js）からバックエンド API（Vercel 上の Serverless Functions）に接続する際の設定と呼び出し方法について説明します。

## 重要な更新（2023 年 6 月）

API の構造を以下のように変更しました：

- Vercel のサーバーレス関数を使用したシンプルな実装に変更
- 各エンドポイントは `/api/` プレフィックスで始まります
- 主要エンドポイントは：
  - `/api/health` - ヘルスチェック
  - `/api/predictions/today-tomorrow` - 今日と明日の予測
  - `/api/predictions/weekly-average` - 週間平均予測

## API 接続設定

### 1. 正しい API エンドポイント URL

Vercel にデプロイされたバックエンドに接続する場合、以下の URL パターンを使用してください：

```javascript
// 環境変数からAPIのベースURLを取得
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://real-time-seating-app-ml.vercel.app";

// 正しいエンドポイントパス
const healthCheckEndpoint = `${API_BASE_URL}/api/health`;
const todayTomorrowPredictionsEndpoint = `${API_BASE_URL}/api/predictions/today-tomorrow`;
const weeklyAveragePredictionsEndpoint = `${API_BASE_URL}/api/predictions/weekly-average`;
```

### 2. fetch リクエストの設定例

```javascript
// 例: ヘルスチェックAPI呼び出し
async function checkAPIHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Origin: window.location.origin, // 現在のオリジンを送信
      },
      credentials: "omit", // CORSの問題を避けるため
    });

    if (!response.ok) {
      throw new Error(
        `API接続エラー: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("API接続エラー:", error);
    // ユーザーフレンドリーなエラーハンドリング
    throw new Error(
      "サーバーとの通信に失敗しました。しばらく待ってから再試行してください。"
    );
  }
}
```

### 3. 環境変数の設定

Next.js プロジェクトの`.env.local`ファイルに以下を追加：

```
NEXT_PUBLIC_API_URL=https://real-time-seating-app-ml.vercel.app
```

## 重要なポイント

1. **パスの指定**: すべての API エンドポイントは `/api/` プレフィックスを含めてください
2. **エラーハンドリング**: 常に try/catch ブロックでエラーをキャッチし、ユーザーフレンドリーなメッセージを表示
3. **CORS 対応**: Origin ヘッダーの設定と credentials: 'omit' の使用
4. **ローディング状態**: API リクエスト中はローディング状態を表示

## 利用可能なエンドポイント

| 機能             | エンドポイント                  | メソッド | 説明                 |
| ---------------- | ------------------------------- | -------- | -------------------- |
| ルート情報       | /api                            | GET      | API の概要情報       |
| ヘルスチェック   | /api/health                     | GET      | API の状態確認       |
| 今日・明日の予測 | /api/predictions/today-tomorrow | GET      | 今日と明日の混雑予測 |
| 週間平均予測     | /api/predictions/weekly-average | GET      | 曜日ごとの平均予測   |

## トラブルシューティング

### CORS エラー

```
Access to fetch at 'https://real-time-seating-app-ml.vercel.app/health' from origin 'https://v0-real-time-seating-app.vercel.app' has been blocked by CORS policy
```

**解決策**:

1. API エンドポイントのパスが正しいか確認（`/api/health`を使用）
2. API サーバーが稼働しているか確認
3. `credentials: 'omit'` を設定
4. 必要に応じてバックエンド管理者に連絡

### 404 エラー

```
GET https://real-time-seating-app-ml.vercel.app/health 404 (Not Found)
```

**解決策**:

1. エンドポイントを `/api/health` に変更
2. API URL が正しいか確認

### Failed to fetch

```
API接続エラー: TypeError: Failed to fetch
```

**解決策**:

1. インターネット接続を確認
2. API URL が正しいか確認
3. バックエンドサーバーが稼働しているか確認
