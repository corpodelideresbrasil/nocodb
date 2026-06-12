import os
import numpy as np
from core.data_provider import DataProvider
from core.calculator import MPRMCalculator
from core.engine import MPRMEngine

def load_assets(filepath):
    """Lê a lista de ativos de um arquivo txt."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    # Remove comentários e linhas vazias
    return [line.strip() for line in lines if line.strip() and not line.startswith('#')]

def monitor_market():
    assets_file = "assets.txt"
    symbols = load_assets(assets_file)

    if not symbols:
        print(f"Nenhum ativo encontrado em {assets_file}. Usando lista padrão.")
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

    provider = DataProvider()
    calc = MPRMCalculator()

    print(f"--- Monitorando MPRM V14.1 ({len(symbols)} ativos) ---")

    for symbol in symbols:
        try:
            # 1. Coleta de dados
            df = provider.fetch_ohlcv(symbol)

            # 2. Cálculos matemáticos
            df = calc.calculate_physics(df)
            df = calc.calculate_markov(df)
            df = calc.identify_regime(df)

            # 3. Processamento de sinais (Estado por ativo)
            engine = MPRMEngine()
            df = engine.process_signals(df)

            # 4. Exibição de resultados detalhados
            last = df.iloc[-1]
            atr = last['atr_sl']
            price = last['close']
            trail = last['trail_stop_val']
            dist_trail = abs(price - trail) if not np.isnan(trail) else 0

            print(f"\n" + "="*40)
            print(f"ATIVO: {symbol} | PREÇO: {price:.4f}")
            print(f"REGIME: {last['regime']} ({last['dynamic_state']})")
            print(f"VALIDADE: {last['signal_validity']} (Idade: {engine.bars_since_ignition} candles)")

            # Decisões (HUD Markov)
            print(f"-"*20)
            print(f"FORÇA MARKOV:")
            print(f"  BULL: {last['p_bull']*100:4.1f}% | BEAR: {last['p_bear']*100:4.1f}%")
            print(f"  COMP: {last['p_comp']*100:4.1f}% | EXH : {last['p_exh']*100:4.1f}%")

            # Gestão de Trail
            if not np.isnan(trail):
                print(f"TRAIL STOP: {trail:.4f} (Dist: {dist_trail:.4f} | ATR: {atr:.4f})")

            # Gatilhos e Alertas
            print(f"-"*20)
            if last['ignition_long']:
                print("⚡ GATILHO: NOVO SINAL DE COMPRA (IGNITION)!")
            elif last['ignition_short']:
                print("🔥 GATILHO: NOVO SINAL DE VENDA (IGNITION)!")

            if last['partial_exit_50']:
                print("⚠️ ALERTA: Saída Parcial 50% (Linha Trail FLAT)")
            if last['partial_exit_30']:
                print("🚀 ALERTA: Saída Parcial 30% (Preço Esticado > 1 ATR)")

            if last['exit_signal'] and not (last['ignition_long'] or last['ignition_short']):
                print("❌ SINAL: SAÍDA TOTAL DA OPERAÇÃO")

        except Exception as e:
            print(f"Erro ao processar {symbol}: {e}")

if __name__ == "__main__":
    monitor_market()
