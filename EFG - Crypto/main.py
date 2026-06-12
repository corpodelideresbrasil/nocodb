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

    table_data = [] # Lista consolidada para a tabela final

    print(f"\n--- MPRM V14.1 Futures Monitor | Saldo: ${portfolio.balance:.2f} ---")

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
            price = last['close']
            strength = last['p_bull'] if last['regime'] == 0 else last['p_bear']
            side = "LONG" if last['regime'] == 0 else "SHORT" if last['regime'] == 1 else "NONE"

            # --- MONITORAMENTO DE POSIÇÕES ATIVAS ---
            if active_pos:
                acao = "SAÍDA TOTAL" if decision.get('exit_total') else \
                       "REDUZIR 50%" if decision.get('exit_50_flat') else \
                       "REDUZIR 30%" if decision.get('exit_30_stretch') else "MANTER"

                table_data.append({
                    'ticker': symbol,
                    'direcao': active_pos['side'],
                    'acao': acao,
                    'alavancagem': f"{active_pos['leverage']:.1f}x",
                    'quantidade': f"{active_pos['quantity']:.4f}",
                    'idade': f"{decision['regime_age']} cnd",
                    'strength': 1.0 # Posições ativas ficam no topo do rank conceitualmente
                })

            # --- BUSCA DE NOVAS OPORTUNIDADES ---
            elif decision['signal_status'] != "EXPIRED" and side != "NONE":
                leverage = portfolio.calculate_suggested_leverage(strength)
                margin = portfolio.balance * portfolio.margin_per_asset_pct
                qty = (margin * leverage) / price

                # Só recomenda se não exceder os 20% de margem total
                if portfolio.get_current_total_margin() + margin <= (portfolio.balance * portfolio.max_total_margin_pct):
                    table_data.append({
                        'ticker': symbol,
                        'direcao': side,
                        'acao': "ENTRAR",
                        'alavancagem': f"{leverage:.1f}x",
                        'quantidade': f"{qty:.4f}",
                        'idade': decision['signal_status'],
                        'strength': strength
                    })

        except Exception as e:
            # Erros silenciosos para não quebrar a tabela, mas reportar se necessário
            pass

    # EXIBIÇÃO DA TABELA
    print("\n" + "="*85)
    header = f"{'RANK':<5} | {'TICKER':<12} | {'DIR':<6} | {'AÇÃO':<12} | {'LEVERAGE':<10} | {'QTY':<12} | {'IDADE':<10}"
    print(header)
    print("-" * 85)

    # Ordenar por Força Markov (strength)
    table_data.sort(key=lambda x: x['strength'], reverse=True)

    for i, row in enumerate(table_data, 1):
        print(f"{i:<5} | {row['ticker']:<12} | {row['direcao']:<6} | {row['acao']:<12} | {row['alavancagem']:<10} | {row['quantidade']:<12} | {row['idade']:<10}")

    # RESUMO DE MARGEM
    used_margin = portfolio.get_current_total_margin()
    max_margin = portfolio.balance * portfolio.max_total_margin_pct
    print("-" * 85)
    print(f"RESUMO DE MARGEM: US${used_margin:.2f} / US${max_margin:.2f} (Máx 20% do Saldo)")
    print(f"ALAVANCAGEM TOTAL CARTEIRA: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*85 + "\n")

if __name__ == "__main__":
    monitor_market()
