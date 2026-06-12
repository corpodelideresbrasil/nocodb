import ccxt
import pandas as pd

class DataProvider:
    """
    Provedor de dados OHLCV para múltiplas exchanges via CCXT.
    """

    def __init__(self, exchange_id='binance'):
        self.exchange = getattr(ccxt, exchange_id)()

    def fetch_ohlcv(self, symbol, timeframe='1d', limit=100):
        """
        Busca dados históricos e retorna um DataFrame formatado.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Erro ao buscar dados para {symbol}: {e}")
            return None
