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



import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_interactive_trading_chart(stock_code, positions_normal, price_data=None):
    """
    使用Plotly创建交互式交易图表
    """
    
    # 提取持仓数据
    stock_holdings = []
    dates = sorted(positions_normal.keys())
    
    for date in dates:
        position = positions_normal[date]
        stock_list = position.get_stock_list()
        
        if stock_code in stock_list:
            amount = position.get_stock_amount(stock_code)
            price = position.get_stock_price(stock_code)
            stock_holdings.append({
                'date': date,
                'amount': amount,
                'price': price
            })
        else:
            stock_holdings.append({
                'date': date,
                'amount': 0,
                'price': 0
            })
    
    
    holdings_df = pd.DataFrame(stock_holdings).set_index('date')
    
    # 如果没有提供价格数据，使用持仓中的价格
    if price_data is None:
        price_data = holdings_df[holdings_df['price'] > 0]['price']
    
    # 计算持仓变化
    holdings_df['amount_change'] = holdings_df['amount'].diff()
    
    # 识别买卖点
    buy_signals = holdings_df[holdings_df['amount_change'] > 0]
    sell_signals = holdings_df[holdings_df['amount_change'] < 0]
    
    # 创建子图
    fig = make_subplots(rows=2, cols=1, 
                        subplot_titles=(f'{stock_code} Price with Buy/Sell Signals', 
                                       'Holdings Amount'),
                        vertical_spacing=0.1,
                        row_heights=[0.7, 0.3])
    
    # 价格图表
    fig.add_trace(
        go.Scatter(x=price_data.index, y=price_data.values,
                  mode='lines', name='Price',
                  line=dict(color='black', width=2)),
        row=1, col=1
    )
    
    # 买入点
    if not buy_signals.empty:
        buy_dates = [date for date in buy_signals.index if date in price_data.index]
        buy_prices = [price_data.loc[date] for date in buy_dates]
        
        fig.add_trace(
            go.Scatter(x=buy_dates, y=buy_prices,
                      mode='markers', name='Buy',
                      marker=dict(color='green', symbol='triangle-up', size=10)),
            row=1, col=1
        )
    
    # 卖出点
    if not sell_signals.empty:
        sell_dates = [date for date in sell_signals.index if date in price_data.index]
        sell_prices = [price_data.loc[date] for date in sell_dates]
        
        fig.add_trace(
            go.Scatter(x=sell_dates, y=sell_prices,
                      mode='markers', name='Sell',
                      marker=dict(color='red', symbol='triangle-down', size=10)),
            row=1, col=1
        )
    
    # 持仓量图表
    fig.add_trace(
        go.Bar(x=holdings_df.index, y=holdings_df['amount'],
               name='Holdings', marker_color='blue'),
        row=2, col=1
    )
    
    fig.update_layout(height=800, title_text=f"{stock_code} Trading Analysis")
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Holdings", row=2, col=1)
    
    fig.show()
    
    return holdings_df, buy_signals, sell_signals

# 使用示例
# holdings_df, buy_signals, sell_signals = plot_interactive_trading_chart('000001', positions_normal)

def plot_detailed_trading_analysis(stock_code, positions_normal, price_data=None):
    """
    绘制详细的交易分析图表，包括价格、持仓和买卖点
    """
    
    # 提取持仓数据
    stock_holdings = []
    dates = sorted(positions_normal.keys())
    
    for date in dates:
        position = positions_normal[date]
        stock_list = position.get_stock_list()
        
        if stock_code in stock_list:
            amount = position.get_stock_amount(stock_code)
            price = position.get_stock_price(stock_code)
            stock_holdings.append({
                'date': date,
                'amount': amount,
                'price': price
            })
        else:
            stock_holdings.append({
                'date': date,
                'amount': 0,
                'price': 0
            })
    
    holdings_df = pd.DataFrame(stock_holdings).set_index('date')
    
    # 如果没有提供价格数据，使用持仓中的价格
    if price_data is None:
        price_data = holdings_df[holdings_df['price'] > 0]['price']
    
    # 计算持仓变化
    holdings_df['amount_change'] = holdings_df['amount'].diff()
    
    # 识别买卖点
    buy_signals = holdings_df[holdings_df['amount_change'] > 0]
    sell_signals = holdings_df[holdings_df['amount_change'] < 0]
    
    # 创建子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), 
                                   gridspec_kw={'height_ratios': [2, 1]})
    
    # 上图：价格和买卖点
    ax1.plot(price_data.index, price_data.values, 
             label=f'{stock_code} Price', linewidth=2, color='black')
    
    # 标记买入点
    if not buy_signals.empty:
        buy_dates = [date for date in buy_signals.index if date in price_data.index]
        buy_prices = [price_data.loc[date] for date in buy_dates]
        ax1.scatter(buy_dates, buy_prices, color='green', marker='^', 
                   s=100, zorder=5, label='Buy')
    
    # 标记卖出点
    if not sell_signals.empty:
        sell_dates = [date for date in sell_signals.index if date in price_data.index]
        sell_prices = [price_data.loc[date] for date in sell_dates]
        ax1.scatter(sell_dates, sell_prices, color='red', marker='v', 
                   s=100, zorder=5, label='Sell')
    
    ax1.set_title(f'{stock_code} - Price Chart with Buy/Sell Signals', fontsize=16)
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 下图：持仓量变化
    ax2.bar(holdings_df.index, holdings_df['amount'], 
            color='blue', alpha=0.7, label='Holdings')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Holdings Amount', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # 计算并显示交易统计
    total_buys = len(buy_signals)
    total_sells = len(sell_signals)
    
    print(f"=== {stock_code} 交易统计 ===")
    print(f"总买入次数: {total_buys}")
    print(f"总卖出次数: {total_sells}")
    
    if not buy_signals.empty:
        print("\n买入点详情:")
        for date in buy_signals.index:
            if date in price_data.index:
                print(f"  {date}: 价格 {price_data.loc[date]:.2f}, 持仓变化 +{buy_signals.loc[date, 'amount_change']}")
    
    if not sell_signals.empty:
        print("\n卖出点详情:")
        for date in sell_signals.index:
            if date in price_data.index:
                print(f"  {date}: 价格 {price_data.loc[date]:.2f}, 持仓变化 {sell_signals.loc[date, 'amount_change']}")
    
    return holdings_df, buy_signals, sell_signals

