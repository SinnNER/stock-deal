"""
模拟数据生成器 - 用于测试
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_ohlcv(symbol='BTCUSDT', days=90, interval='1h', initial_price=45000, volatility=0.02):
    """
    生成模拟K线数据
    
    Args:
        days: 天数
        interval: 时间间隔 (1h, 4h, 1d)
        initial_price: 初始价格
        volatility: 波动率
    """
    # 计算K线数量
    if interval == '1h':
        periods = days * 24
    elif interval == '4h':
        periods = days * 6
    else:  # 1d
        periods = days
    
    # 生成随机价格走势 (几何布朗运动)
    np.random.seed(42)  # 固定种子，可重现
    returns = np.random.normal(0.0001, volatility, periods)
    price_series = initial_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV
    data = []
    base_time = datetime.now() - timedelta(days=days)
    
    for i, close in enumerate(price_series):
        # 生成OHLC
        high = close * (1 + abs(np.random.normal(0, volatility/2)))
        low = close * (1 - abs(np.random.normal(0, volatility/2)))
        open_price = np.random.uniform(low, high)
        
        # 确保OHLC关系正确
        high = max(open, close, high)
        low = min(open, close, low)
        
        volume = np.random.uniform(100, 1000)
        
        timestamp = base_time + timedelta(hours=i)
        data.append([timestamp, open_price, high, low, close, volume])
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df.set_index('timestamp', inplace=True)
    
    return df

def generate_trending_ohlcv(symbol='BTCUSDT', days=90, interval='1h', 
                           initial_price=45000, trend=0.001, volatility=0.02):
    """
    生成带趋势的模拟K线数据
    
    Args:
        trend: 趋势强度 (正=上涨, 负=下跌)
    """
    if interval == '1h':
        periods = days * 24
    elif interval == '4h':
        periods = days * 6
    else:
        periods = days
    
    np.random.seed(123)
    
    # 趋势 + 随机
    returns = np.random.normal(trend, volatility, periods)
    price_series = initial_price * np.exp(np.cumsum(returns))
    
    data = []
    base_time = datetime.now() - timedelta(days=days)
    
    for i, close in enumerate(price_series):
        high = close * (1 + abs(np.random.normal(0, volatility/2)))
        low = close * (1 - abs(np.random.normal(0, volatility/2)))
        open_price = np.random.uniform(low, high)
        
        high = max(open_price, close, high)
        low = min(open_price, close, low)
        
        volume = np.random.uniform(100, 1000)
        timestamp = base_time + timedelta(hours=i)
        
        data.append([timestamp, open_price, high, low, close, volume])
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df.set_index('timestamp', inplace=True)
    
    return df

if __name__ == '__main__':
    # 测试
    df = generate_ohlcv(days=30)
    print(df.tail(10))
    print(f"\n数据条数: {len(df)}")
    print(f"价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")