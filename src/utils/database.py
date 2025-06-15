"""
Supabaseデータベース接続モジュール
"""

from supabase import create_client, Client
from src.utils.config import NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

def get_supabase_client() -> Client:
    """
    Supabaseクライアントを作成・取得する関数
    
    Returns:
        Client: Supabaseクライアントインスタンス
    """
    if not NEXT_PUBLIC_SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise Exception("Supabase環境変数が設定されていません")
    
    supabase: Client = create_client(NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return supabase

# グローバルクライアントインスタンス
supabase_client = get_supabase_client() 