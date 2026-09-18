import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_hf_gold_data(days=10, interval='1min'):
    """
    Generates High-Frequency style synthetic data with 'Flash Bursts'
    to test micro-proliferation logic.
    """
    np.random.seed(42)
    periods = days * 24 * 60
    price = 2500.0
    prices = []
    
    # HF patterns: 
    # 0: Noise (most of the time)
    # 1: Flash Burst (The Hog Run - very short, very aggressive)
    # 2: Mean Reversion (The Trap)
    segments = np.random.choice([0, 1, 2], size=periods, p=[0.85, 0.05, 0.1])
    
    for seg in segments:
        if seg == 0: # Noise
            price += np.random.normal(0, 0.1)
        elif seg == 1: # Flash Burst
            direction = np.random.choice([1, -1])
            # A burst lasts for a few minutes, simulated here as a strong push
            price += direction * np.random.normal(0.5, 0.1)
        else: # Mean Reversion / Trap
            price += np.random.normal(0, 0.3)
        prices.append(price)
        
    df = pd.DataFrame({'close': prices})
    df['high'] = df['close'] + np.random.uniform(0, 0.1, len(df))
    df['low'] = df['close'] - np.random.uniform(0, 0.1, len(df))
    return df

def backtest_hf_feral_hog(df, initial_balance=100):
    # HF Hyper-parameters
    CONTRACT_SIZE = 100
    ALPHA_LOT = 0.02 # Start stronger to cover noise
    BREED_LOT = 0.01
    BREED_GAP = 0.3 # 3 pips - very tight proliferation
    MAX_HERD_SIZE = 4
    TRAIL_STOP_PIPS = 0.5 # Razor stop: 5 pips
    ACCOUNT_FLOOR = 50.0
    
    balance = initial_balance
    equity = []
    positions = [] # List of entry prices
    direction = 0
    trailing_stop = None
    in_trade = False
    
    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        
        # Calculate floating PnL
        floating_pnl = 0
        if in_trade:
            for entry in positions:
                floating_pnl += (price - entry) * direction * 0.01 * CONTRACT_SIZE
            # First position was 0.02
            floating_pnl += (price - positions[0]) * direction * 0.01 * CONTRACT_SIZE
            
        current_equity = balance + floating_pnl
        if current_equity <= ACCOUNT_FLOOR:
            return [initial_balance] * (i) + [current_equity] # Bankrupt

        if not in_trade:
            # HF Entry: Volatility Spike
            # Look for a move > 2x standard deviation of last 10 bars
            lookback = df['close'].iloc[i-10:i]
            std = lookback.std()
            if abs(price - lookback.mean()) > 2 * std:
                in_trade = True
                direction = 1 if price > lookback.mean() else -1
                positions.append(price)
                trailing_stop = price - (direction * TRAIL_STOP_PIPS)
        else:
            # THE RAZOR CULLING
            if (direction == 1 and price <= trailing_stop) or \
               (direction == -1 and price >= trailing_stop):
                balance += floating_pnl
                positions = []
                in_trade = False
                direction = 0
                trailing_stop = None
                continue
            
            # Update trailing stop strictly
            if direction == 1:
                trailing_stop = max(trailing_stop, price - TRAIL_STOP_PIPS)
            else:
                trailing_stop = min(trailing_stop, price + TRAIL_STOP_PIPS)

            # FLASH BREEDING
            if len(positions) < MAX_HERD_SIZE:
                last_entry = positions[-1]
                if (direction == 1 and price >= last_entry + BREED_GAP) or \
                   (direction == -1 and price <= last_entry - BREED_GAP):
                    if floating_pnl > 0: # Only breed in profit
                        positions.append(price)

        equity.append(current_equity)
        
    return equity

df = generate_hf_gold_data()
equity_curve = backtest_hf_feral_hog(df)

plt.figure(figsize=(12,6))
plt.plot(equity_curve, label='HF Feral Hog', color='blue')
plt.axhline(y=100, color='r', linestyle='--', label='Starting Balance')
plt.title('Feral Hog HIGH FREQUENCY - XAUUSD Micro-Scalp Simulation')
plt.xlabel('Minutes')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('feral_hog_hf.png')

print(f"Final Balance: ${equity_curve[-1]:.2f}")
print(f"Max Drawdown: ${max(equity_curve) - min(equity_curve):.2f}")
print(f"Success: {'Yes' if equity_curve[-1] > 100 else 'No'}")
