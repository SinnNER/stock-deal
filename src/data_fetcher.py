"""
数据获取模块 - 国内数据源
"""
import requests
import pandas as pd
from typing import Optional
import json

class DataFetcher:
    """数据获取器 - 国内源"""
    
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        })
    
    def fetch_ohlcv(self, symbol='SH600519', interval='1d', limit=100) -> pd.DataFrame:
        """获取K线数据
        
        symbol格式: SH600519(上证), SZ000001(深证), BTCUSDT(数字货币)
        interval: 1d, 1w, 1h, 30m, 15m, 5m, 1m
        """
        if self.use_mock:
            return self._mock_data(symbol, interval, limit)
        
        # A股 - 东方财富
        if symbol.startswith('SH') or symbol.startswith('SZ'):
            return self._eastmoney_ohlcv(symbol, interval, limit)
        
        # 数字货币 - 暂时用模拟数据（国内没有免费好用的币价API）
        return self._mock_data(symbol, interval, limit)
    
    def _eastmoney_ohlcv(self, symbol, interval, limit):
        """东方财富K线"""
        # 转换symbol: SH600519 -> 1.600519
        market = '1' if symbol.startswith('SH') else '0'
        code = symbol[2:]
        secid = f"{market}.{code}"
        
        # 映射interval
        interval_map = {
            '1d': '101',
            '1w': '102',
            '1h': '60',
            '30m': '30',
            '15m': '15',
            '5m': '5',
            '1m': '1'
        }
        klt = interval_map.get(interval, '101')
        
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': klt,
            'fqt': '1',  # 前复权
            'end': '20500101',
            'lmt': limit
        }
        
        r = self.session.get(url, params=params, timeout=10)
        data = r.json()
        
        klines = data['data']['klines']
        
        records = []
        for k in klines:
            parts = k.split(',')
            # 格式: 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
            records.append({
                'timestamp': parts[0],
                'open': float(parts[1]),
                'close': float(parts[2]),
                'high': float(parts[3]),
                'low': float(parts[4]),
                'volume': float(parts[5]) if len(parts) > 5 else 0,
            })
        
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 排序
        df = df.sort_index()
        
        return df
    
    def _mock_data(self, symbol, interval, limit):
        """模拟数据"""
        from mock_data import generate_ohlcv, generate_trending_ohlcv
        import random
        
        if interval == '1d':
            days = min(limit + 10, 365)
        elif interval == '1h':
            days = min(limit // 24 + 10, 90)
        else:
            days = min(limit // 24 + 5, 30)
        
        # A股模拟
        if symbol.startswith('SH') or symbol.startswith('SZ'):
            initial_price = random.uniform(10, 300)
            trend = random.uniform(-0.001, 0.002)
        else:
            initial_price = 45000
            trend = random.uniform(-0.0005, 0.001)
        
        df = generate_trending_ohlcv(
            days=days,
            interval='1d' if interval == '1d' else '1h',
            initial_price=initial_price,
            trend=trend,
            volatility=0.03
        )
        
        if interval == '1d':
            # 重采样日线
            df = df.resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
            df = df.dropna()
        
        return df.tail(limit)
    
    def get_realtime(self, symbol='SH600519'):
        """实时行情"""
        if symbol.startswith('SH') or symbol.startswith('SZ'):
            market = '1' if symbol.startswith('SH') else '0'
            code = symbol[2:]
            secid = f"{market}.{code}"
            
            url = 'https://push2.eastmoney.com/api/qt/ulist.np/get'
            params = {
                'fltt': '2',
                'invt': '2',
                'fields': 'f2,f3,f4,f12,f13,f104,f105',
                'secid': secid
            }
            
            r = self.session.get(url, params=params, timeout=10)
            data = r.json()['data']['diff'][0]
            
            return {
                'symbol': symbol,
                'price': data['f2'],
                'change_pct': data['f3'],
                'name': data.get('f104', '')
            }
        return {}


if __name__ == '__main__':
    f = DataFetcher()
    
    # 测试A股
    print("获取茅台日线...")
    df = f.fetch_ohlcv('SH600519', '1d', 30)
    print(df.tail())
    
    print("\n获取实时行情...")
    quote = f.get_realtime('SH600519')
    print(quote)