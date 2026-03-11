#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟交易主程序
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.stocks import CHINA_500, GLOBAL_500, US_STOCKS
from src.virtual.virtual_trading import VirtualBacktest, VIRTUAL_STRATEGIES
from src.data_fetcher import DataFetcher


def run_china_500():
    """中国500强虚拟交易"""
    print("\n" + "="*70)
    print("【中国500强虚拟交易】")
    print("="*70)
    
    bt = VirtualBacktest(VIRTUAL_STRATEGIES['rsi'])
    results = bt.run_multi(CHINA_500[:20], 'china_500', min_holding_days=3)
    
    return results


def run_global_500():
    """全球500强虚拟交易"""
    print("\n" + "="*70)
    print("【全球500强虚拟交易】")
    print("="*70)
    
    bt = VirtualBacktest(VIRTUAL_STRATEGIES['rsi'])
    results = bt.run_multi(GLOBAL_500[:15], 'global_500', min_holding_days=3)
    
    return results


def run_us_500():
    """美国500强虚拟交易（模拟）"""
    print("\n" + "="*70)
    print("【美国500强虚拟交易】- 需开通美股账户")
    print("="*70)
    
    # 美股需要境外API，暂时跳过
    print("提示: 美股数据需使用境外API，当前环境无法访问")
    print("建议: 开通盈透证券或富途证券账户")
    
    return []


def analyze_results(all_results):
    """分析结果"""
    print("\n" + "="*70)
    print("【虚拟交易汇总分析】")
    print("="*70)
    
    # 按收益率排序
    all_results.sort(key=lambda x: x['pnl'], reverse=True)
    
    print("\nTop 10 盈利股票:")
    for i, r in enumerate(all_results[:10], 1):
        print(f"  {i:2d}. {r['symbol']} {r['name']:6s} | 交易:{r['trades']} | 胜率:{r['win_rate']:5.1f}% | 盈亏:{r['pnl']:,.0f}")
    
    # 亏损的
    losers = [r for r in all_results if r['pnl'] < 0]
    if losers:
        print(f"\n亏损股票 ({len(losers)}只):")
        for r in losers[:5]:
            print(f"  {r['symbol']} {r['name']:6s} | 盈亏:{r['pnl']:,.0f}")
    
    # 统计
    total_pnl = sum(r['pnl'] for r in all_results)
    wins = len([r for r in all_results if r['pnl'] > 0])
    print(f"\n总计: {len(all_results)}只股票 | 盈利:{wins}只 | 亏损:{len(all_results)-wins}只 | 总盈亏:{total_pnl:,.0f}")
    
    return all_results


def main():
    all_results = []
    
    # 中国500强
    results1 = run_china_500()
    all_results.extend(results1)
    
    # 全球500强
    results2 = run_global_500()
    all_results.extend(results2)
    
    # 美国500强
    run_us_500()
    
    # 分析
    analyze_results(all_results)
    
    print("\n" + "="*70)
    print("注: 虚拟交易仅供策略验证，不涉及真实资金")
    print("="*70)


if __name__ == '__main__':
    main()