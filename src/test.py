import sys
import os
# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)

from src.ml.train_ml_models import run_full_ml_pipeline

run_full_ml_pipeline(n_trials=30, target_type='both')