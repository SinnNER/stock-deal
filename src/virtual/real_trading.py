"""
真实交易模拟器 - 有资金限制和频率限制
"""
import json
from datetime import datetime, timedelta
from collections import defaultdict

class RealTradingConfig:
    """真实交易配置"""
    
    # 交易频率选项
    FREQUENCY_DAILY = '1d'
    FREQUENCY_3DAYS = '3d'
    FREQUENCY_5DAYS = '5d'
    FREQUENCY_WEEKLY = '1w'
    FREQUENCY_2WEEKS = '2w'
    FREQUENCY_MONTHLY = '1M'
    FREQUENCY_QUARTERLY = '3M'
    FREQUENCY_HALFYEAR = '6M'
    FREQUENCY_YEARLY = '1Y'
    
    @staticmethod
    def get_frequency_days(freq):
        """交易频率对应的天数"""
        mapping = {
            '1d': 1,
            '3d': 3,
            '5d': 5,
            '1w': 7,
            '2w': 14,
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
        }
        return mapping.get(freq, 1)


class RealTrading:
    """真实交易模拟器"""
    
    def __init__(self, 
                 initial_capital=100000,
                 max_positions=10,
                 max_trades_per_day=None,
                 frequency='1d',
                 fee_rate=0.001):
        
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_positions = max_positions
        self.frequency = frequency
        self.fee_rate = fee_rate
        
        # 频率控制
        self.min_trade_interval = RealTradingConfig.get_frequency_days(frequency)
        self.last_trade_date = None
        
        # 持仓
        self.positions = {}  # {symbol: {'name':, 'quantity':, 'entry_price':, 'entry_date':}}
        
        # 交易日志
        self.trade_log = []
        
        # 每日记录
        self.daily_records = []
    
    def can_trade(self, date):
        """检查是否可以交易"""
        if self.last_trade_date is None:
            return True
        
        if isinstance(date, datetime):
            days_diff = (date - self.last_trade_date).days
        else:
            days_diff = 1
        
        return days_diff >= self.min_trade_interval
    
    def buy(self, symbol, name, price, quantity, date):
        """买入"""
        cost = price * quantity * (1 + self.fee_rate)
        
        if cost > self.cash:
            return False, '资金不足'
        
        if len(self.positions) >= self.max_positions:
            return False, '持仓已达上限'
        
        if not self.can_trade(date):
            return False, f'交易频率限制({self.min_trade_interval}天内不能交易)'
        
        self.cash -= cost
        self.positions[symbol] = {
            'name': name,
            'quantity': quantity,
            'entry_price': price,
            'entry_date': date,
            'cost': cost
        }
        
        self.last_trade_date = date
        
        self.trade_log.append({
            'date': str(date),
            'symbol': symbol,
            'name': name,
            'action': '买入',
            'price': price,
            'quantity': quantity,
            'amount': cost,
            'cash_after': self.cash,
            'position_count': len(self.positions)
        })
        
        return True, '成功'
    
    def sell(self, symbol, price, date):
        """卖出"""
        if symbol not in self.positions:
            return False, '无持仓'
        
        if not self.can_trade(date):
            return False, f'交易频率限制({self.min_trade_interval}天内不能交易)'
        
        pos = self.positions[symbol]
        revenue = price * pos['quantity'] * (1 - self.fee_rate)
        pnl = revenue - pos['cost']
        
        self.cash += revenue
        del self.positions[symbol]
        
        self.last_trade_date = date
        
        self.trade_log.append({
            'date': str(date),
            'symbol': symbol,
            'name': pos['name'],
            'action': '卖出',
            'price': price,
            'quantity': pos['quantity'],
            'amount': revenue,
            'pnl': pnl,
            'pnl_pct': pnl / pos['cost'] * 100,
            'cash_after': self.cash,
            'position_count': len(self.positions)
        })
        
        return True, f'成功，盈利{pnl:.2f}'
    
    def get_equity(self, current_prices):
        """当前权益"""
        positions_value = sum(
            pos['quantity'] * current_prices.get(symbol, pos['entry_price'])
            for symbol, pos in self.positions.items()
        )
        return self.cash + positions_value
    
    def get_status(self):
        """状态"""
        total_pnl = sum(t.get('pnl', 0) for t in self.trade_log if t['action'] == '卖出')
        
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'positions': len(self.positions),
            'total_trades': len([t for t in self.trade_log if t['action'] == '卖出']),
            'total_pnl': total_pnl,
            'return_pct': (total_pnl / self.initial_capital) * 100
        }
    
    def save_log(self, path='real_trade_log.json'):
        """保存"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'config': {
                    'initial_capital': self.initial_capital,
                    'max_positions': self.max_positions,
                    'frequency': self.frequency,
                    'fee_rate': self.fee_rate
                },
                'status': self.get_status(),
                'trades': self.trade_log
            }, f, ensure_ascii=False, indent=2)


class RealPortfolioManager:
    """真实交易组合管理器"""
    
    def __init__(self, config):
        self.config = config
        self.traders = {}  # 按频率创建不同的交易器
        self.daily_data = {}  # 大盘数据
    
    def add_stock(self, symbol, name):
        """添加跟踪股票"""
        if symbol not in self.traders:
            self.traders[symbol] = {
                'name': name,
                'trader': RealTrading(
                    initial_capital=self.config['capital'],
                    max_positions=self.config['max_positions'],
                    frequency=self.config['frequency'],
                    fee_rate=self.config.get('fee', 0.001)
                ),
                'signals': []
            }
    
    def update(self, date, prices):
        """每日更新"""
        for symbol, data in self.traders.items():
            if symbol not in prices:
                continue
            
            price = prices[symbol]['close']
            trader = data['trader']
            
            # 计算权益
            equity = trader.get_equity({symbol: price})
            
            data['signals'].append({
                'date': str(date),
                'price': price,
                'cash': trader.cash,
                'equity': equity,
                'positions': len(trader.positions)
            })
    
    def get_summary(self):
        """汇总"""
        total_pnl = 0
        total_trades = 0
        
        for symbol, data in self.traders.items():
            status = data['trader'].get_status()
            total_pnl += status['total_pnl']
            total_trades += status['total_trades']
        
        return {
            'stocks': len(self.traders),
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'return_pct': total_pnl / self.config['capital'] * 100
        }