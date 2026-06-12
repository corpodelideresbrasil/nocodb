import os
import numpy as np
from core.data_provider import DataProvider
from core.calculator import MPRMCalculator
from core.engine import MPRMEngine
from core.portfolio import PortfolioManager

def load_assets(filepath):
    if not os.path.exists(filepath): return []
    symbols = []
    with open(filepath, 'r') as f:
        for line in f:
            clean = line.strip().replace(',', '').replace("'", "").replace('"', '')
            if clean and not clean.startswith('#'): symbols.append(clean)
    return symbols

def monitor_market():
    symbols = load_assets("assets.txt")
    provider = DataProvider()
    calc = MPRMCalculator()
    portfolio = PortfolioManager(balance=200.0)

    opportunities = []

    print(f"\n--- MPRM V14.1 Futures Monitor | Saldo: ${portfolio.balance} ---")
    # Agora garantimos que o método existe e a chamada é segura
    print(f"Alavancagem Atual: {portfolio.get_current_leverage():.1f}X / 5.0X")
    print("-" * 50)

    for symbol in symbols:
        try:
            df = provider.fetch_ohlcv(symbol)
            if df is None or df.empty: continue

            df = calc.calculate_physics(df)
            df = calc.calculate_markov(df)
            df = calc.identify_regime(df)

            active_pos = portfolio.positions.get(symbol)
            engine = MPRMEngine(sl_mult=1.5, active_position=active_pos)
            decision = engine.process_signals(df)

            last = df.iloc[-1]

            if active_pos:
                # Tratamento para Trail Stop que pode ser None
                stop_val = decision.get('trail_stop')
                stop_str = f"{stop_val:.4f}" if stop_val and not np.isnan(stop_val) else "N/A"

                print(f"[ATIVA] {symbol:10} | Lado: {active_pos['side']:5} | Stop: {stop_str}")
                if decision.get('exit_total'):
                    print(f"   >>> ❌ SAÍDA TOTAL RECOMENDADA")
                elif decision.get('exit_50_flat'):
                    print(f"   >>> ⚠️ REDUZIR 50% (Trail Flat)")
                elif decision.get('exit_30_stretch'):
                    print(f"   >>> 🚀 REDUZIR 30% (Preço Esticado)")
            else:
                if decision['signal_status'] != "EXPIRED":
                    strength = last['p_bull'] if last['regime'] == 0 else last['p_bear']
                    side = "LONG" if last['regime'] == 0 else "SHORT"
                    opportunities.append({
                        'symbol': symbol, 'side': side, 'strength': strength,
                        'status': decision['signal_status'], 'age': decision['regime_age']
                    })
        except Exception as e:
            print(f"Erro em {symbol}: {e}")

    if opportunities:
        print("\n" + "="*50)
        print("RANKING DE OPORTUNIDADES (TOP MARKOV STRENGTH)")
        print("="*50)
        opportunities.sort(key=lambda x: x['strength'], reverse=True)
        for op in opportunities:
            status_exec = "✅ DISPONÍVEL" if portfolio.can_open_new() else "❌ LIMITE ATINGIDO"
            margin = portfolio.balance * portfolio.margin_per_asset_pct
            print(f"[{op['strength']*100:4.1f}%] {op['symbol']:10} | {op['side']:5} | {op['status']} ({op['age']} candles)")
            print(f"       Ação: {status_exec} | Margem Sugerida: ${margin:.2f}")
            print("-" * 50)

if __name__ == "__main__":
    monitor_market()
