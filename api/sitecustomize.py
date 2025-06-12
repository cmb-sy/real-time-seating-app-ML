"""
Pythonのキャッシュファイル生成を無効化する設定
Vercelのビルドプロセスでの問題を回避するため
"""
import sys
sys.dont_write_bytecode = True 