"""
Supabaseアクセス用の共通モジュール
"""
import os
import json
import urllib.parse
import urllib.request

def get_supabase_config():
    """Supabase設定を取得"""
    try:
        supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        service_role_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        anon_key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
                
        if service_role_key:
            print("SERVICE_ROLE_KEYを利用します")
            return supabase_url, service_role_key
        elif anon_key:
            print("ANON_KEYを利用します") 
            return supabase_url, anon_key
        else:
            print("No valid keys found")
            return None, None
            
    except Exception as e:
        print(f"Supabase設定取得エラー: {str(e)}")
        return None, None

def get_mock_data(day_of_week=None):
    """テスト用のモックデータを生成"""
    import random
    
    if day_of_week is None:
        day_of_week = random.randint(0, 4)
    
    # 曜日に基づいたモックデータを生成
    mock_data = []
    record_count = random.randint(5, 15)
    
    for _ in range(record_count):
        base_density = 30 + day_of_week * 10 + random.randint(-10, 10)
        base_seats = 3 + random.randint(0, 3)
        
        mock_data.append({
            'density_rate': max(0, min(100, base_density)),
            'occupied_seats': max(0, min(8, base_seats)),
            'day_of_week': day_of_week
        })
    
    print(f"Generated {len(mock_data)} mock records for day_of_week={day_of_week}")
    return mock_data

def get_supabase_data(query_params=None):
    """Supabaseから実データを取得"""
    supabase_url, supabase_key = get_supabase_config()  # 変数名を統一
    
    if not supabase_url or not supabase_key:
        print("Supabaseの設定が見つからないため、モックデータを使用します")
        return get_mock_data()
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        url = f"{supabase_url}/rest/v1/density_history"
        if query_params:
            url = f"{url}?{query_params}"
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            raw_response = response.read().decode()
            data = json.loads(raw_response)
        return data
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Error response: {e.read().decode()}")
        return get_mock_data()
    except Exception as e:
        raise e

if __name__ == "__main__":
    # 全データ取得
    all_data = get_supabase_data()
    print(f"取得したデータ数: {len(all_data)}")
    
    # 特定の曜日のデータ取得
    day1_data = get_supabase_data("day_of_week=eq.1&select=density_rate,occupied_seats")
    print(f"月曜日のデータ数: {len(day1_data)}")