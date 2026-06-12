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
    print("\n" + "="*30)
    print("   EFG - CRYPTO MONITOR   ")
    print("="*30)
    print("1. Rodada Oficial (Atualiza Portfolio)")
    print("2. Apenas Acompanhamento")
    escolha = input("\nSelecione o modo (1/2): ")

    is_official = (escolha == '1')
    symbols = load_assets("assets.txt")
    provider = DataProvider()
    calc = MPRMCalculator()
    portfolio = PortfolioManager()

    table_data = []

    print(f"\nProcessando {len(symbols)} ativos. Por favor, aguarde...")

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

            # Agrupamento: 1=Acompanhado, 2=Reduzido/Encerrado, 3=Nova Entrada
            if active_pos:
                if decision.get('exit_total'):
                    acao, grupo = "FECHAR", 2
                elif decision.get('exit_50_flat'):
                    acao, grupo = "REDUZIR 50%", 2
                elif decision.get('exit_30_stretch'):
                    acao, grupo = "REDUZIR 30%", 2
                else:
                    acao, grupo = "MANTER", 1

                table_data.append({
                    'rank': f"{active_pos.get('markov_strength', 0)*100:4.1f}%",
                    'ticker': symbol, 'dir': active_pos['side'], 'acao': acao,
                    'lev': f"{active_pos['leverage']}x", 'qty': f"{active_pos['notional_usdt']:.1f} USDT",
                    'idade': f"{decision['regime_age']} cnd", 'grupo': grupo, 'strength': 1.1 # Prioridade visual
                })
            elif decision['signal_status'] != "EXPIRED" and side != "NONE":
                leverage = portfolio.calculate_suggested_leverage(strength)
                margin = portfolio.balance * portfolio.margin_per_asset_pct
                notional = margin * leverage

                if portfolio.get_current_total_margin() + margin <= (portfolio.balance * portfolio.max_total_margin_pct):
                    table_data.append({
                        'rank': f"{strength*100:4.1f}%",
                        'ticker': symbol, 'dir': side, 'acao': "ENTRAR",
                        'lev': f"{leverage}x", 'qty': f"{notional:.1f} USDT",
                        'idade': decision['signal_status'], 'grupo': 3, 'strength': strength
                    })
        except Exception:
            continue

    # EXIBIÇÃO DA TABELA AGRUPADA
    print("\n" + "="*95)
    header = f"{'STRENGTH':<10} | {'TICKER':<12} | {'DIR':<6} | {'AÇÃO':<12} | {'LEV':<6} | {'VALOR (USDT)':<12} | {'IDADE':<10}"
    print(header)
    print("-" * 95)

    # Ordenar por Grupo e depois por Strength
    table_data.sort(key=lambda x: (x['grupo'], -x['strength']))

    for row in table_data:
        print(f"{row['rank']:<10} | {row['ticker']:<12} | {row['dir']:<6} | {row['acao']:<12} | {row['lev']:<6} | {row['qty']:<12} | {row['idade']:<10}")

    print("-" * 95)
    print(f"RESUMO: Margem US${portfolio.get_current_total_margin():.2f} (Máx $40) | Alavancagem Portfólio: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*95 + "\n")

    # INTERAÇÃO (APENAS MODO OFICIAL)
    if is_official:
        print("--- ATUALIZAÇÃO DO PORTFOLIO ---")
        for row in table_data:
            if row['acao'] == "ENTRAR":
                conf = input(f"Confirmar entrada em {row['ticker']} ({row['dir']})? (s/n): ")
                if conf.lower() == 's':
                    # Simplificação para o prompt
                    s = float(row['rank'].replace('%', ''))/100
                    l = int(row['lev'].replace('x', ''))
                    # Precisamos do preço atual, buscar de novo ou guardar no table_data
                    portfolio.open_position(row['ticker'], row['dir'], 0, s, l) # Preço 0 p/ simplificar registro

            elif row['acao'] in ["REDUZIR 50%", "REDUZIR 30%", "FECHAR"]:
                conf = input(f"Executou {row['acao']} em {row['ticker']}? (s/n): ")
                if conf.lower() == 's':
                    if row['acao'] == "FECHAR":
                        res = input("Qual foi o Lucro/Prejuízo (USD)? (ex: 5.50 ou -2.10): ")
                        portfolio.update_balance(float(res))
                        portfolio.close_position(row['ticker'])
                    elif "50%" in row['acao']: portfolio.reduce_position(row['ticker'], 50)
                    elif "30%" in row['acao']: portfolio.reduce_position(row['ticker'], 30)

        print("\n✅ Portfolio atualizado e salvo em portfolio.json.")

if __name__ == "__main__":
    main()
