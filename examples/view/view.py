import qlib
from qlib.workflow import R
import pandas as pd
import plotly.graph_objects as go
import os

# 初始化
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

# 加载实验结果
exp_name = "workflow"
from qlib.contrib.report import analysis_model, analysis_position
from qlib.data import D

recorder = R.get_recorder(recorder_id=ba_rid, experiment_name=exp_name)
print(recorder)
pred_df = recorder.load_object("pred.pkl")
report_normal_df = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
positions = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")
analysis_df = recorder.load_object("portfolio_analysis/port_analysis_1day.pkl")

analysis_position.report_graph(report_normal_df)