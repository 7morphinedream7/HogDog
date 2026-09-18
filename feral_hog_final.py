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
            price += np.random.normal(0, 0.3)
        elif seg == 1: # The Run
            direction = np.random.choice([1, -1])
            price += direction * np.random.normal(3.0, 0.8)
        else: # Random
            price += np.random.normal(0, 1.0)
        prices.append(price)
    df = pd.DataFrame({'close': prices})
    df['high'] = df['close'] + np.random.uniform(0, 0.5, len(df))
    df['low'] = df['close'] - np.random.uniform(0, 0.5, len(df))
    df['open'] = df['close'].shift(1).fillna(df['close'])
    return df

def backtest_feral_hog_final(df, initial_balance=100):
    # Constants
    CONTRACT_SIZE = 100
    MAX_HERD_SIZE = 3
    ACCOUNT_FLOOR = 60.0 # Slightly lower floor to allow for a few losses
    
    # Indicators
    df['atr'] = df['high'].rolling(20).max() - df['low'].rolling(20).min()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    
    balance = initial_balance
    equity = []
    positions = [] # List of (entry_price, direction)
    trailing_stop = None
    in_trade = False
    direction = 0 # 1 for Long, -1 for Short
    
    for i in range(20, len(df)):
        price = df['close'].iloc[i]
        atr = df['atr'].iloc[i]
        
        # Calculate current floating PnL
        floating_pnl = 0
        if in_trade:
            for entry, pos_dir in positions:
                floating_pnl += (price - entry) * pos_dir * 0.01 * CONTRACT_SIZE
        
        current_equity = balance + floating_pnl
        
        # Circuit Breaker
        if current_equity <= ACCOUNT_FLOOR:
            if in_trade:
                balance += floating_pnl
                positions = []
                in_trade = False
                direction = 0
            equity.append(balance)
            continue

        if not in_trade:
            # THE DEN DETECTION
            range_20 = df['high'].iloc[i-20:i].max() - df['low'].iloc[i-20:i].min()
            if range_20 < 2.0 * atr:
                # LONG BREAKOUT
                if price > df['high'].iloc[i-1] + 0.2:
                    in_trade = True
                    direction = 1
                    positions.append((price, 1))
                    trailing_stop = df['low'].iloc[i-20:i].min()
                # SHORT BREAKOUT
                elif price < df['low'].iloc[i-1] - 0.2:
                    in_trade = True
                    direction = -1
                    positions.append((price, -1))
                    trailing_stop = df['high'].iloc[i-20:i].max()
        else:
            # CULLING: Trailing Stop
            if (direction == 1 and price <= trailing_stop) or \
               (direction == -1 and price >= trailing_stop):
                # Close all positions
                for entry, pos_dir in positions:
                    balance += (price - entry) * pos_dir * 0.01 * CONTRACT_SIZE
                positions = []
                in_trade = False
                direction = 0
                trailing_stop = None
                continue
            
            # UPDATE TRAILING STOP (Dynamic based on 3-bar extremes)
            if direction == 1:
                new_stop = df['low'].iloc[i-3:i].min()
                if new_stop > trailing_stop: trailing_stop = new_stop
            else:
                new_stop = df['high'].iloc[i-3:i].max()
                if new_stop < trailing_stop: trailing_stop = new_stop

            # PROLIFERATION (Dynamic ATR Gap)
            if len(positions) < MAX_HERD_SIZE:
                last_entry, _ = positions[-1]
                breed_gap = 0.5 * atr
                
                # Breed if price moves favorably by ATR gap AND herd is in profit
                if (direction == 1 and price >= last_entry + breed_gap) or \
                   (direction == -1 and price <= last_entry - breed_gap):
                    
                    if floating_pnl > 0:
                        positions.append((price, direction))
                        # Tighten stop to lock in profit
                        if direction == 1:
                            trailing_stop = max(trailing_stop, price - breed_gap)
                        else:
                            trailing_stop = min(trailing_stop, price + breed_gap)

        equity.append(current_equity)
        
    return equity

df = generate_synthetic_gold_data()
equity_curve = backtest_feral_hog_final(df)

plt.figure(figsize=(12,6))
plt.plot(equity_curve, label='Omni-Directional Feral Hog', color='green')
plt.axhline(y=100, color='r', linestyle='--', label='Starting Balance')
plt.axhline(y=60, color='black', linestyle=':', label='Account Floor')
plt.title('Feral Hog FINAL - XAUUSD Omni-Directional Simulation')
plt.xlabel('Ticks')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('feral_hog_final.png')

print(f"Final Balance: ${equity_curve[-1]:.2f}")
print(f"Max Drawdown: ${max(equity_curve) - min(equity_curve):.2f}")
print(f"Success: {'Yes' if equity_curve[-1] > 100 else 'No'}")
