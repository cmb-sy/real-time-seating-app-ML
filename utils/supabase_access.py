"""
Supabaseアクセス用の共通モジュール
"""

import os
import json
import urllib.parse
import urllib.request


def get_supabase_config():
    """Supabase設定取得"""
    try:
        supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        anon_key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if service_role_key:
            return supabase_url, service_role_key
        elif anon_key:
            return supabase_url, anon_key
        else:
            print("Supabaseの設定が見つかりません。")
            return None, None

    except Exception as e:
        print(f"Supabase設定取得エラー: {str(e)}")
        return None, None


def get_supabase_data(query_params=None):
    """Supabaseから実データを取得"""
    supabase_url, supabase_key = get_supabase_config()

    if not supabase_url or not supabase_key:
        raise Exception(
            "Supabaseの設定が見つかりません。環境変数NEXT_PUBLIC_SUPABASE_URL、SUPABASE_SERVICE_ROLE_KEY、またはNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。"
        )

    try:
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
        }
        url = f"{supabase_url}/rest/v1/density_history"
        if query_params:
            url = f"{url}?{query_params}"
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req) as response:
            raw_response = response.read().decode()
            data = json.loads(raw_response)

        # 平日データのみを許可（1-5: 月-金）
        if query_params and "day_of_week=eq." in query_params:
            day_of_week = int(query_params.split("day_of_week=eq.")[1].split("&")[0])
            if day_of_week < 1 or day_of_week > 5:
                raise ValueError(
                    f"無効な曜日（曜日{day_of_week}）のデータ取得は許可されていません。業務は平日（1-5: 月-金）のみです。"
                )

        return data

    except urllib.error.HTTPError as e:
        error_message = f"Supabaseからのデータ取得に失敗しました: HTTP {e.code}"
        print(error_message)
        try:
            error_response = e.read().decode()
            print(f"Error response: {error_response}")
        except:
            pass
        raise Exception(error_message)
    except Exception as e:
        error_message = f"Supabaseからのデータ取得エラー: {str(e)}"
        print(error_message)
        raise Exception(error_message)


if __name__ == "__main__":
    try:
        print("=== 全データ取得テスト ===")
        all_data = get_supabase_data()
        print(f"取得したデータ数: {len(all_data)}")

        print("\n=== 平日データ取得テスト ===")
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
        for i, db_day in enumerate(range(1, 6)):  # DB形式: 1-5
            day_data = get_supabase_data(
                f"day_of_week=eq.{db_day}&select=density_rate,occupied_seats"
            )
            print(f"{weekday_names[i]}のデータ数: {len(day_data)}")

        # 土日データ取得テスト（エラーが発生するはず）
        print("\n=== 土日データ取得テスト（エラー確認） ===")
        try:
            weekend_data = get_supabase_data(
                "day_of_week=eq.6&select=density_rate,occupied_seats"
            )
        except Exception as e:
            print(f"期待通りエラー: {str(e)}")

    except Exception as e:
        print(f"テスト実行エラー: {str(e)}")
