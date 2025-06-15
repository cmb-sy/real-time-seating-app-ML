# Supabase 統合における問題と解決方法

## 概要

リアルタイム座席予測アプリの ML API に Supabase を統合する際に発生した問題と、その解決方法

## 発生した問題

### 1. 依存関係の問題

**問題**:

- 初期実装では`supabase-py`ライブラリを使用しようとしました
- Vercel のサーバーレス環境で依存関係のインストールに失敗
- `psycopg2`などの PostgreSQL 関連の依存関係でエラーが発生

**エラー例**:

```
ModuleNotFoundError: No module named 'supabase'
```

### 2. 環境変数の管理問題

**問題**:

- Supabase URL と API Key の安全な管理が必要
- デバッグ時に機密情報がログに出力される危険性
- 本番環境と開発環境での設定の違い

### 3. データ取得の複雑さ

**問題**:

- Supabase からリアルタイムデータを取得する必要
- `density_seats_ratio`の計算が必要
- フォールバック機能の実装が必要

## 解決方法

### 1. HTTP REST API アプローチの採用

**解決策**: Supabase Python SDK の代わりに、直接 HTTP REST API を使用

```python
import requests
import os

def get_supabase_data():
    """Supabaseから直接HTTPでデータを取得"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')

    if not url or not key:
        return None

    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{url}/rest/v1/seating_data", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None
```

**メリット**:

- 軽量な実装（追加の依存関係不要）
- Vercel のサーバーレス環境で確実に動作
- エラーハンドリングが簡単

### 2. セキュアな環境変数管理

**実装**:

```python
# 環境変数の安全な取得
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# ログに機密情報を出力しない
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Supabase configuration missing")  # 具体的な値は出力しない
```

**セキュリティ対策**:

- API Key をログに出力しない
- 環境変数の存在チェックのみ実行
- エラー時は汎用的なメッセージを返す

### 3. リアルタイムデータ処理とフォールバック

**実装**:

```python
def calculate_density_seats_ratio(data):
    """リアルタイムデータからdensity_seats_ratioを計算"""
    if not data:
        return 0.5  # デフォルト値

    total_density = sum(record.get('density', 0) for record in data)
    total_seats = sum(record.get('total_seats', 0) for record in data)

    if total_seats == 0:
        return 0.5

    return total_density / total_seats

def get_predictions_with_fallback(features):
    """MLモデル予測とデータベース平均のフォールバック"""
    try:
        # MLモデルによる予測を試行
        predictions = make_ml_predictions(features)
        return {
            'predictions': predictions,
            'model_prediction': True,
            'source': 'ML Model'
        }
    except Exception:
        # フォールバック: データベース平均値を使用
        fallback_data = get_database_averages()
        return {
            'predictions': fallback_data,
            'model_prediction': False,
            'source': 'Database Average'
        }
```

## Vercel での環境変数設定

### 必要な環境変数

**はい、Vercel に以下の環境変数の設定が必要です**:

1. **SUPABASE_URL**

   - 値: `https://your-project-id.supabase.co`
   - 説明: Supabase プロジェクトの URL

2. **SUPABASE_ANON_KEY**
   - 値: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - 説明: Supabase の匿名キー（公開 API 用）

### Vercel での設定方法

1. **Vercel Dashboard から設定**:

   ```
   1. Vercelプロジェクトのダッシュボードにアクセス
   2. Settings → Environment Variables
   3. 以下を追加:
      - Name: SUPABASE_URL, Value: あなたのSupabase URL
      - Name: SUPABASE_ANON_KEY, Value: あなたのSupabase匿名キー
   4. Production, Preview, Developmentすべてにチェック
   5. Save
   ```

2. **Vercel CLI から設定**:
   ```bash
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_ANON_KEY
   ```

### セキュリティ考慮事項

**匿名キーの使用理由**:

- REST API での読み取り専用アクセス
- Row Level Security (RLS) で適切にアクセス制御
- サービスキーは使用しない（より高い権限のため）

**RLS 設定例**:

```sql
-- seating_dataテーブルのRLS設定
ALTER TABLE seating_data ENABLE ROW LEVEL SECURITY;

-- 読み取り専用ポリシー
CREATE POLICY "Allow read access" ON seating_data
FOR SELECT USING (true);
```

## 実装の利点

### 1. 信頼性の向上

- 依存関係の問題を回避
- Vercel での確実な動作
- エラーハンドリングの改善

### 2. パフォーマンス

- 軽量な HTTP リクエスト
- 必要最小限のデータ取得
- 効率的なフォールバック機能

### 3. セキュリティ

- 機密情報の適切な管理
- ログへの情報漏洩防止
- 最小権限の原則に従った実装

### 4. 保守性

- シンプルなコード構造
- 明確なエラーハンドリング
- 容易なデバッグとテスト

## まとめ

この解決方法により、以下を実現しました：

1. **安定した動作**: Vercel サーバーレス環境での確実な実行
2. **リアルタイムデータ**: Supabase からの最新データを使用
3. **セキュリティ**: 機密情報の適切な管理
4. **フォールバック**: ML モデル失敗時の代替手段
5. **シンプルさ**: 複雑な依存関係を避けた実装

**重要**: Vercel には必ず`SUPABASE_URL`と`SUPABASE_ANON_KEY`の環境変数設定が必要です。これらがないと Supabase からのデータ取得ができません。
