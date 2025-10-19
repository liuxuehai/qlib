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
import matplotlib.pyplot as plt
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
    
        # 检查数据结构
    positions_normal = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")

    print("positions_normal 类型:", type(positions_normal))
    print("positions_normal 长度:", len(positions_normal))

    first_date = list(positions_normal.keys())[0]
    first_position = positions_normal[first_date]

    print("Position 对象类型:", type(first_position))
    print("Position 对象属性:", dir(first_position))

    # 尝试访问可能的属性
    if hasattr(first_position, 'get_stock_list'):
        print("股票列表:", first_position.get_stock_list())
        
    if hasattr(first_position, 'get_stock_amount'):
        sample_stock = first_position.get_stock_list()[0] if first_position.get_stock_list() else None
        if sample_stock:
            print(f"样本股票 {sample_stock} 的数量:", first_position.get_stock_amount(sample_stock))

    if hasattr(first_position, 'get_cash'):
        print("现金:", first_position.get_cash())
        
    if hasattr(first_position, 'get_value'):
        print("总价值:", first_position.get_value())

    # 提取所有持仓数据
    all_holdings = []

    for date, position in positions_normal.items():
        # 获取股票列表
        if hasattr(position, 'get_stock_list'):
            stock_list = position.get_stock_list()
            
            # 计算总价值（用于计算权重）
            total_value = position.get_value() if hasattr(position, 'get_value') else 0
            
            # 提取每只股票的持仓信息
            for stock in stock_list:
                amount = position.get_stock_amount(stock)

                price = position.get_stock_price(stock)
                # 计算权重
                weight = position.get_stock_weight(stock)
                #value = position.get_stock_value(stock)

                count= position.get_stock_count(stock,'day')
                    
                all_holdings.append({
                        'date': date,
                        'instrument': stock,
                        'amount': round(amount, 2),
                        'value': round(amount*price, 2),
                        'weight': weight,
                        'count':count,
                        'price': round(price, 2)
                    })

        # 添加现金信息
        if hasattr(position, 'get_cash'):
            cash = position.get_cash()
            if total_value > 0:
                cash_weight = cash / total_value
            else:
                cash_weight = 0
                
            all_holdings.append({
                'date': date,
                'instrument': 'CASH',
                'amount': cash,
                'value': cash,
                'weight': cash_weight,
                'count':0,
                'price': 0
            })

    # 转换为DataFrame
    if all_holdings:
        holdings_df = pd.DataFrame(all_holdings)
        
        # 透视数据用于绘图
        pivot_weights = holdings_df.pivot_table(
            index='date', 
            columns='instrument', 
            values='weight', 
            aggfunc='sum'
        ).fillna(0)
        
        # 绘制堆叠面积图
        plt.figure(figsize=(15, 8))
        
        # 如果股票太多，只显示权重最大的前15个，其他归为"其他"
        if len(pivot_weights.columns) > 15:
            top_stocks = pivot_weights.sum().nlargest(15).index
            #other_weights = pivot_weights.drop(columns=top_stocks).sum(axis=1)
            #plot_data = pd.concat([pivot_weights[top_stocks], other_weights.rename('Other')], axis=1)

            plot_data = pivot_weights[top_stocks]
        else:
            plot_data = pivot_weights
        
        plt.stackplot(plot_data.index, plot_data.values.T, 
                    labels=plot_data.columns, alpha=0.7)
        plt.title('Portfolio Weight Allocation Over Time')
        plt.xlabel('Date')
        plt.ylabel('Weight')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        # 显示持仓数据的前几行
        print("持仓数据预览:")
        print(holdings_df.head())
    else:
        print("无法提取持仓数据")