"""
Supabaseデータベース接続モジュール
"""

from supabase import create_client, Client
from src.utils.config import NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_URL

def get_supabase_client() -> Client:
    """
    Supabaseクライアントを作成・取得する関数
    
    Returns:
        Client: Supabaseクライアントインスタンス
    """
    supabase: Client = create_client(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_URL)
    return supabase

# グローバルクライアントインスタンス
supabase_client = get_supabase_client() 