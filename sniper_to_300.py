import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_sniper_gold_data(days=180, interval='1h'):
    np.random.seed(42)
    periods = days * 24
    price = 2500.0
    prices = []
    for i in range(periods):
        if np.random.random() > 0.05:
            price += np.random.normal(0, 1.2)
        else:
            direction = np.random.choice([1, -1])
            magnitude = np.random.normal(15.0, 5.0)
            for _ in range(np.random.randint(3, 8)):
                price += direction * (magnitude / 5)
                prices.append(price)
            continue
        prices.append(price)
    df = pd.DataFrame({'close': prices})
    return df

def run_sniper_sim(params, df, initial_balance=100):
    CONTRACT_SIZE = 100
    SPREAD = 0.15
    COMMISSION = 0.7
    
    close_vals = df['close'].values
    balance = initial_balance
    in_trade = False
    direction = 0
    entry_price = None
    stop_loss = None
    
    trades_this_week = 0
    tick_count = 0
    
    for i in range(24, len(close_vals)):
        tick_count += 1
        if tick_count % 168 == 0:
            trades_this_week = 0
            
        price = close_vals[i]
        
        if not in_trade:
            lookback = close_vals[i-24:i]
            mean = np.mean(lookback)
            vol = np.std(lookback)
            
            if abs(price - mean) > params['vol_mult'] * vol and trades_this_week < 1:
                in_trade = True
                direction = 1 if price > mean else -1
                entry_price = price + (SPREAD / 2 if direction == 1 else -SPREAD / 2)
                stop_loss = entry_price - (direction * params['stop_dist'])
                
                # Dynamic Lot: Increase slightly as balance grows to hit $300 faster
                # Base 0.01, add 0.01 for every $100 profit
                lot = 0.01 + (max(0, int((balance - 100) // 100)) * 0.01)
                lot = min(lot, 0.05) # Cap to avoid ruin
                
                balance -= (COMMISSION * (lot/0.01))
                trades_this_week += 1
        else:
            exit_price = price - (SPREAD / 2 * direction)
            # Determine lot used for this trade
            lot = 0.01 + (max(0, int((balance - 100) // 100)) * 0.01) # Simplified for simulation
            lot = min(lot, 0.05)
            
            if (direction == 1 and exit_price <= stop_loss) or (direction == -1 and exit_price >= stop_loss):
                balance += (exit_price - entry_price) * direction * lot * CONTRACT_SIZE
                in_trade = False
                direction = 0
            elif abs(exit_price - entry_price) >= params['stop_dist'] * params['rr_ratio']:
                balance += (exit_price - entry_price) * direction * lot * CONTRACT_SIZE
                in_trade = False
                direction = 0
        
        if balance <= 0: return 0.0
        
    return balance

df = generate_sniper_gold_data()
# Using our previously discovered optimal parameters
params = {'vol_mult': 4.0, 'stop_dist': 0.6, 'rr_ratio': 15}
final_balance = run_sniper_sim(params, df)

print(f"Final Balance: ${final_balance:.2f}")
print(f"Goal $300 Reached: {'YES' if final_balance >= 300 else 'NO'}")
