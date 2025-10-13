#  Copyright (c) Microsoft Corporation.
#  Licensed under the MIT License.
"""
Qlib provides two kinds of interfaces.
(1) Users could define the Quant research workflow by a simple configuration.
(2) Qlib is designed in a modularized way and supports creating research workflow by code just like building blocks.

The interface of (1) is `qrun XXX.yaml`.  The interface of (2) is script like this, which nearly does the same thing as `qrun XXX.yaml`
"""
import qlib
import pandas as pd
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config, flatten_dict
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord, SigAnaRecord
from qlib.tests.data import GetData
from qlib.tests.config import CSI300_BENCH, CSI300_GBDT_TASK
import plotly.graph_objects as go
import os
from qlib.contrib.report.analysis_position.report import report_graph
import plotly

def view(ba_rid, dataset):
    # 加载实验结果
    exp_name = "workflow"
    from qlib.contrib.report import analysis_model, analysis_position
    from qlib.data import D

    recorder = R.get_recorder(
        recorder_id=ba_rid,
     experiment_name=exp_name)
    print(recorder)
    pred_df = recorder.load_object("pred.pkl")
    report_normal_df = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
    positions = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")
    analysis_df = recorder.load_object("portfolio_analysis/port_analysis_1day.pkl")

    analysis_position.report_graph(report_normal_df)
    analysis_position.risk_analysis_graph(analysis_df, report_normal_df)
    label_df = dataset.prepare("test", col_set="label")
    label_df.columns = ["label"]
    pred_label = pd.concat([label_df, pred_df], axis=1, sort=True).reindex(label_df.index)
    analysis_position.score_ic_graph(pred_label)
    analysis_model.model_performance_graph(pred_label)

def view2(ba_rid):
    # 获取实验记录
    exp_name = "workflow"  # 默认实验名称
    recorder = R.get_exp(experiment_name=exp_name)[0]  # 获取第一个记录

    report_df = pd.read_pickle(os.path.join(recorder.get_path(), "portfolio_analysis/report_normal_1day.pkl"))
    analysis = recorder.load_object("portfolio_analysis/analysis.pkl")

    # 累积回报
    cum_return = report_df['excess_return_with_cost']
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=cum_return.index, y=cum_return.cumsum(), mode='lines', name='Cumulative Excess Return'))
    fig1.update_layout(title='Cumulative Excess Return', xaxis_title='Date', yaxis_title='Return')
    fig1.show()
    fig1.write_image("cumulative_return.png")

    # IC 时间序列
    ic_series = analysis['ic']['mean']
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=ic_series.index, y=ic_series.values, mode='lines', name='Information Coefficient'))
    fig2.update_layout(title='Information Coefficient Over Time', xaxis_title='Date', yaxis_title='IC')
    fig2.show()
    fig2.write_image("ic_series.png")


if __name__ == "__main__":
    # use default data
    provider_uri = "~/.qlib/qlib_data/cn_data"  # target_dir
    custom_output_dir = "~/.qlib/qlib_data/output"
    GetData().qlib_data(
        target_dir=provider_uri, 
        region=REG_CN, 
        exists_skip=True)
    qlib.init(provider_uri=provider_uri, region=REG_CN)

    model = init_instance_by_config(CSI300_GBDT_TASK["model"])
    dataset = init_instance_by_config(CSI300_GBDT_TASK["dataset"])

    port_analysis_config = {
        "executor": {
            "class": "SimulatorExecutor",
            "module_path": "qlib.backtest.executor",
            "kwargs": {
                "time_per_step": "day",
                "generate_portfolio_metrics": True,
            },
        },
        "strategy": {
            "class": "TopkDropoutStrategy",
            "module_path": "qlib.contrib.strategy.signal_strategy",
            "kwargs": {
                "signal": (model, dataset),
                "topk": 50,
                "n_drop": 5,
            },
        },
        "backtest": {
            "start_time": "2017-01-01",
            "end_time": "2020-08-01",
            "account": 100000000,
            "benchmark": CSI300_BENCH,
            "exchange_kwargs": {
                "freq": "day",
                "limit_threshold": 0.095,
                "deal_price": "close",
                "open_cost": 0.0005,
                "close_cost": 0.0015,
                "min_cost": 5,
            },
        },
    }

    # NOTE: This line is optional
    # It demonstrates that the dataset can be used standalone.
    example_df = dataset.prepare("train")
    print(example_df.head())

    # start exp
    with R.start(experiment_name="workflow"):
        R.log_params(**flatten_dict(CSI300_GBDT_TASK))
        model.fit(dataset)
        R.save_objects(**{"params.pkl": model})

        # prediction
        recorder = R.get_recorder()
        ba_rid = recorder.id
        sr = SignalRecord(model, dataset, recorder)
        sr.generate()

        # Signal Analysis
        sar = SigAnaRecord(recorder)
        sar.generate()

        # backtest. If users want to use backtest based on their own prediction,
        # please refer to https://qlib.readthedocs.io/en/latest/component/recorder.html#record-template.
        par = PortAnaRecord(recorder, port_analysis_config, "day")
        artifact_dict = par.generate()
        report_normal_df = artifact_dict['report_normal_1day.pkl']
        positions_normal = artifact_dict['positions_normal_1day.pkl']
        report_normal_df.to_pickle('/Users/liuping/学习/code5/qlib/output/report_normal_df.pkl')

        ##report_normal_df = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
        fig = report_graph(report_normal_df, show_notebook=False)
        plotly.offline.plot(fig[0], filename="portfolio_report.html")
        # 其他结果手动保存
        ## report_df.to_csv(os.path.join(custom_output_dir, "report.csv"))
    
    # Call view function to display results
    # view2(ba_rid)
