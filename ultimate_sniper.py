import pandas as pd
import numpy as np

def generate_sniper_gold_data(days=365, interval='1h'):
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

def run_ultimate_sim(df, initial_balance=100):
    # --- GOLDEN PARAMETERS (From Grid Search) ---
    VOL_MULT = 3.0
    STOP_DIST = 1.0
    RR_RATIO = 24
    
    # --- SYSTEM CONSTANTS ---
    CONTRACT_SIZE = 100
    SPREAD = 0.15
    COMMISSION = 0.7
    
    close_vals = df['close'].values
    balance = initial_balance
    ath_balance = initial_balance
    
    in_trade = False
    direction = 0
    entry_price = None
    stop_loss = None
    trade_lot = 0.01
    trades_this_week = 0
    tick_count = 0
    trail_activated = False

    for i in range(24, len(close_vals)):
        tick_count += 1
        if tick_count % 168 == 0: trades_this_week = 0
        price = close_vals[i]
        
        # Update ATH for Circuit Breaker
        ath_balance = max(ath_balance, balance)
        
        if not in_trade:
            lookback = close_vals[i-24:i]
            mean = np.mean(lookback)
            vol = np.std(lookback)
            
            if abs(price - mean) > VOL_MULT * vol and trades_this_week < 1:
                in_trade = True
                direction = 1 if price > mean else -1
                entry_price = price + (SPREAD / 2 if direction == 1 else -SPREAD / 2)
                stop_loss = entry_price - (direction * STOP_DIST)
                
                # --- INFINITE LOGARITHMIC SCALING ENGINE ---
                # Base scale: 0.01 per $50, then decelerating to preserve wealth
                # Formula: log10(balance/100) provides a growth curve that never flatlines but prevents over-leverage
                scale_factor = np.log10(balance / 100 + 1) + 1
                trade_lot = 0.01 * (balance / (50 * scale_factor))
                
                # --- ANTI-FRAGILE CIRCUIT BREAKER ---
                # If we are in a drawdown > 20% from ATH, slash risk by 50%
                if balance < ath_balance * 0.80:
                    trade_lot *= 0.5
                
                trade_lot = max(0.01, trade_lot)
                balance -= (COMMISSION * (trade_lot/0.01))
                trades_this_week += 1
                trail_activated = False
        else:
            exit_price = price - (SPREAD / 2 * direction)
            current_profit = (exit_price - entry_price) * direction
            
            # --- SYNTHESIS TRAILING SYSTEM ---
            # 1. Safety Switch: Move to BE at 1:3 RR
            if not trail_activated and current_profit >= STOP_DIST * 3:
                stop_loss = entry_price
                trail_activated = True
            
            # 2. Last-Mile Trail: Aggressive lock-in after 1:8 RR
            elif trail_activated and current_profit >= STOP_DIST * 8:
                # Lock in profit by trailing 1x risk behind current price
                new_stop = entry_price + (direction * (current_profit // STOP_DIST - 1) * STOP_DIST)
                if (direction == 1 and new_stop > stop_loss) or (direction == -1 and new_stop < stop_loss):
                    stop_loss = new_stop

            # --- EXIT CHECK ---
            if (direction == 1 and exit_price <= stop_loss) or (direction == -1 and exit_price >= stop_loss) or \
               abs(exit_price - entry_price) >= STOP_DIST * RR_RATIO:
                balance += (exit_price - entry_price) * direction * trade_lot * CONTRACT_SIZE
                in_trade = False
                direction = 0
                
        if balance <= 0: return 0.0
    return balance

if __name__ == "__main__":
    # Extending to 20 years to prove the infinite growth theory
    df = generate_sniper_gold_data(days=365 * 20)
    final_res = run_ultimate_sim(df)
    print("\n" + "="*40)
    print("🚀 ULTIMATE SNIPER: 20-YEAR STRESS TEST 🚀")
    print(f"Final Account Balance: ${final_res:,.2f}")
    print("="*40)
    input("\nPress Enter to exit...")
