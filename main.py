#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易机器人 - 主入口
用法:
    python main.py backtest --symbol SH600519 --strategy sma_cross
    python main.py paper-trade --symbol SH600519 --strategy rsi
    python main.py list-strategies
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import DataFetcher
from mock_data import generate_ohlcv, generate_trending_ohlcv
from backtest import BacktestEngine
from strategies import get_strategy, STRATEGIES
from paper_trading import TradingBot

def cmd_backtest(args):
    print("回测: {} | 策略: {}".format(args.symbol, args.strategy))
    
    fetcher = DataFetcher()
    df = fetcher.fetch_ohlcv(args.symbol, interval=args.timeframe, limit=args.limit)
    print("数据: {} 条K线 ({} ~ {})".format(len(df), df.index[0].date(), df.index[-1].date()))
    
    strategy_fn = get_strategy(args.strategy)
    engine = BacktestEngine(initial_capital=args.capital)
    metrics = engine.run(df, strategy_fn, args.symbol)
    
    print("\n" + "="*50)
    print("回测结果")
    print("="*50)
    print("初始资金:     ${:.2f}".format(metrics['initial_capital']))
    print("最终权益:     ${:.2f}".format(metrics['final_equity']))
    print("总收益率:     {:.2f}%".format(metrics['total_return_pct']))
    print("最大回撤:     {:.2f}%".format(metrics['max_drawdown_pct']))
    print("交易次数:     {}".format(metrics['total_trades']))
    print("胜率:         {:.1f}%".format(metrics['win_rate_pct']))
    print("="*50)

def cmd_paper_trade(args):
    print("模拟交易: {} | 策略: {}".format(args.symbol, args.strategy))
    print("初始资金: ${:.2f}".format(args.capital))
    print("实盘阈值: 3% 收益率 + 至少3笔交易")
    print("-" * 50)
    
    # 获取历史数据
    fetcher = DataFetcher()
    df = fetcher.fetch_ohlcv(args.symbol, interval=args.timeframe, limit=args.limit)
    
    strategy_fn = get_strategy(args.strategy)
    bot = TradingBot(strategy_fn, args.symbol, initial_capital=args.capital)
    
    warmup = min(args.warmup, len(df) - 10)
    
    # 逐根K线模拟
    for i in range(warmup, len(df)):
        tick_df = df.iloc[:i+1]
        status = bot.tick(tick_df)
        
        # 打印交易信号
        if status.get('just_traded'):
            action = status.get('action', '')
            print("[{}] {} {} @ ${:.2f} | 权益: ${:.2f} | 收益: {:.2f}%".format(
                tick_df.index[-1].date(),
                action,
                args.symbol,
                status['price'],
                status['equity'],
                status['total_pnl_pct']))
    
    print("\n" + "="*50)
    print("模拟交易结束")
    print("="*50)
    
    status = bot.get_status()
    print("总交易次数:   {}".format(status['total_trades']))
    print("实盘审核状态: {}".format(status['message']))
    print("="*50)
    
    bot.save_log('trade_log.json')

def cmd_list_strategies(args):
    print("可用策略:")
    for name in STRATEGIES.keys():
        print("  - {}".format(name))

def main():
    parser = argparse.ArgumentParser(description='量化交易机器人')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    bt_parser = subparsers.add_parser('backtest', help='回测')
    bt_parser.add_argument('--symbol', default='SH600519', help='交易对')
    bt_parser.add_argument('--strategy', default='rsi', help='策略')
    bt_parser.add_argument('--timeframe', default='1d', help='时间框架')
    bt_parser.add_argument('--limit', type=int, default=60, help='K线数量')
    bt_parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    
    pt_parser = subparsers.add_parser('paper-trade', help='模拟交易(历史回放)')
    pt_parser.add_argument('--symbol', default='SH600519', help='交易对')
    pt_parser.add_argument('--strategy', default='rsi', help='策略')
    pt_parser.add_argument('--timeframe', default='1d', help='时间框架')
    pt_parser.add_argument('--limit', type=int, default=60, help='K线数量')
    pt_parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    pt_parser.add_argument('--warmup', type=int, default=30, help='预热K线数')
    
    subparsers.add_parser('list-strategies', help='列出可用策略')
    
    args = parser.parse_args()
    
    if args.command == 'backtest':
        cmd_backtest(args)
    elif args.command == 'paper-trade':
        cmd_paper_trade(args)
    elif args.command == 'list-strategies':
        cmd_list_strategies(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()