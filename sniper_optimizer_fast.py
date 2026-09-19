import pandas as pd
import numpy as np

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

def run_sniper_sim(params, df):
    CONTRACT_SIZE = 100
    LOT_SIZE = 0.01
    SPREAD = 0.15
    COMMISSION = 0.7
    
    # Use numpy arrays for speed
    close_vals = df['close'].values
    balance = 100.0
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
            # Fast volatility check
            lookback = close_vals[i-24:i]
            mean = np.mean(lookback)
            vol = np.std(lookback)
            
            if abs(price - mean) > params['vol_mult'] * vol and trades_this_week < 1:
                in_trade = True
                direction = 1 if price > mean else -1
                entry_price = price + (SPREAD / 2 if direction == 1 else -SPREAD / 2)
                stop_loss = entry_price - (direction * params['stop_dist'])
                balance -= COMMISSION
                trades_this_week += 1
        else:
            exit_price = price - (SPREAD / 2 * direction)
            if (direction == 1 and exit_price <= stop_loss) or (direction == -1 and exit_price >= stop_loss):
                balance += (exit_price - entry_price) * direction * LOT_SIZE * CONTRACT_SIZE
                in_trade = False
                direction = 0
            elif abs(exit_price - entry_price) >= params['stop_dist'] * params['rr_ratio']:
                balance += (exit_price - entry_price) * direction * LOT_SIZE * CONTRACT_SIZE
                in_trade = False
                direction = 0
        
        if balance <= 0: return 0.0
        
    return balance

df = generate_sniper_gold_data()
vol_mults = [2.0, 2.5, 3.0, 3.5, 4.0]
stop_dists = [0.2, 0.3, 0.4, 0.5, 0.6]
rr_ratios = [5, 8, 10, 12, 15]

best_bal = -float('inf')
best_params = {}

for vm in vol_mults:
    for sd in stop_dists:
        for rr in rr_ratios:
            params = {'vol_mult': vm, 'stop_dist': sd, 'rr_ratio': rr}
            res = run_sniper_sim(params, df)
            if res > best_bal:
                best_bal = res
                best_params = params

print(f"Optimal Balance: ${best_bal:.2f}")
print(f"Best Parameters: {best_params}")
