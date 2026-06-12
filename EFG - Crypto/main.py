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

def print_status_table(table_data, portfolio, title="STATUS DO MERCADO"):
    """Função centralizada para imprimir a tabela de ativos e o resumo."""
    if not table_data:
        print(f"\n--- {title}: NENHUM ATIVO PARA EXIBIR ---")
        return

    print("\n" + "="*110)
    print(f" {title} ")
    print("="*110)
    header = f"{'RANK (%)':<10} | {'TICKER':<12} | {'REGIME':<8} | {'DIR':<6} | {'AÇÃO':<12} | {'LEV':<6} | {'VALOR (USDT)':<15} | {'IDADE':<10}"
    print(header)
    print("-" * 110)

    for row in table_data:
        print(f"{row['rank']:<10} | {row['ticker']:<12} | {row['regime']:<8} | {row['dir']:<6} | {row['acao']:<12} | {row['lev']:<6} | {row['qty']:<15} | {row['idade']:<10}")

    print("-" * 110)
    print(f"RESUMO: Saldo US${portfolio.balance:.2f} | Margem Ocupada: US${portfolio.get_current_total_margin():.2f} / US${portfolio.balance * 0.25:.2f} (25%)")
    print(f"ALAVANCAGEM TOTAL CARTEIRA: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*110 + "\n")

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

    initial_table = []
    print(f"\nAnalisando {len(symbols)} ativos. Aguarde...")

    virtual_margin_pool = portfolio.get_current_total_margin()

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
            strength = last['p_bull'] if last['regime'] == 0 else last['p_bear']
            side = "LONG" if last['regime'] == 0 else "SHORT" if last['regime'] == 1 else "NONE"
            regime_str = {0: "BULL", 1: "BEAR", 2: "COMP", 3: "EXH"}.get(last['regime'], "???")

            # --- CASO 1: POSIÇÃO JÁ ATIVA (Sempre mostrar) ---
            if active_pos:
                if decision.get('exit_total'): acao, grupo = "FECHAR", 2
                elif decision.get('exit_50_flat'): acao, grupo = "REDUZIR 50%", 2
                elif decision.get('exit_30_stretch'): acao, grupo = "REDUZIR 30%", 2
                else: acao, grupo = "MANTER", 1

                initial_table.append({
                    'rank': f"{active_pos.get('markov_strength', 0)*100:4.1f}%",
                    'ticker': symbol, 'regime': regime_str, 'dir': active_pos['side'], 'acao': acao,
                    'lev': f"{int(active_pos['leverage'])}x", 'qty': f"{active_pos['notional_usdt']:.1f} USDT",
                    'idade': f"{active_pos.get('bars_held', 0)} cnd", 'grupo': grupo, 'strength': 1.1, 'price': last['close']
                })

            # --- CASO 2: NOVA OPORTUNIDADE (Filtro Rígido) ---
            elif decision['signal_status'] != "EXPIRED" and side != "NONE":
                # REGRAS DO MANUAL:
                # 1. Markov Strength >= 40% (0.4)
                # 2. State != EXHAUSTION
                if strength >= 0.4 and last['dynamic_state'] != "EXHAUSTION":
                    lev = portfolio.calculate_suggested_leverage(strength)
                    margin_needed = portfolio.balance * portfolio.margin_per_asset_pct

                    # Checa se cabe na margem de 25%
                    if virtual_margin_pool + margin_needed <= (portfolio.balance * portfolio.max_total_margin_pct):
                        initial_table.append({
                            'rank': f"{strength*100:4.1f}%",
                            'ticker': symbol, 'regime': regime_str, 'dir': side, 'acao': "ENTRAR",
                            'lev': f"{lev}x", 'qty': f"{margin_needed * lev:.1f} USDT",
                            'idade': decision['signal_status'], 'grupo': 3, 'strength': strength, 'price': last['close']
                        })
                        virtual_margin_pool += margin_needed
        except Exception: continue

    # Ordenar por Grupo e Strength
    initial_table.sort(key=lambda x: (x['grupo'], -x['strength']))

    # Exibição da Tabela Filtrada
    print_status_table(initial_table, portfolio, "ACOMPANHAMENTO E OPORTUNIDADES FILTRADAS")

    if is_official:
        portfolio.increment_bars_held()
        print("--- ATUALIZAÇÃO DO PORTFOLIO ---")
        for row in initial_table:
            if row['acao'] == "ENTRAR":
                if portfolio.can_open_new():
                    if input(f"Confirmar entrada em {row['ticker']} ({row['dir']})? (s/n): ").lower() == 's':
                        portfolio.open_position(row['ticker'], row['dir'], row['price'], float(row['rank'].replace('%',''))/100, int(row['lev'].replace('x','')))
            elif row['acao'] in ["REDUZIR 50%", "REDUZIR 30%", "FECHAR"]:
                if input(f"Executou {row['acao']} em {row['ticker']}? (s/n): ").lower() == 's':
                    if row['acao'] == "FECHAR":
                        res = input("Lucro/Prejuízo (USD)?: ")
                        portfolio.update_balance(float(res))
                        portfolio.close_position(row['ticker'])
                    elif "50%" in row['acao']: portfolio.reduce_position(row['ticker'], 50)
                    elif "30%" in row['acao']: portfolio.reduce_position(row['ticker'], 30)

        # REPUBLICAR TABELA FINAL (SOMENTE ATIVOS EM CARTEIRA)
        print("\n✅ Portfolio atualizado.")
        portfolio = PortfolioManager()
        final_table = []
        for ticker, pos in portfolio.positions.items():
            final_table.append({
                'rank': f"{pos.get('markov_strength', 0)*100:4.1f}%",
                'ticker': ticker, 'regime': "---", 'dir': pos['side'], 'acao': "MANTER",
                'lev': f"{int(pos['leverage'])}x", 'qty': f"{pos['notional_usdt']:.1f} USDT",
                'idade': f"{pos.get('bars_held', 0)} cnd"
            })
        print_status_table(final_table, portfolio, "CARTEIRA ATUALIZADA (SITUAÇÃO ATUAL)")

if __name__ == "__main__":
    main()
