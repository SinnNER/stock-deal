#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实交易模拟 - 有资金和频率限制
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_fetcher import DataFetcher
from src.strategies import get_strategy
from src.virtual.real_trading import RealTrading, RealTradingConfig

def run_real_trading():
    """真实交易模拟"""
    print("\n" + "="*70)
    print("【真实交易模拟】- 资金10万，持仓最多10只，频率按日")
    print("="*70)
    
    # 配置
    config = {
        'capital': 100000,      # 10万
        'max_positions': 10,    # 最多10只
        'frequency': '1d',      # 每日可交易
        'fee': 0.001            # 0.1%手续费
    }
    
    # 股票池
    stocks = [
        ('SH601318', '中国平安'),
        ('SH600036', '招商银行'),
        ('SH600519', '贵州茅台'),
        ('SH601318', '中国平安'),
        ('SH600900', '长江电力'),
        ('SH600028', '中国石化'),
        ('SH600031', '三一重工'),
        ('SH600887', '伊利股份'),
        ('SH601012', '隆基绿能'),
        ('SH600276', '恒瑞医药'),
    ]
    
    f = DataFetcher()
    traders = {}
    
    # 为每只股票创建交易器
    for symbol, name in stocks:
        traders[symbol] = {
            'name': name,
            'trader': RealTrading(
                initial_capital=config['capital'],
                max_positions=config['max_positions'],
                frequency=config['frequency'],
                fee_rate=config['fee']
            )
        }
    
    # 获取大盘数据
    print("\n获取大盘数据...")
    market_df = f.fetch_ohlcv('SH000001', '1d', 180)
    print(f"上证指数: {len(market_df)}条数据")
    
    # 回测
    print("\n开始回测...")
    
    for symbol, data in traders.items():
        print(f"处理 {symbol} {data['name']}...")
        
        try:
            df = f.fetch_ohlcv(symbol, '1d', 180)
            if len(df) < 100:
                continue
            
            trader = data['trader']
            strategy = get_strategy('rsi')
            
            # 逐日回测
            for i in range(50, len(df)):
                date = df.index[i]
                price = df.iloc[i]['close']
                
                signal = strategy(df.iloc[:i+1])
                
                has_position = symbol in trader.positions
                
                # 买入
                if signal == 1 and not has_position:
                    max_qty = (trader.cash * 0.9) / price  # 90%仓位
                    qty = max_qty
                    trader.buy(symbol, data['name'], price, qty, date)
                
                # 卖出
                elif signal == -1 and has_position:
                    trader.sell(symbol, price, date)
                
                # 平仓信号
                elif signal == 0 and has_position:
                    trader.sell(symbol, price, date)
            
            # 最终状态
            status = trader.get_status()
            print(f"  {symbol}: 交易{status['total_trades']}次 | 收益{status['return_pct']:.2f}%")
            
        except Exception as e:
            print(f"  {symbol} 失败: {e}")
    
    # 汇总
    print("\n" + "="*70)
    print("【真实交易汇总】")
    print("="*70)
    
    total_pnl = 0
    total_trades = 0
    
    for symbol, data in traders.items():
        status = data['trader'].get_status()
        total_pnl += status['total_pnl']
        total_trades += status['total_trades']
        
        if status['total_trades'] > 0:
            print(f"{symbol} {data['name']:6s} | 交易:{status['total_trades']:2d}次 | 收益:{status['return_pct']:6.2f}% | 盈利:{status['total_pnl']:,.0f}")
    
    print("-"*70)
    print(f"总计: {len(traders)}只股票 | 交易{total_trades}次 | 总盈亏:{total_pnl:,.0f}")
    print(f"资金使用: 10万上限 | 持仓上限:10只 | 频率:按日")


def run_frequency_test():
    """测试不同交易频率"""
    print("\n" + "="*70)
    print("【交易频率测试】- 中国平安")
    print("="*70)
    
    frequencies = ['1d', '3d', '5d', '1w', '2w', '1M']
    
    f = DataFetcher()
    df = f.fetch_ohlcv('SH601318', '1d', 180)
    strategy = get_strategy('rsi')
    
    for freq in frequencies:
        trader = RealTrading(
            initial_capital=100000,
            max_positions=10,
            frequency=freq,
            fee_rate=0.001
        )
        
        for i in range(50, len(df)):
            date = df.index[i]
            price = df.iloc[i]['close']
            signal = strategy(df.iloc[:i+1])
            
            has_position = 'SH601318' in trader.positions
            
            if signal == 1 and not has_position:
                qty = (trader.cash * 0.9) / price
                trader.buy('SH601318', '中国平安', price, qty, date)
            elif (signal == -1 or signal == 0) and has_position:
                trader.sell('SH601318', price, date)
        
        status = trader.get_status()
        print(f"频率:{freq:4s} | 交易:{status['total_trades']:2d}次 | 收益:{status['return_pct']:6.2f}%")


if __name__ == '__main__':
    run_real_trading()
    run_frequency_test()