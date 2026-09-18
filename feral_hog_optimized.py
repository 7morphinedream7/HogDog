import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_gold_data(days=100, interval='15min'):
    np.random.seed(42)
    periods = days * 24 * (60 // 15)
    price = 2500.0
    prices = []
    segments = np.random.choice([0, 1, 2], size=periods, p=[0.6, 0.1, 0.3])
    for seg in segments:
        if seg == 0: # The Den
            price += np.random.normal(0, 0.4)
        elif seg == 1: # The Run
            direction = np.random.choice([1, -1])
            price += direction * np.random.normal(2.5, 0.7)
        else: # Random
            price += np.random.normal(0, 1.2)
        prices.append(price)
    df = pd.DataFrame({'close': prices})
    df['high'] = df['close'] + np.random.uniform(0, 0.5, len(df))
    df['low'] = df['close'] - np.random.uniform(0, 0.5, len(df))
    df['open'] = df['close'].shift(1).fillna(df['close'])
    return df

def backtest_feral_hog_optimized(df, initial_balance=100):
    # Hyper-parameters for $100 balance
    LOT_SIZE = 0.01
    CONTRACT_SIZE = 100
    BREED_THRESHOLD = 4.0 # 40 pips
    MAX_HERD_SIZE = 3 # Reduced from 5 to protect micro-capital
    ACCOUNT_FLOOR = 70.0 # Circuit breaker
    
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['atr'] = df['high'].rolling(20).max() - df['low'].rolling(20).min()
    
    balance = initial_balance
    equity = []
    positions = [] # List of entry prices
    trailing_stop = None
    in_trade = False
    
    for i in range(20, len(df)):
        price = df['close'].iloc[i]
        ema = df['ema20'].iloc[i]
        
        # Circuit Breaker check
        current_floating = 0
        if in_trade:
            for entry in positions:
                current_floating += (price - entry) * LOT_SIZE * CONTRACT_SIZE
        
        current_equity = balance + current_floating
        if current_equity <= ACCOUNT_FLOOR:
            # Force liquidate everything and stop strategy for this run
            if in_trade:
                balance += current_floating
                positions = []
                in_trade = False
            equity.append(balance)
            continue

        if not in_trade:
            # THE DEN DETECTION
            range_20 = df['high'].iloc[i-20:i].max() - df['low'].iloc[i-20:i].min()
            if range_20 < 2.5 * df['atr'].iloc[i]:
                if price > df['high'].iloc[i-1] + 0.2:
                    in_trade = True
                    positions.append(price)
                    trailing_stop = df['low'].iloc[i-20:i].min()
        else:
            # RAZOR CULLING: Hard Trailing Stop
            if price <= trailing_stop:
                for entry in positions:
                    balance += (price - entry) * LOT_SIZE * CONTRACT_SIZE
                positions = []
                in_trade = False
                trailing_stop = None
                continue
            
            # UPDATE TRAILING STOP (Lock in profit at Higher Lows)
            # Move stop to the low of the last 3 bars
            new_stop = df['low'].iloc[i-3:i].min()
            if new_stop > trailing_stop:
                trailing_stop = new_stop

            # CONTROLLED PROLIFERATION
            if len(positions) < MAX_HERD_SIZE:
                last_entry = positions[-1]
                # Only breed if:
                # 1. Current price is X pips above last entry
                # 2. The total herd is currently in profit (Break-even guard)
                current_herd_profit = sum((price - e) * LOT_SIZE * CONTRACT_SIZE for e in positions)
                if price >= last_entry + BREED_THRESHOLD and current_herd_profit > 0:
                    positions.append(price)
                    # Aggressively move stop to the most recent entry of the new position
                    trailing_stop = max(trailing_stop, price - 2.0)

        equity.append(current_equity)
        
    return equity

df = generate_synthetic_gold_data()
equity_curve = backtest_feral_hog_optimized(df)

plt.figure(figsize=(12,6))
plt.plot(equity_curve, label='Optimized Feral Hog')
plt.axhline(y=100, color='r', linestyle='--', label='Starting Balance')
plt.axhline(y=70, color='black', linestyle=':', label='Account Floor')
plt.title('Feral Hog Optimized - XAUUSD Simulation')
plt.xlabel('Ticks')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('feral_hog_optimized.png')

print(f"Final Balance: ${equity_curve[-1]:.2f}")
print(f"Max Drawdown: ${max(equity_curve) - min(equity_curve):.2f}")
print(f"Success: {'Yes' if equity_curve[-1] > 100 else 'No'}")
