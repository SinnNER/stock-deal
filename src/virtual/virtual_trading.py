"""
虚拟交易引擎 - 无限资金，不限频率
"""
import json
from datetime import datetime
from collections import defaultdict

class VirtualTrading:
    """虚拟交易系统"""
    
    def __init__(self):
        # 每只股票的持仓记录
        self.positions = {}  # {symbol: {'quantity': x, 'entry_price': y, 'entry_date': z}}
        
        # 交易日志
        self.trade_log = []
        
        # 每日权益记录
        self.daily_equity = {}
        
        # 按组合分类的结果
        self.portfolio_results = {
            'china_500': {'trades': [], 'stocks': {}},
            'global_500': {'trades': [], 'stocks': {}},
            'us_500': {'trades': [], 'stocks': {}},
        }
    
    def buy(self, symbol, name, price, quantity, date, portfolio='china_500'):
        """买入"""
        self.positions[symbol] = {
            'name': name,
            'quantity': quantity,
            'entry_price': price,
            'entry_date': date,
            'portfolio': portfolio
        }
        
        self.trade_log.append({
            'date': str(date),
            'symbol': symbol,
            'name': name,
            'action': '买入',
            'price': price,
            'quantity': quantity,
            'amount': price * quantity,
            'portfolio': portfolio
        })
    
    def sell(self, symbol, price, date):
        """卖出"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        pnl = (price - pos['entry_price']) * pos['quantity']
        
        self.trade_log.append({
            'date': str(date),
            'symbol': symbol,
            'name': pos['name'],
            'action': '卖出',
            'price': price,
            'quantity': pos['quantity'],
            'amount': price * pos['quantity'],
            'pnl': pnl,
            'pnl_pct': (price - pos['entry_price']) / pos['entry_price'] * 100,
            'holding_days': (date - pos['entry_date']).days if isinstance(date, datetime) else 0,
            'portfolio': pos['portfolio']
        })
        
        # 记录到组合结果
        portfolio = pos['portfolio']
        if symbol not in self.portfolio_results[portfolio]['stocks']:
            self.portfolio_results[portfolio]['stocks'][symbol] = {
                'name': pos['name'],
                'trades': 0,
                'wins': 0,
                'total_pnl': 0
            }
        
        stock_stat = self.portfolio_results[portfolio]['stocks'][symbol]
        stock_stat['trades'] += 1
        if pnl > 0:
            stock_stat['wins'] += 1
        stock_stat['total_pnl'] += pnl
        
        del self.positions[symbol]
        return pnl
    
    def get_position(self, symbol):
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self):
        """获取所有持仓"""
        return self.positions
    
    def get_portfolio_summary(self, portfolio):
        """获取组合汇总"""
        stocks = self.portfolio_results[portfolio]['stocks']
        
        if not stocks:
            return {'stocks': 0, 'total_trades': 0, 'wins': 0, 'win_rate': 0, 'total_pnl': 0}
        
        total_trades = sum(s['trades'] for s in stocks.values())
        wins = sum(s['wins'] for s in stocks.values())
        total_pnl = sum(s['total_pnl'] for s in stocks.values())
        
        return {
            'stocks': len(stocks),
            'total_trades': total_trades,
            'wins': wins,
            'win_rate': wins / total_trades * 100 if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'details': stocks
        }
    
    def save_log(self, path='virtual_trade_log.json'):
        """保存交易日志"""
        data = {
            'trade_log': self.trade_log,
            'portfolios': {
                k: self.get_portfolio_summary(k) for k in self.portfolio_results.keys()
            }
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class VirtualBacktest:
    """虚拟交易回测"""
    
    def __init__(self, strategy_fn, initial_capital=None):
        """
        虚拟交易不需要资金上限
        strategy_fn: 策略函数 (df, positions) -> signal
                     positions: 当前持仓dict
                     return: 1=买入, -1=卖出, 0=持有
        """
        self.strategy = strategy_fn
        self.vt = VirtualTrading()
        self.trade_log = []
    
    def run(self, df, symbol, name, portfolio='china_500', min_holding_days=1):
        """
        运行虚拟交易回测
        min_holding_days: 最小持仓天数（防止频繁交易）
        """
        current_position = None
        entry_date = None
        
        for i in range(50, len(df)):  # 预热50天
            date = df.index[i]
            price = df.iloc[i]['close']
            
            # 策略信号
            signal = self.strategy(df.iloc[:i+1], current_position)
            
            # 持仓天数检查
            can_trade = True
            if entry_date and isinstance(date, datetime):
                holding_days = (date - entry_date).days
                if holding_days < min_holding_days:
                    can_trade = False
            
            # 买入
            if signal == 1 and not current_position and can_trade:
                quantity = 10000 / price  # 虚拟购买10000元
                self.vt.buy(symbol, name, price, quantity, date, portfolio)
                current_position = {'price': price, 'quantity': quantity}
                entry_date = date
            
            # 卖出
            elif (signal == -1 or signal == 0) and current_position and can_trade:
                pnl = self.vt.sell(symbol, price, date)
                current_position = None
                entry_date = None
        
        # 最后持仓
        if current_position:
            price = df.iloc[-1]['close']
            self.vt.sell(symbol, price, df.index[-1])
        
        return self.vt
    
    def run_multi(self, stocks, portfolio='china_500', min_holding_days=1):
        """多股票回测"""
        from src.data_fetcher import DataFetcher
        
        f = DataFetcher()
        
        print(f"\n{'='*60}")
        print(f"虚拟交易回测: {portfolio}")
        print('='*60)
        
        results = []
        
        for symbol, name, industry in stocks:
            try:
                df = f.fetch_ohlcv(symbol, '1d', 180)
                if len(df) < 100:
                    continue
                
                vt = self.run(df, symbol, name, portfolio, min_holding_days)
                
                # 统计
                trades = [t for t in vt.trade_log if t['action'] == '卖出']
                if trades:
                    pnl = sum(t['pnl'] for t in trades)
                    wins = len([t for t in trades if t['pnl'] > 0])
                    win_rate = wins / len(trades) * 100
                    
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'industry': industry,
                        'trades': len(trades),
                        'wins': wins,
                        'win_rate': win_rate,
                        'pnl': pnl,
                        'avg_pnl': pnl / len(trades) if trades else 0
                    })
                    
                    print(f"{symbol} {name:6s} | 交易:{len(trades)} | 胜率:{win_rate:5.1f}% | 盈亏:{pnl:,.0f}")
                    
            except Exception as e:
                print(f"{symbol} 失败: {e}")
        
        return results


def virtual_strategy_rsi(df, position):
    """虚拟交易RSI策略"""
    from src.strategies import rsi_strategy
    return rsi_strategy(df)


def virtual_strategy_ma(df, position):
    """均线策略"""
    from src.strategies import sma_cross
    return sma_cross(df)


def virtual_strategy_breakout(df, position):
    """突破策略"""
    from src.strategies import breakout
    return breakout(df)


# 策略注册表
VIRTUAL_STRATEGIES = {
    'rsi': virtual_strategy_rsi,
    'ma': virtual_strategy_ma,
    'breakout': virtual_strategy_breakout,
}