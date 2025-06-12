# リアルタイム座席予測アプリケーション（ML 版）

リアルタイム座席予測アプリケーションにおいて、Supabase をデータベースとして使用し、Vercel サーバーレス関数で API を提供します。

## プロジェクト概要

このプロジェクトは以下のコンポーネントで構成されています：

1. **機械学習モデル** - scikit-learn と Optuna を使用した予測モデル
2. **データ分析ツール** - 過去データの分析と可視化
3. **API エンドポイント** - Vercel サーバーレス関数で実装
4. **定期実行スケジューラー** - 2 週間ごとにモデルを更新

## 機能

- 密度率と占有座席数の予測
- 曜日・時間帯ごとの利用パターン分析
- リアルタイム API エンドポイント（今日・明日の予測）
- 機械学習モデルによる曜日別予測
- 週間平均予測データの提供
- Optuna によるハイパーパラメータ最適化
- データ可視化ツール

## 環境設定

### 前提条件

- Python 3.10 以上
- Supabase アカウントと API 情報

### インストール手順

1. リポジトリのクローン:

```bash
git clone https://github.com/yourusername/real-time-seating-app-ML.git
cd real-time-seating-app-ML
```

2. 仮想環境の作成と有効化:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. 依存関係のインストール:

```bash
pip install -r requirements.txt
```

4. プロジェクトのパスを追加:

```bash
pip install -e .
```

4. 環境変数の設定:

プロジェクトルートに`.env`ファイルを作成し、以下の内容を設定します：

```
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

## 使用方法

### メインコマンド

```bash
python main.py train     # 機械学習モデルの訓練
python main.py analyze   # データ分析の実行
python main.py schedule  # スケジューラーの実行
```

### 機械学習モデルの訓練（詳細オプション）

```bash
python -m src.ml.train_ml_models --mode train --n-trials 50
```

オプション:

- `--mode`: 実行モード（train: 訓練, test: 予測テスト, info: モデル情報表示）
- `--n-trials`: Optuna の最適化試行回数（デフォルト: 50）
- `--target`: 最適化対象（density: 密度率, seats: 座席数, both: 両方）

### 予測テストの実行

```bash
python -m src.ml.train_ml_models --mode test
```

### モデル情報の表示

```bash
python -m src.ml.train_ml_models --mode info
```

### API サーバーのローカル実行

```bash
uvicorn src.api.health:app --reload --port 8000
```

## モデルの更新

モデルは 2 週間ごとに自動的に更新されるようスケジュールされています。手動でモデルを更新する場合は以下のコマンドを実行します：

```bash
python -m src.utils.scheduler --mode force
```

継続的な監視モードで実行するには：

```bash
python -m src.utils.scheduler --mode monitor
```

## API エンドポイント

本番環境では、以下の Vercel サーバーレス関数エンドポイントが利用可能です：

- `/api/health` - システムの状態確認
- `/api/predictions/today-tomorrow` - 今日と明日の予測（履歴データに基づく）
- `/api/predictions/weekly-average` - 週間平均予測
- `/api/predictions/ml` - 機械学習モデルによる曜日別予測
- `/api/supabase/sync` - Supabase データベース同期

### 機械学習予測 API

`/api/predictions/ml` エンドポイントは、訓練済みの機械学習モデルを使用して曜日別の予測を提供します：

- **入力**: なし（リクエスト日の曜日を自動検出）
- **出力**:
  - 今日と明日の密度率予測
  - 占有座席数予測
  - 予測の信頼度
  - モデルのパフォーマンス指標（RMSE）
  - モデルタイプ

このエンドポイントは、時間特徴量を除去し、曜日のみを特徴量として使用した予測モデルを活用しています。

### Vercel デプロイについて

Vercel では`vercel.json`の設定により、`src/api`ディレクトリの API ファイルを直接使用するように構成されています：

1. リクエストルーティング - すべての API リクエストが`src/api`ディレクトリのファイルに転送されます
2. 関数設定 - `src/api/*.py`が実行可能な Python 関数として設定されています
3. 無視ルール - `.vercelignore`ファイルで`src/api`ディレクトリが保護されています

この設定により、開発時の構造化されたディレクトリ構成をそのまま Vercel にデプロイできます。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
