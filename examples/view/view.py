import qlib
from qlib.workflow import R
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from qlib.contrib.evaluate import risk_analysis
from qlib.contrib.report.analysis_position.report import report_graph
import plotly

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
    report_normal_df = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
    ##fig = report_graph(report_normal_df, show_notebook=False)
    ##plotly.offline.plot(fig[0], filename=f"{recorder_id}_portfolio_report.html")


    # 计算策略和基准的累计收益
    cumulative_strategy_return = (1 + report_normal_df['return']).cumprod() - 1
    cumulative_bench_return = (1 + report_normal_df['bench']).cumprod() - 1

    # 计算超额收益 (Alpha)
    excess_return = cumulative_strategy_return - cumulative_bench_return

    print("=== 策略表现基础统计 ===")
    print(f"回测期间: {report_normal_df.index[0]} 至 {report_normal_df.index[-1]}")
    print(f"总交易日数: {len(report_normal_df)}")
    print(f"策略总收益: {cumulative_strategy_return.iloc[-1]:.2%}")
    print(f"基准总收益: {cumulative_bench_return.iloc[-1]:.2%}")
    print(f"超额收益: {excess_return.iloc[-1]:.2%}")

    # 使用Qlib内置函数计算风险指标
    risk_stats = risk_analysis(report_normal_df['return'])
    
    # 计算总成本占收益的比例
    total_cost = report_normal_df['cost'].sum()
    total_return = report_normal_df['return'].sum()
    cost_ratio = total_cost / total_return if total_return > 0 else 0

    # 计算关键指标
    annual_return = risk_stats.get('annualized_return', 0)
    sharpe_ratio = risk_stats.get('information_ratio', 0)  # Qlib中常使用信息比率
    max_drawdown = risk_stats.get('max_drawdown', 0)

    print("=== 关键绩效指标 ===")
    print(f"年化收益率: {annual_return:.2%}")
    print(f"夏普比率: {sharpe_ratio:.2f}")
    print(f"最大回撤: {max_drawdown:.2%}")
    print(f"平均日换手率: {report_normal_df['turnover'].mean():.2%}")

    # 简单的风险收益比评估
    if sharpe_ratio > 1.0 and max_drawdown < 0.15:
        print("✅ 策略表现优秀：高夏普比率，回撤可控")
    elif sharpe_ratio > 0.5 and max_drawdown < 0.25:
        print("⚠️ 策略表现一般：需关注风险控制")
    else:
        print("❌ 策略表现不佳：风险收益比不理想")

    # 加载持仓数据
    positions_normal = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")
    
    print("\n=== 持仓数据分析 ===")
    print(f"持仓数据日期范围: {len(positions_normal)} 个交易日")
    
    # 检查数据结构
    first_date = list(positions_normal.keys())[0]
    first_pos = positions_normal[first_date]
    print(f"每日持仓股票数量示例: {first_pos}")
    print(f"持仓数据列: {first_pos.columns.tolist()}")
    
    # 1. 持仓权重时间序列可视化
    def visualize_position_weights(positions_dict, top_n=10):
        """可视化前N只股票的持仓权重变化"""
        
        # 提取权重数据
        weight_data = []
        for date, pos_df in positions_dict.items():
            if 'weight' in pos_df.columns:
                for instrument in pos_df.index:
                    weight_data.append({
                        'date': pd.to_datetime(date),
                        'instrument': instrument,
                        'weight': pos_df.loc[instrument, 'weight']
                    })
        
        if not weight_data:
            print("未找到权重数据列")
            return None
            
        weight_df = pd.DataFrame(weight_data)
        
        # 计算每只股票的平均权重，选择前N只
        avg_weights = weight_df.groupby('instrument')['weight'].mean().sort_values(ascending=False)
        top_instruments = avg_weights.head(top_n).index
        
        # 创建时间序列图
        fig = go.Figure()
        
        for instrument in top_instruments:
            instrument_data = weight_df[weight_df['instrument'] == instrument]
            fig.add_trace(go.Scatter(
                x=instrument_data['date'],
                y=instrument_data['weight'],
                mode='lines',
                name=instrument,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=f'前{top_n}只股票持仓权重变化',
            xaxis_title='日期',
            yaxis_title='持仓权重',
            hovermode='x unified',
            height=600
        )
        
        return fig
    
    # 2. 持仓集中度分析
    def visualize_position_concentration(positions_dict):
        """可视化持仓集中度"""
        
        concentration_data = []
        for date, pos_df in positions_dict.items():
            if 'weight' in pos_df.columns:
                weights = pos_df['weight'].abs().sort_values(ascending=False)
                
                # 计算集中度指标
                top5_concentration = weights.head(5).sum()
                top10_concentration = weights.head(10).sum()
                hhi = (weights ** 2).sum()  # Herfindahl-Hirschman Index
                
                concentration_data.append({
                    'date': pd.to_datetime(date),
                    'top5_concentration': top5_concentration,
                    'top10_concentration': top10_concentration,
                    'hhi': hhi,
                    'num_positions': len(weights[weights > 0.001])  # 权重>0.1%的持仓数
                })
        
        if not concentration_data:
            return None
            
        conc_df = pd.DataFrame(concentration_data)
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('前5大持仓集中度', '前10大持仓集中度', 'HHI指数', '有效持仓数量'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 前5大集中度
        fig.add_trace(
            go.Scatter(x=conc_df['date'], y=conc_df['top5_concentration'], 
                      name='前5大集中度', line=dict(color='blue')),
            row=1, col=1
        )
        
        # 前10大集中度
        fig.add_trace(
            go.Scatter(x=conc_df['date'], y=conc_df['top10_concentration'], 
                      name='前10大集中度', line=dict(color='green')),
            row=1, col=2
        )
        
        # HHI指数
        fig.add_trace(
            go.Scatter(x=conc_df['date'], y=conc_df['hhi'], 
                      name='HHI指数', line=dict(color='red')),
            row=2, col=1
        )
        
        # 有效持仓数量
        fig.add_trace(
            go.Scatter(x=conc_df['date'], y=conc_df['num_positions'], 
                      name='有效持仓数', line=dict(color='orange')),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text="持仓集中度分析")
        return fig
    
    # 3. 持仓分布热力图
    def visualize_position_heatmap(positions_dict, sample_days=20):
        """创建持仓权重热力图"""
        
        # 采样部分日期以避免图表过于密集
        dates = list(positions_dict.keys())
        if len(dates) > sample_days:
            step = len(dates) // sample_days
            sampled_dates = dates[::step]
        else:
            sampled_dates = dates
        
        # 收集所有股票代码
        all_instruments = set()
        for date in sampled_dates:
            if 'weight' in positions_dict[date].columns:
                all_instruments.update(positions_dict[date].index)
        
        # 限制显示的股票数量
        if len(all_instruments) > 50:
            # 选择平均权重最大的50只股票
            avg_weights = {}
            for instrument in all_instruments:
                weights = []
                for date in sampled_dates:
                    pos_df = positions_dict[date]
                    if instrument in pos_df.index and 'weight' in pos_df.columns:
                        weights.append(abs(pos_df.loc[instrument, 'weight']))
                if weights:
                    avg_weights[instrument] = np.mean(weights)
            
            top_instruments = sorted(avg_weights.keys(), 
                                   key=lambda x: avg_weights[x], reverse=True)[:50]
        else:
            top_instruments = list(all_instruments)
        
        # 构建热力图数据
        heatmap_data = []
        for instrument in top_instruments:
            row = []
            for date in sampled_dates:
                pos_df = positions_dict[date]
                if instrument in pos_df.index and 'weight' in pos_df.columns:
                    row.append(pos_df.loc[instrument, 'weight'])
                else:
                    row.append(0)
            heatmap_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[str(date)[:10] for date in sampled_dates],  # 只显示日期部分
            y=top_instruments,
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(title="持仓权重")
        ))
        
        fig.update_layout(
            title='持仓权重热力图',
            xaxis_title='日期',
            yaxis_title='股票代码',
            height=max(600, len(top_instruments) * 15)
        )
        
        return fig
    
    # 生成可视化图表
    try:
        # 权重时间序列
        fig1 = visualize_position_weights(positions_normal, top_n=10)
        if fig1:
            plotly.offline.plot(fig1, filename=f"{recorder_id}_position_weights.html")
            print(f"✅ 持仓权重时间序列图已保存: {recorder_id}_position_weights.html")
        
        # 持仓集中度
        fig2 = visualize_position_concentration(positions_normal)
        if fig2:
            plotly.offline.plot(fig2, filename=f"{recorder_id}_position_concentration.html")
            print(f"✅ 持仓集中度分析图已保存: {recorder_id}_position_concentration.html")
        
        # 持仓热力图
        fig3 = visualize_position_heatmap(positions_normal, sample_days=30)
        if fig3:
            plotly.offline.plot(fig3, filename=f"{recorder_id}_position_heatmap.html")
            print(f"✅ 持仓热力图已保存: {recorder_id}_position_heatmap.html")
            
    except Exception as e:
        print(f"可视化过程中出现错误: {e}")
        print("正在检查数据结构...")
        
        # 详细检查数据结构
        sample_date = list(positions_normal.keys())[0]
        sample_pos = positions_normal[sample_date]
        print(f"样本日期: {sample_date}")
        print(f"样本数据形状: {sample_pos.shape}")
        print(f"样本数据列: {sample_pos.columns.tolist()}")
        print(f"样本数据前5行:")
        print(sample_pos.head())

    # 预测分数
    # report_df = recorder.load_object("portfolio_analysis/analysis.pkl")
    # fig = report_graph(report_df, show_notebook=False)
    # plotly.offline.plot(fig[0], filename=f"{recorder_id}_analysis.html")