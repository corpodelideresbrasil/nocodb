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

def print_status_table(table_data, portfolio, title="STATUS DO MERCADO", show_age=True):
    """Função centralizada para imprimir a tabela de ativos e o resumo."""
    if not table_data:
        print(f"\n--- {title}: NENHUM ATIVO PARA EXIBIR ---")
        return

    print("\n" + "="*135)
    print(f" {title} ")
    print("="*135)

    col_width = 135 if show_age else 123
    header = f"{'RANK (%)':<10} | {'TICKER':<12} | {'REGIME':<8} | {'DIR':<6} | {'AÇÃO':<14} | {'STOP LOSS':<12} | {'LEV':<4} | {'VALOR (USDT)':<15}"
    if show_age: header += f" | {'IDADE':<10}"

    print(header)
    print("-" * col_width)

    for row in table_data:
        line = f"{row['rank']:<10} | {row['ticker']:<12} | {row['regime']:<8} | {row['dir']:<6} | {row['acao']:<14} | {row['stop']:<12} | {row['lev']:<4} | {row['qty']:<15}"
        if show_age: line += f" | {row['idade']:<10}"
        print(line)

    print("-" * col_width)
    print(f"RESUMO: Saldo US${portfolio.balance:.2f} | Margem Ocupada: US${portfolio.get_current_total_margin():.2f} / US${portfolio.balance * 0.25:.2f} (25%)")
    print(f"ALAVANCAGEM TOTAL CARTEIRA: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*135 + "\n")

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

    processed_data = [] # Para armazenar os dados brutos de todos os ativos analisados
    print(f"\nAnalisando {len(symbols)} ativos. Aguarde...")

    virtual_margin_pool = portfolio.get_current_total_margin()

    for symbol in symbols:
        try:
            df = provider.fetch_ohlcv(symbol, limit=100)
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

            stop_val = decision.get('trail_stop')
            stop_str = f"{stop_val:.4f}" if stop_val and not np.isnan(stop_val) else "---"

            if active_pos:
                if decision.get('exit_total'): acao, grupo = "FECHAR", 2
                elif decision.get('exit_50_flat'): acao, grupo = "REDUZIR 50%", 2
                elif decision.get('exit_30_stretch'): acao, grupo = "REDUZIR 30%", 2
                else: acao, grupo = "MANTER", 1

                # SUPRESSÃO DE REDUÇÕES REPETIDAS NO MESMO RASTRO
                if acao.startswith("REDUZIR") and active_pos.get('last_reduction_trail') == decision.get('trail_stop'):
                    acao = "MANTER"
                    grupo = 1

                processed_data.append({
                    'rank': f"{active_pos.get('markov_strength', 0)*100:4.1f}%",
                    'ticker': symbol, 'regime': regime_str, 'dir': active_pos['side'], 'acao': acao,
                    'stop': stop_str, 'lev': f"{int(active_pos['leverage'])}x",
                    'qty': f"{active_pos['notional_usdt']:.1f} USDT", 'idade': f"{active_pos.get('bars_held', 0)} cnd",
                    'grupo': grupo, 'strength': 1.1, 'price': last['close'],
                    'trail_stop_raw': decision.get('trail_stop')
                })
            elif decision['ignition_long'] or decision['ignition_short']:
                # CRITÉRIO DE ENTRADA TEÓRICO:
                # 1. Força de Markov >= 35% (vencendo a probabilidade neutra de 25%)
                # 2. Estado Dinâmico == EXPANSION (alinhamento de momento)
                if strength >= 0.35 and last['dynamic_state'] == "EXPANSION":
                    lev = portfolio.calculate_suggested_leverage(strength)
                    margin_needed = portfolio.balance * portfolio.margin_per_asset_pct

                    if virtual_margin_pool + margin_needed <= (portfolio.balance * portfolio.max_total_margin_pct):
                        processed_data.append({
                            'rank': f"{strength*100:4.1f}%",
                            'ticker': symbol, 'regime': regime_str, 'dir': side, 'acao': "ENTRAR",
                            'stop': stop_str, 'lev': f"{lev}x", 'qty': f"{margin_needed * lev:.1f} USDT",
                            'idade': "FRESH", 'grupo': 3, 'strength': strength, 'price': last['close']
                        })
                        virtual_margin_pool += margin_needed
        except Exception: continue

    processed_data.sort(key=lambda x: (x['grupo'], -x['strength']))
    print_status_table(processed_data, portfolio, "ACOMPANHAMENTO E OPORTUNIDADES")

    if is_official:
        portfolio.increment_bars_held()
        print("--- ATUALIZAÇÃO DO PORTFOLIO ---")
        for row in processed_data:
            if row['acao'] == "ENTRAR":
                if portfolio.can_open_new():
                    if input(f"Confirmar entrada em {row['ticker']}? (s/n): ").lower() == 's':
                        portfolio.open_position(row['ticker'], row['dir'], row['price'], float(row['rank'].replace('%',''))/100, int(row['lev'].replace('x','')))

            elif row['acao'] in ["REDUZIR 50%", "REDUZIR 30%", "FECHAR"]:
                if input(f"Executou {row['acao']} em {row['ticker']}? (s/n): ").lower() == 's':
                    res_str = input("Lucro/Prejuízo Realizado (USD) (digite 0 se não houve saída financeira)?: ").replace(',', '.')
                    portfolio.update_balance(float(res_str))
                    if row['acao'] == "FECHAR":
                        portfolio.close_position(row['ticker'])
                    elif "50%" in row['acao']: portfolio.reduce_position(row['ticker'], 50, trail_price=row.get('trail_stop_raw'))
                    elif "30%" in row['acao']: portfolio.reduce_position(row['ticker'], 30, trail_price=row.get('trail_stop_raw'))
                    portfolio = PortfolioManager() # Sincroniza estado

        # REPUBLICAR COM DADOS ATUALIZADOS REAIS
        print("\n✅ Portfolio atualizado.")
        portfolio = PortfolioManager() # Recarrega estado final
        final_list = []
        # Re-filtramos as posições atuais para a tabela final
        for row in processed_data:
            pos = portfolio.positions.get(row['ticker'])
            if pos:
                row['acao'] = "MANTER"
                row['qty'] = f"{pos['notional_usdt']:.1f} USDT"
                row['idade'] = f"{pos['bars_held']} cnd"
                # Garantimos que regime e stop estejam presentes
                final_list.append(row)
        print_status_table(final_list, portfolio, "CARTEIRA ATUALIZADA (SITUAÇÃO ATUAL)", show_age=False)

if __name__ == "__main__":
    main()
