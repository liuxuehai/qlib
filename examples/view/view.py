import qlib
from qlib.workflow import R
import pandas as pd
import plotly.graph_objects as go
import os

# 初始化
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

exps = R.list_experiments()

print(exps)

# 获取实验记录
exp_name = "workflow"  # 替换为你的实验名称
exp = R.get_exp(experiment_name=exp_name)
recorders = exp.list_recorders()

   # 遍历记录器并导出
for recorder_id, recorder in recorders.items():
       # 预测分数
       pred_df = recorder.load_object("pred.pkl")
       pred_df.to_csv(os.path.join(custom_export_dir, f"predictions_{recorder_id}.csv"))
       pred_df.to_json(os.path.join(custom_export_dir, f"predictions_{recorder_id}.json"), orient="records")

       # 回测报告
       report_path = os.path.join(recorder.get_path(), "portfolio_analysis/report_normal_1day.pkl")
       if os.path.exists(report_path):
           report_df = pd.read_pickle(report_path)
           report_df.to_csv(os.path.join(custom_export_dir, f"report_{recorder_id}.csv"))
           report_df.to_json(os.path.join(custom_export_dir, f"report_{recorder_id}.json"), orient="records")

       # 仓位数据
       positions_path = os.path.join(recorder.get_path(), "portfolio_analysis/positions_normal_1day.pkl")
       if os.path.exists(positions_path):
           positions_df = pd.read_pickle(positions_path)
           positions_df.to_csv(os.path.join(custom_export_dir, f"positions_{recorder_id}.csv"))
           positions_df.to_json(os.path.join(custom_export_dir, f"positions_{recorder_id}.json"), orient="records")

       # 指标
       analysis_path = os.path.join(recorder.get_path(), "portfolio_analysis/analysis.pkl")
       if os.path.exists(analysis_path):
           analysis = pd.read_pickle(analysis_path)
           metrics = {}
           for metric, values in analysis.items():
               if isinstance(values, dict):
                   for sub_key, sub_value in values.items():
                       metrics[f"{metric}_{sub_key}"] = sub_value
               else:
                   metrics[metric] = values
           with open(os.path.join(custom_export_dir, f"metrics_{recorder_id}.json"), "w") as f:
               json.dump(metrics, f, indent=4)
           pd.DataFrame([metrics]).to_csv(os.path.join(custom_export_dir, f"metrics_{recorder_id}.csv"), index=False)

       # 模型文件
       model_path = os.path.join(recorder.get_path(), "model.pkl")
       if os.path.exists(model_path):
           shutil.copy(model_path, os.path.join(custom_export_dir, f"model_{recorder_id}.pkl"))

print(f"Results exported to {custom_export_dir}")