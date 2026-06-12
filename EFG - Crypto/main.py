from core.data_provider import DataProvider
from core.calculator import MPRMCalculator
from core.engine import MPRMEngine

def monitor_market(symbols):
    provider = DataProvider()
    calc = MPRMCalculator()

    print("--- Monitorando MPRM V14.1 ---")

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

            # 4. Exibição de resultados
            last = df.iloc[-1]
            print(f"\nAtivo: {symbol} | Regime: {last['regime']} | Estado: {last['dynamic_state']}")
            print(f"Validade: {last['signal_validity']}")

            if last['ignition_long']:
                print("⚡ GATILHO COMPRA!")
            elif last['ignition_short']:
                print("🔥 GATILHO VENDA!")

            if last['partial_exit_50']:
                print("⚠️ ALERTA: Saída Parcial 50% (Flat)")
            if last['partial_exit_30']:
                print("🚀 ALERTA: Preço Esticado (Saída 30%)")

        except Exception as e:
            print(f"Erro ao processar {symbol}: {e}")

if __name__ == "__main__":
    # Lista de ativos para monitorar
    monitor_market(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
