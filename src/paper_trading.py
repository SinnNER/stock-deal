"""
模拟交易引擎 - Paper Trading
"""
import json
from datetime import datetime
from collections import defaultdict

class PaperTrading:
    """模拟交易引擎"""
    
    def __init__(self, initial_capital=10000, fee=0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.fee = fee
        self.positions = {}
        self.trade_log = []
        self.last_equity = initial_capital
        
        # 审核阈值
        self.min_return_for_live = 3.0
        self.min_trades = 3
    
    def buy(self, symbol, quantity, price, timestamp=None):
        """买入"""
        cost = quantity * price * (1 + self.fee)
        if self.cash >= cost:
            self.cash -= cost
            self.positions[symbol] = {
                'side': 'long',
                'quantity': quantity,
                'entry_price': price,
                'entry_time': timestamp or datetime.now()
            }
            self.trade_log.append({
                'time': str(timestamp) if timestamp else datetime.now().isoformat(),
                'action': '买入',
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'pnl': 0
            })
            return True
        return False
    
    def sell(self, symbol, quantity, price, timestamp=None):
        """卖出平仓"""
        if symbol not in self.positions:
            return 0, '无持仓'
        
        pos = self.positions[symbol]
        revenue = quantity * price * (1 - self.fee)
        cost = pos['quantity'] * pos['entry_price'] * (1 + self.fee)
        pnl = revenue - cost
        
        self.cash += revenue
        self.trade_log.append({
            'time': str(timestamp) if timestamp else datetime.now().isoformat(),
            'action': '卖出',
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'pnl': pnl
        })
        
        action = '卖出'
        del self.positions[symbol]
        return pnl, action
    
    def get_equity(self, current_prices):
        """计算当前权益"""
        positions_value = sum(
            pos['quantity'] * current_prices.get(symbol, pos['entry_price'])
            for symbol, pos in self.positions.items()
        )
        return self.cash + positions_value
    
    def get_total_pnl(self, current_prices):
        """计算总盈亏百分比"""
        realized = sum(t['pnl'] for t in self.trade_log)
        return realized / self.initial_capital * 100
    
    def can_go_live(self):
        """检查是否允许实盘交易"""
        if len(self.trade_log) < self.min_trades:
            return False, "交易次数不足: {}/{}".format(len(self.trade_log), self.min_trades)
        
        total_pnl = sum(t['pnl'] for t in self.trade_log)
        total_return = total_pnl / self.initial_capital * 100
        
        if total_return < self.min_return_for_live:
            return False, "收益率不足: {:.2f}%/{}%".format(total_return, self.min_return_for_live)
        
        return True, "审核通过！收益率: {:.2f}%".format(total_return)


class TradingBot:
    """交易机器人"""
    
    def __init__(self, strategy_fn, symbol='SH600519', initial_capital=100000, fee=0.001):
        self.strategy = strategy_fn
        self.symbol = symbol
        self.paper = PaperTrading(initial_capital, fee)
        self.last_signal = 0
    
    def tick(self, df):
        """每个tick执行一次"""
        signal = self.strategy(df)
        current_price = df['close'].iloc[-1]
        timestamp = df.index[-1]
        
        has_position = self.symbol in self.paper.positions
        
        just_traded = False
        action = ''
        
        # 交易逻辑
        if signal == 1 and not has_position:
            # 买入信号
            max_spend = self.paper.cash * 0.95
            quantity = max_spend / current_price
            self.paper.buy(self.symbol, quantity, current_price, timestamp)
            just_traded = True
            action = '买入'
        
        elif signal == -1 and has_position:
            # 卖出信号
            pos = self.paper.positions[self.symbol]
            pnl, action = self.paper.sell(self.symbol, pos['quantity'], current_price, timestamp)
            just_traded = True
        
        # 方向改变也平仓
        elif signal != 0 and signal != self.last_signal and has_position:
            pos = self.paper.positions[self.symbol]
            pnl, action = self.paper.sell(self.symbol, pos['quantity'], current_price, timestamp)
            just_traded = True
        
        self.last_signal = signal
        
        # 权益
        equity = self.paper.get_equity({self.symbol: current_price})
        
        return {
            'price': current_price,
            'signal': signal,
            'position': has_position,
            'cash': self.paper.cash,
            'equity': equity,
            'total_pnl_pct': self.paper.get_total_pnl({self.symbol: current_price}),
            'just_traded': just_traded,
            'action': action
        }
    
    def get_status(self):
        can_live, message = self.paper.can_go_live()
        return {
            'can_live': can_live,
            'message': message,
            'total_trades': len(self.paper.trade_log),
            'min_return_required': "{}%".format(self.paper.min_return_for_live),
        }
    
    def save_log(self, path):
        with open(path, 'w') as f:
            json.dump(self.paper.trade_log, f, indent=2, ensure_ascii=False)