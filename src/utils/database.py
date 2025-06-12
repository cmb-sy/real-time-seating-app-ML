"""
Supabaseデータベース接続モジュール
"""

from supabase import create_client, Client
from src.utils.config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    """
    Supabaseクライアントを作成・取得する関数
    
    Returns:
        Client: Supabaseクライアントインスタンス
    """
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

# グローバルクライアントインスタンス
supabase_client = get_supabase_client() 