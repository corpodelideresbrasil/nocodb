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

def main():
    print("\n" + "="*35)
    print("      EFG - CRYPTO MONITOR V14.1      ")
    print("="*35)
    print("1. Rodada Oficial (Atualiza Portfolio)")
    print("2. Acompanhamento (Leitura Apenas)")
    escolha = input("\nSelecione o modo (1/2): ")

    is_official = (escolha == '1')
    portfolio = PortfolioManager()
    symbols = load_assets("assets.txt")
    provider = DataProvider()
    calc = MPRMCalculator()

    table_data = []

    print(f"\nAnalisando {len(symbols)} ativos. Aguarde...")

    # Variável para rastrear margem "em uso" virtualmente durante o processamento do ranking
    virtual_margin_used = portfolio.get_current_total_margin()

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

            regime_names = {0: "BULL", 1: "BEAR", 2: "COMP", 3: "EXH"}
            regime_str = regime_names.get(last['regime'], "???")

            if active_pos:
                if decision.get('exit_total'): acao, grupo = "FECHAR", 2
                elif decision.get('exit_50_flat'): acao, grupo = "REDUZIR 50%", 2
                elif decision.get('exit_30_stretch'): acao, grupo = "REDUZIR 30%", 2
                else: acao, grupo = "MANTER", 1

                table_data.append({
                    'rank': f"{active_pos.get('markov_strength', 0)*100:4.1f}%",
                    'ticker': symbol, 'regime': regime_str, 'dir': active_pos['side'], 'acao': acao,
                    'lev': f"{int(active_pos['leverage'])}x", 'qty': f"{active_pos['notional_usdt']:.1f} USDT",
                    'idade': f"{decision['regime_age']} cnd", 'grupo': grupo, 'strength': 1.1, 'price': price
                })
            elif decision['signal_status'] != "EXPIRED" and side != "NONE":
                table_data.append({
                    'rank': f"{strength*100:4.1f}%",
                    'ticker': symbol, 'regime': regime_str, 'dir': side, 'acao': "ENTRAR",
                    'idade': decision['signal_status'], 'grupo': 3, 'strength': strength, 'price': price
                })
        except Exception:
            continue

    # Ordenar por Grupo e depois por Strength
    table_data.sort(key=lambda x: (x['grupo'], -x['strength']))

    # EXIBIÇÃO DA TABELA
    print("\n" + "="*110)
    header = f"{'RANK (%)':<10} | {'TICKER':<12} | {'REGIME':<8} | {'DIR':<6} | {'AÇÃO':<12} | {'LEV':<6} | {'VALOR (USDT)':<15} | {'IDADE':<10}"
    print(header)
    print("-" * 110)

    for row in table_data:
        if row['acao'] == "ENTRAR":
            lev = portfolio.calculate_suggested_leverage(row['strength'])
            margin = portfolio.balance * portfolio.margin_per_asset_pct

            # Checa se ainda há margem
            if virtual_margin_used + margin <= (portfolio.balance * portfolio.max_total_margin_pct):
                notional = margin * lev
                row['lev'] = f"{lev}x"
                row['qty'] = f"{notional:.1f} USDT"
                virtual_margin_used += margin
            else:
                row['acao'] = "LIMITE OFF"
                row['lev'] = "---"
                row['qty'] = "---"

        print(f"{row['rank']:<10} | {row['ticker']:<12} | {row['regime']:<8} | {row['dir']:<6} | {row['acao']:<12} | {row['lev']:<6} | {row['qty']:<15} | {row['idade']:<10}")

    print("-" * 110)
    print(f"RESUMO: Saldo: US${portfolio.balance:.2f} | Margem Ocupada: US${portfolio.get_current_total_margin():.2f} / US${portfolio.balance * 0.2:.2f} (20%)")
    print(f"ALAVANCAGEM TOTAL CARTEIRA: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*110 + "\n")

    if is_official:
        print("--- ATUALIZAÇÃO DO PORTFOLIO ---")
        for row in table_data:
            if row['acao'] == "ENTRAR":
                conf = input(f"Confirmar entrada em {row['ticker']} ({row['dir']})? (s/n): ")
                if conf.lower() == 's':
                    s = float(row['rank'].replace('%', ''))/100
                    l = int(row['lev'].replace('x', ''))
                    portfolio.open_position(row['ticker'], row['dir'], row['price'], s, l)

            elif row['acao'] in ["REDUZIR 50%", "REDUZIR 30%", "FECHAR"]:
                conf = input(f"Executou {row['acao']} em {row['ticker']}? (s/n): ")
                if conf.lower() == 's':
                    if row['acao'] == "FECHAR":
                        res = input("Qual foi o Lucro/Prejuízo (USD)? (ex: 5.50 ou -2.10): ")
                        portfolio.update_balance(float(res))
                        portfolio.close_position(row['ticker'])
                    elif "50%" in row['acao']: portfolio.reduce_position(row['ticker'], 50)
                    elif "30%" in row['acao']: portfolio.reduce_position(row['ticker'], 30)
        print("\n✅ Portfolio atualizado.")

if __name__ == "__main__":
    main()
