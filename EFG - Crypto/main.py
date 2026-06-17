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
    """Função centralizada para imprimir a tabela de ativos e o resumo com coluna de MOTIVO e SYNC."""
    if not table_data:
        print(f"\n--- {title}: NENHUM ATIVO PARA EXIBIR ---")
        return

    # Ajuste para restaurar visibilidade de Regime e Sync conforme pedido do usuário
    col_width = 185
    print("\n" + "="*col_width)
    print(f" {title} ")
    print("="*col_width)

    header = f"{'RANK (%)':<10} | {'CONV. (%)':<10} | {'TICKER':<12} | {'REGIME (1D)':<11} | {'SYNC (4h)':<10} | {'DIR':<6} | {'AÇÃO':<16} | {'MOTIVO':<22} | {'STOP LOSS':<12} | {'LEV':<6} | {'PNL (%)':<10} | {'VALOR (USDT)':<15}"

    print(header)
    print("-" * col_width)

    for row in table_data:
        acao = row.get('acao', '---')
        motivo = row.get('motivo', '---')
        pnl_str = row.get('pnl', '---')
        conv_str = row.get('conv', '---')
        line = f"{row['rank']:<10} | {conv_str:<10} | {row['ticker']:<12} | {row['regime']:<11} | {row['sync']:<10} | {row['dir']:<6} | {acao:<16} | {motivo:<22} | {row['stop']:<12} | {row.get('lev', '---'):<6} | {pnl_str:<10} | {row['qty']:<15}"
        print(line)

    print("-" * col_width)
    print(f"RESUMO: Saldo US${portfolio.balance:.2f} | Margem Ocupada: US${portfolio.get_current_total_margin():.2f} / US${portfolio.balance * 0.25:.2f} (25%)")
    print(f"ALAVANCAGEM TOTAL CARTEIRA: {portfolio.get_current_total_leverage():.2f}X / 5.0X")
    print("="*col_width + "\n")

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
            # 1. TIMEFRAME PRINCIPAL (1 DIARIO)
            df_1d = provider.fetch_ohlcv(symbol, timeframe='1d', limit=100)
            if df_1d is None or df_1d.empty: continue

            df_1d = calc.calculate_physics(df_1d)
            df_1d = calc.calculate_markov(df_1d)
            df_1d = calc.identify_regime(df_1d)

            # 2. TIMEFRAME DE AJUSTE/PULLBACK (4 HORAS)
            df_4h = provider.fetch_ohlcv(symbol, timeframe='4h', limit=100)
            sync_str = "???"
            if df_4h is not None and not df_4h.empty:
                df_4h = calc.calculate_physics(df_4h)
                df_4h = calc.calculate_markov(df_4h)
                df_4h = calc.identify_regime(df_4h)
                last_4h = df_4h.iloc[-1]
                sync_str = {0: "BULL", 1: "BEAR", 2: "COMP", 3: "EXH"}.get(last_4h['regime'], "???")

            active_pos = portfolio.positions.get(symbol)
            engine = MPRMEngine(sl_mult=1.5, active_position=active_pos)
            decision = engine.process_signals(df_1d)

            last = df_1d.iloc[-1]
            strength = last['p_bull'] if last['regime'] == 0 else last['p_bear']
            side = "LONG" if last['regime'] == 0 else "SHORT" if last['regime'] == 1 else "NONE"
            regime_str = {0: "BULL", 1: "BEAR", 2: "COMP", 3: "EXH"}.get(last['regime'], "???")

            # Verificação de Alinhamento (Sync) - Requer alinhamento de regime E força instantânea
            is_synced = False
            if df_4h is not None and not df_4h.empty:
                last_4h = df_4h.iloc[-1]
                if last['regime'] == 0: # BULL
                    is_synced = (last_4h['regime'] == 0 and last_4h['p_bull_i'] >= last_4h['p_bear_i'])
                elif last['regime'] == 1: # BEAR
                    is_synced = (last_4h['regime'] == 1 and last_4h['p_bear_i'] >= last_4h['p_bull_i'])

            stop_val = decision.get('trail_stop')
            stop_str = f"{stop_val:.4f}" if stop_val and not np.isnan(stop_val) else "---"

            if active_pos:
                motivo = "OK"
                if decision.get('exit_total'):
                    acao, grupo, motivo = "FECHAR TOTAL", 2, "REGIME/STOP"
                elif decision.get('exit_50_flat'):
                    acao, grupo, motivo = "REDUZIR 50%", 2, "TRAIL FLAT (3x)"
                elif decision.get('exit_30_stretch'):
                    acao, grupo, motivo = "REDUZIR 30%", 2, "PREÇO ESTICADO"
                else:
                    acao, grupo = "MANTER", 1

                # Lógica de Supressão Visual e Funcional
                current_trail = decision.get('trail_stop')
                last_reduction = active_pos.get('last_reduction_trail')

                # Tolerância para flutuações mínimas de float
                is_already_reduced = False
                if last_reduction and current_trail:
                    if abs(last_reduction - current_trail) < (last['close'] * 0.0001):
                        is_already_reduced = True

                if acao != "FECHAR TOTAL" and acao.startswith("REDUZIR") and is_already_reduced:
                    motivo = f"REDUÇÃO JÁ FEITA ({acao.split()[-1]})"
                    acao = "MANTER"
                    grupo = 1

                # Cálculo do valor investido alvo (após a ação sugerida)
                target_qty = active_pos['notional_usdt']
                if acao == "FECHAR TOTAL":
                    target_qty = 0.0
                elif "50%" in acao:
                    target_qty *= 0.5
                elif "30%" in acao:
                    target_qty *= 0.7

                # Cálculo de PnL Momentâneo
                entry_price = active_pos.get('entry_price', last['close'])
                current_price = last['close']
                side_mult = 1 if active_pos['side'] == 'LONG' else -1
                raw_pnl = ((current_price / entry_price) - 1) * side_mult
                pnl_pct = raw_pnl * 100

                processed_data.append({
                    'rank': f"{active_pos.get('markov_strength', 0)*100:4.1f}%",
                    'conv': f"{decision.get('conviction', 0)*100:4.1f}%",
                    'ticker': symbol, 'regime': regime_str, 'sync': sync_str, 'dir': active_pos['side'], 'acao': acao,
                    'motivo': motivo,
                    'stop': stop_str, 'lev': f"{int(active_pos['leverage'])}x",
                    'pnl': f"{pnl_pct:+.2f}%",
                    'qty': f"{target_qty:.1f} USDT", 'idade': f"{active_pos.get('bars_held', 0)} cnd",
                    'grupo': grupo, 'strength': 1.1, 'price': last['close'],
                    'trail_stop_raw': current_trail
                })
            elif decision['ignition_long'] or decision['ignition_short']:
                # CRITÉRIO DE ENTRADA TEÓRICO (V14.1 + MTF SYNC):
                # 1. Força de Markov >= 35%
                # 2. Estado Dinâmico == EXPANSION
                # 3. Alinhamento 1D/4H (Sync) para evitar pullback adverso
                if strength >= 0.35 and last['dynamic_state'] == "EXPANSION":
                    acao, grupo, motivo = "ENTRAR", 3, "MARKOV >= 35%"

                    if not is_synced:
                        acao, grupo, motivo = "ESPERAR 4H", 4, "PULLBACK (SEM SYNC)"

                    lev = portfolio.calculate_suggested_leverage(strength)
                    margin_needed = portfolio.balance * portfolio.margin_per_asset_pct

                    if virtual_margin_pool + margin_needed <= (portfolio.balance * portfolio.max_total_margin_pct):
                        processed_data.append({
                            'rank': f"{strength*100:4.1f}%",
                            'conv': f"{decision.get('conviction', 0)*100:4.1f}%",
                            'ticker': symbol, 'regime': regime_str, 'sync': sync_str, 'dir': side, 'acao': acao,
                            'motivo': motivo,
                            'stop': stop_str, 'lev': f"{lev}x", 'qty': f"{margin_needed * lev:.1f} USDT",
                            'idade': "FRESH", 'grupo': grupo, 'strength': strength, 'price': last['close']
                        })
                        if acao == "ENTRAR": virtual_margin_pool += margin_needed
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
                        exec_price = input(f"Preço de Execução para {row['ticker']} (USDT) [Sugestão {row['price']:.4f}]: ")
                        try:
                            final_price = float(exec_price.replace(',', '.'))
                        except:
                            final_price = row['price']
                        portfolio.open_position(row['ticker'], row['dir'], final_price, float(row['rank'].replace('%',''))/100, int(row['lev'].replace('x','')))

            elif row['acao'] in ["REDUZIR 50%", "REDUZIR 30%", "FECHAR TOTAL"]:
                if input(f"Executou {row['acao']} em {row['ticker']}? (s/n): ").lower() == 's':
                    res_str = input("Lucro/Prejuízo Realizado (USD) (digite 0 se não houve saída financeira)?: ").replace(',', '.')
                    portfolio.update_balance(float(res_str))
                    if row['acao'] == "FECHAR TOTAL":
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
        print_status_table(final_list, portfolio, "CARTEIRA ATUALIZADA (SITUAÇÃO ATUAL)")

if __name__ == "__main__":
    main()
