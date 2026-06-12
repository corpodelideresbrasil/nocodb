import ccxt
import pandas as pd

class DataProvider:
    """
    Provedor de dados OHLCV para Binance Futures (Perpétuos).
    """

    def __init__(self, exchange_id='binance'):
        self.exchange = getattr(ccxt, exchange_id)({
            'options': {'defaultType': 'future'}
        })

    def fetch_ohlcv(self, symbol, timeframe='1d', limit=100):
        """
        Busca dados de futuros. Binance Futures usa símbolos como BTC/USDT.
        """
        try:
            # Sanea o símbolo caso venha com vírgulas ou aspas
            clean_symbol = symbol.replace(',', '').replace("'", "").replace('"', '').strip()
            ohlcv = self.exchange.fetch_ohlcv(clean_symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Erro ao buscar dados para {symbol}: {e}")
            return None
