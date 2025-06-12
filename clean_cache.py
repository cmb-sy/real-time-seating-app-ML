#!/usr/bin/env python3
"""
デプロイ前にPythonキャッシュを削除するためのスクリプト
"""
import os
import shutil

def clean_pycache(directory):
    """
    指定されたディレクトリとその下のサブディレクトリから__pycache__ディレクトリを削除します
    """
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing {pycache_path}")
            shutil.rmtree(pycache_path)
        
        # .pycファイルも削除
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                file_path = os.path.join(root, file)
                print(f"Removing {file_path}")
                os.remove(file_path)

if __name__ == '__main__':
    # カレントディレクトリからPythonキャッシュを削除
    clean_pycache('.')
    print("Python cache cleaned successfully!") 