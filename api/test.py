"""
デバッグ用テストエンドポイント
"""
import os
import json
import sys

def handler(request, context):
    """デバッグ用のハンドラー関数"""
    try:
        # 基本情報の収集
        debug_info = {
            "success": True,
            "message": "テストエンドポイントが正常に動作しています",
            "python_version": sys.version,
            "environment_variables": {
                "NEXT_PUBLIC_SUPABASE_URL": bool(os.environ.get('NEXT_PUBLIC_SUPABASE_URL')),
                "SUPABASE_SERVICE_ROLE_KEY": bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY')),
                "NEXT_PUBLIC_SUPABASE_ANON_KEY": bool(os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')),
                "VERCEL": os.environ.get('VERCEL'),
                "VERCEL_ENV": os.environ.get('VERCEL_ENV')
            },
            "request_info": {
                "method": getattr(request, 'method', 'unknown'),
                "type": str(type(request)),
                "attributes": [attr for attr in dir(request) if not attr.startswith('_')]
            }
        }
        
        # Supabaseライブラリのテスト
        try:
            from supabase import create_client, Client
            debug_info["supabase_library"] = "✅ インポート成功"
            
            # 環境変数の取得
            supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
            
            if supabase_url and supabase_key:
                # クライアント作成テスト
                supabase = create_client(supabase_url, supabase_key)
                debug_info["supabase_client"] = "✅ クライアント作成成功"
                
                # データベース接続テスト
                response = supabase.table('density_history').select('*').limit(1).execute()
                debug_info["database_test"] = {
                    "status": "✅ 接続成功",
                    "data_count": len(response.data) if response.data else 0
                }
            else:
                debug_info["database_test"] = "❌ 環境変数が不足"
                
        except ImportError as e:
            debug_info["supabase_library"] = f"❌ インポートエラー: {str(e)}"
        except Exception as e:
            debug_info["database_test"] = f"❌ 接続エラー: {str(e)}"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin, Accept, X-Requested-With'
            },
            'body': json.dumps(debug_info, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"テストエンドポイントでエラーが発生しました: {str(e)}",
            "error_type": type(e).__name__
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response, ensure_ascii=False)
        } 