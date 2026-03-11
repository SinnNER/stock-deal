# 量化交易机器人

AI驱动的量化交易系统，支持回测和模拟交易。

## 功能

- 数据源：东方财富（A股实时/历史数据）
- 策略：RSI、均线交叉、突破策略
- 回测引擎：支持历史回测
- 模拟交易：Paper Trading，审核机制

## 使用方法

```bash
# 安装依赖
pip3.8 install -r requirements.txt

# 回测
python3.8 main.py backtest --symbol SH601318 --strategy rsi --limit 180

# 模拟交易
python3.8 main.py paper-trade --symbol SH601318 --strategy rsi --limit 180

# 查看策略
python3.8 main.py list-strategies
```

## 策略说明

| 策略 | 说明 |
|------|------|
| rsi | RSI超买超卖策略 |
| sma_cross | 均线交叉策略 |
| breakout | 突破策略 |

## 模拟交易结果（180天）

| 股票 | 策略 | 收益率 | 交易次数 | 胜率 |
|------|------|--------|----------|------|
| 中国平安 | RSI | 10.81% | 5笔 | 80% |
| 贵州茅台 | RSI | 8.35% | 7笔 | 71% |
| 招商银行 | RSI | 5.88% | 9笔 | 78% |
| 长江电力 | RSI | 4.19% | 10笔 | 80% |
| 三一重工 | RSI | 3.49% | 5笔 | 80% |

## 审核标准

- 收益率 ≥ 3%
- 交易次数 ≥ 3笔

## 当前持仓

- 中国平安(601318)：成本61.40元，现价62.55元（持仓中）