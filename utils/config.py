"""
設定ファイル - 環境変数を読み込み
"""
import os
from os.path import join, dirname
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 環境変数を取得
NEXT_PUBLIC_SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
NEXT_PUBLIC_SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

#　設定値を確認
if __name__ == "__main__":
    print("=== 設定確認 ===")
    print(f"NEXT_PUBLIC_SUPABASE_URL: {NEXT_PUBLIC_SUPABASE_URL}")
    print(f"NEXT_PUBLIC_SUPABASE_ANON_KEY: {NEXT_PUBLIC_SUPABASE_ANON_KEY}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {SUPABASE_SERVICE_ROLE_KEY}")