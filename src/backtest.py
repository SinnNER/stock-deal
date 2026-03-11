"""
回测引擎 - 改进版
"""
import pandas as pd
import numpy as np
from typing import List, Callable, Dict, Any

class Trade:
    """单笔交易记录"""
    def __init__(self, entry_time, exit_time, symbol, side, entry_price, exit_price, quantity, pnl, pnl_pct):
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.pnl = pnl
        self.pnl_pct = pnl_pct

class BacktestEngine:
    def __init__(self, initial_capital=10000, fee=0.001):
        self.initial_capital = initial_capital
        self.fee = fee
        self.trades = []
        self.equity_curve = []
    
    def run(self, df, strategy_fn, symbol='BTC/USDT'):
        """运行回测
        
        策略信号: 1=做多, -1=做空, 0=空仓/平仓
        """
        cash = self.initial_capital
        position = 0  # 持仓数量
        position_side = None  # 'long' or 'short'
        entry_price = 0
        
        self.trades = []
        self.equity_curve = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            price = row['close']
            signal = strategy_fn(df.iloc[:i+1])
            
            # 当前权益
            if position > 0:
                if position_side == 'long':
                    equity = cash + position * price
                else:
                    equity = cash + (entry_price - price) * position
            else:
                equity = cash
            
            self.equity_curve.append({
                'timestamp': df.index[i],
                'equity': equity,
                'price': price,
                'position': position_side
            })
            
            # ========== 交易逻辑 ==========
            
            # 平仓信号 (0 或 方向改变)
            should_close = False
            if signal == 0:
                should_close = True
            elif position_side == 'long' and signal < 0:
                should_close = True  # 多转空
            elif position_side == 'short' and signal > 0:
                should_close = True  # 空转多
            
            # 执行平仓
            if should_close and position > 0:
                if position_side == 'long':
                    exit_price = price * (1 - self.fee)
                    pnl = (exit_price - entry_price) * position
                else:
                    exit_price = price * (1 + self.fee)
                    pnl = (entry_price - exit_price) * position
                
                self.trades.append(Trade(
                    entry_time=df.index[i-1],
                    exit_time=df.index[i],
                    symbol=symbol,
                    side=position_side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=position,
                    pnl=pnl,
                    pnl_pct=pnl / self.initial_capital * 100
                ))
                
                if position_side == 'long':
                    cash += exit_price * position
                else:
                    cash += position * entry_price - (entry_price - exit_price) * position
                
                position = 0
                position_side = None
            
            # 开仓
            if signal > 0 and position == 0:  # 做多
                max_spend = cash * (1 - self.fee)
                quantity = max_spend / price
                position = quantity
                position_side = 'long'
                entry_price = price * (1 + self.fee)
                cash -= entry_price * quantity
                
            elif signal < 0 and position == 0:  # 做空
                max_spend = cash * (1 - self.fee)  # 融券保证金
                quantity = max_spend / price
                position = quantity
                position_side = 'short'
                entry_price = price * (1 + self.fee)
        
        return self.get_metrics()
    
    def get_metrics(self):
        """计算回测指标"""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min() * 100
        
        # 胜率
        winning_trades = [t for t in self.trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'total_trades': len(self.trades),
            'win_rate_pct': win_rate,
            'avg_win': np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t.pnl for t in self.trades if t.pnl < 0]) if [t for t in self.trades if t.pnl < 0] else 0,
        }