# 使用示例
# holdings_df, buy_signals, sell_signals = plot_detailed_trading_analysis('000001', positions_normal)
  
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_stock_trading_points(stock_code, positions_normal, price_data=None):
    """
    绘制特定股票的买卖点及价格走势
    
    参数:
    stock_code: 股票代码
    positions_normal: 持仓数据
    price_data: 股票价格数据(可选)
    """
    
    # 提取该股票的持仓变化
    stock_holdings = []
    
    dates = sorted(positions_normal.keys())
    for i, date in enumerate(dates):
        position = positions_normal[date]
        stock_list = position.get_stock_list()
        
        if stock_code in stock_list:
            amount = position.get_stock_amount(stock_code)
            price = position.get_stock_price(stock_code)
            weight = position.get_stock_weight(stock_code)
            
            stock_holdings.append({
                'date': date,
                'amount': amount,
                'price': price,
                'weight': weight
            })
        else:
            # 如果当天没有持仓，记录为0
            stock_holdings.append({
                'date': date,
                'amount': 0,
                'price': 0,
                'weight': 0
            })
    
    # 转换为DataFrame
    holdings_df = pd.DataFrame(stock_holdings).set_index('date')
    
    # 识别买卖点
    holdings_df['amount_change'] = holdings_df['amount'].diff()
    
    # 买入点: 持仓量增加
    buy_points = holdings_df[holdings_df['amount_change'] > 0]
    
    # 卖出点: 持仓量减少
    sell_points = holdings_df[holdings_df['amount_change'] < 0]
    
    # 如果没有提供价格数据，尝试从持仓中提取
    if price_data is None:
        # 从持仓数据中提取价格
        price_series = holdings_df[holdings_df['price'] > 0]['price']
    else:
        # 使用提供的价格数据
        price_series = price_data
    
    # 绘制价格走势和买卖点
    plt.figure(figsize=(15, 10))
    
    # 绘制价格走势
    plt.plot(price_series.index, price_series.values, 
             label=f'{stock_code} Price', linewidth=2, color='black', alpha=0.7)
    
    # 标记买入点
    if not buy_points.empty:
        buy_prices = []
        buy_dates = []
        for date in buy_points.index:
            if date in price_series.index:
                buy_prices.append(price_series.loc[date])
                buy_dates.append(date)
        
        plt.scatter(buy_dates, buy_prices, color='green', marker='^', 
                   s=100, zorder=5, label='Buy Points')
    
    # 标记卖出点
    if not sell_points.empty:
        sell_prices = []
        sell_dates = []
        for date in sell_points.index:
            if date in price_series.index:
                sell_prices.append(price_series.loc[date])
                sell_dates.append(date)
        
        plt.scatter(sell_dates, sell_prices, color='red', marker='v', 
                   s=100, zorder=5, label='Sell Points')
    
    plt.title(f'{stock_code} - Price Chart with Buy/Sell Points', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # 输出交易统计
    print(f"交易统计 - {stock_code}:")
    print(f"买入次数: {len(buy_points)}")
    print(f"卖出次数: {len(sell_points)}")
    
    return holdings_df, buy_points, sell_points

from qlib.data import D

def plot_stock_with_qlib_data(stock_code, positions_normal, start_date, end_date):
    """
    使用Qlib数据绘制股票价格和买卖点
    """
    
    # 从Qlib获取股票价格数据
    fields = ['$close', '$volume']
    instruments = [stock_code]
    
    # 获取价格数据
    price_data = D.features(instruments, fields, start_time=start_date, end_time=end_date)
    price_series = price_data['$close'].droplevel('instrument')
    
    # 调用之前的函数绘制图表
    return plot_stock_trading_points(stock_code, positions_normal, price_series)

# 使用示例
# plot_stock_with_qlib_data('000001', positions_normal, '2020-01-01', '2020-12-31')
# 使用示例
# holdings_df, buy_points, sell_points = plot_stock_trading_points('000001', positions_normal)
   # 遍历记录器并导出
for recorder_id, recorder in recorders.items():

    
        # 检查数据结构
    positions_normal = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")

    holdings_df, buy_signals, sell_signals = plot_interactive_trading_chart('SZ000333', positions_normal)
    
    holdings_df, buy_signals, sell_signals = plot_detailed_trading_analysis('SZ000333', positions_normal)
    
    holdings_df, buy_points, sell_points = plot_stock_trading_points('SZ000333', positions_normal)

    plot_stock_with_qlib_data('SZ000333', positions_normal, '2020-01-01', '2020-12-31')