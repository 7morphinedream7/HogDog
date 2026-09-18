import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_gold_data(days=100, interval='15min'):
    """
    Generates synthetic XAUUSD data to simulate 'The Den' (consolidation) 
    and 'The Run' (explosive momentum).
    """
    np.random.seed(42)
    periods = days * 24 * (60 // 15)
    
    # Start price for Gold
    price = 2500.0
    prices = []
    
    # Create segments of volatility
    # 0: Consolidation (The Den)
    # 1: Explosive Trend (The Run)
    # 2: Random Walk
    segments = np.random.choice([0, 1, 2], size=periods, p=[0.6, 0.1, 0.3])
    
    for seg in segments:
        if seg == 0: # The Den: Low volatility
            price += np.random.normal(0, 0.5)
        elif seg == 1: # The Run: High momentum
            direction = np.random.choice([1, -1])
            price += direction * np.random.normal(2.0, 0.5)
        else: # Random walk
            price += np.random.normal(0, 1.5)
        prices.append(price)
        
    df = pd.DataFrame({'close': prices})
    df['high'] = df['close'] + np.random.uniform(0, 1, len(df))
    df['low'] = df['close'] - np.random.uniform(0, 1, len(df))
    df['open'] = df['close'].shift(1).fillna(df['close'])
    return df

def backtest_feral_hog(df, initial_balance=100):
    # Strategy Parameters
    PIP_VALUE = 0.1 # Gold: 0.1 point = 1 pip approx for simplicity
    BREED_THRESHOLD = 3.0 # 30 pips in price points
    MAX_HERD_SIZE = 5
    LOT_SIZE = 0.01
    CONTRACT_SIZE = 100 # 1 lot = 100oz
    
    # Indicators
    df['atr'] = df['high'].rolling(20).max() - df['low'].rolling(20).min()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    
    balance = initial_balance
    equity = []
    positions = [] # List of entry prices
    in_trade = False
    
    for i in range(20, len(df)):
        price = df['close'].iloc[i]
        ema = df['ema20'].iloc[i]
        atr = df['atr'].iloc[i]
        
        if not in_trade:
            # THE DEN DETECTION
            # Check if last 20 bars range is < 1.5 * ATR (oversimplified for synthetic)
            range_20 = df['high'].iloc[i-20:i].max() - df['low'].iloc[i-20:i].min()
            if range_20 < 3.0 * atr: # We are in the den
                # TRIGGER: Breakout with momentum
                if price > df['high'].iloc[i-1] + 0.5:
                    # Enter Scout
                    in_trade = True
                    positions.append(price)
                    # Risk is simplified: Stop loss at bottom of den
                    stop_loss = df['low'].iloc[i-20:i].min()
        
        else:
            # TRAILING STOP / CULLING
            # Liquidate if price closes below EMA20
            if price < ema:
                # Close all
                for entry in positions:
                    profit = (price - entry) * LOT_SIZE * CONTRACT_SIZE
                    balance += profit
                positions = []
                in_trade = False
                continue

            # PROLIFERATION (BREEDING)
            # If we have room in the herd and the most recent position is in profit
            if len(positions) < MAX_HERD_SIZE:
                last_entry = positions[-1]
                if price >= last_entry + BREED_THRESHOLD:
                    positions.append(price)
        
        # Calculate floating equity
        current_floating = 0
        if in_trade:
            for entry in positions:
                current_floating += (price - entry) * LOT_SIZE * CONTRACT_SIZE
        
        equity.append(balance + current_floating)
        
    return equity

# Run Simulation
df = generate_synthetic_gold_data()
equity_curve = backtest_feral_hog(df)

plt.figure(figsize=(12,6))
plt.plot(equity_curve, label='Account Balance')
plt.axhline(y=100, color='r', linestyle='--', label='Starting Balance')
plt.title('Feral Hog Strategy - XAUUSD Synthetic Simulation')
plt.xlabel('Ticks')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('feral_hog_results.png')

print(f"Final Balance: ${equity_curve[-1]:.2f}")
print(f"Max Drawdown: ${max(equity_curve) - min(equity_curve):.2f}")
