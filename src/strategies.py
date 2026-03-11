"""
内置策略集 - Python 3.6兼容版
"""
import pandas as pd
import numpy as np

def sma_cross(df, fast=20, slow=50):
    """
    均线交叉策略
    - 快线 > 慢线 → 做多
    - 快线 < 慢线 → 做空
    """
    if len(df) < slow:
        return 0
    
    sma_fast = df['close'].rolling(fast).mean()
    sma_slow = df['close'].rolling(slow).mean()
    
    if sma_fast.iloc[-1] > sma_slow.iloc[-1]:
        return 1
    elif sma_fast.iloc[-1] < sma_slow.iloc[-1]:
        return -1
    return 0

def rsi_strategy(df, period=14, oversold=30, overbought=70):
    """
    RSI策略
    - RSI < 30 → 超卖，买入
    - RSI > 70 → 超买，卖出
    """
    if len(df) < period:
        return 0
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = rsi.iloc[-1]
    
    if current_rsi < oversold:
        return 1
    elif current_rsi > overbought:
        return -1
    return 0

def breakout(df, window=20):
    """
    突破策略
    - 突破20日高点 → 做多
    - 跌破20日低点 → 做空
    """
    if len(df) < window:
        return 0
    
    high = df['high'].rolling(window).max()
    low = df['low'].rolling(window).min()
    
    current_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2]
    
    if prev_price < high.iloc[-2] and current_price > high.iloc[-1]:
        return 1
    elif prev_price > low.iloc[-2] and current_price < low.iloc[-1]:
        return -1
    return 0

# 策略注册表
STRATEGIES = {
    'sma_cross': sma_cross,
    'rsi': rsi_strategy,
    'breakout': breakout,
}

def get_strategy(name):
    """获取策略函数"""
    return STRATEGIES.get(name, sma_cross)