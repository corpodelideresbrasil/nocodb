from core.data_provider import DataProvider
from core.calculator import MPRMCalculator
from core.engine import MPRMEngine
import time

def monitor_market(symbols):
    """
    Loop principal de monitoramento de ativos.
    """
    provider = DataProvider()
    calc = MPRMCalculator(markov_len=20)

    print("--- Iniciando Monitoramento MPRM V14.1 ---")

    for symbol in symbols:
        print(f"\nAnalisando {symbol}...")

        # 1. Obter Dados
        df = provider.fetch_ohlcv(symbol, timeframe='1d', limit=100)
        if df is None: continue

        # 2. Calcular Lógica Matemática (Sem estado)
        df = calc.calculate_physics(df)
        df = calc.calculate_markov(df)
        df = calc.identify_regime(df)

        # 3. Processar Sinais (Com estado específico por ativo)
        engine = MPRMEngine(sl_mult=1.5)
        df = engine.process_signals(df)

        # 4. Verificar Último Estado (Gatilhos e Alertas)
        last_bar = df.iloc[-1]

        if last_bar['ignition_long']:
            print(f"  [GATILHO] ⚡ IGNITION LONG em {symbol}!")
        elif last_bar['ignition_short']:
            print(f"  [GATILHO] 🔥 IGNITION SHORT em {symbol}!")

        if last_bar['partial_exit_50']:
            print(f"  [ALERTA] ⚠️ LINHA FLAT: Sugestão de Realização Parcial (50%)")
        if last_bar['partial_exit_30']:
            print(f"  [ALERTA] 🚀 PREÇO ESTICADO (>1 ATR): Sugestão de Realização Parcial (30%)")

        print(f"  Regime Atual: {last_bar['regime']} | Validade: {last_bar['signal_validity']}")
        print(f"  Probabilidades Markov: Bull {last_bar['p_bull']:.1%} | Bear {last_bar['p_bear']:.1%}")

if __name__ == "__main__":
    # Exemplo com alguns ativos
    monitor_market(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
