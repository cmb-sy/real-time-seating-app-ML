import os

# dotenvが利用可能な場合のみ.envファイルを読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenvがインストールされていない場合は環境変数のみ使用
    pass

# Supabase設定
NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")