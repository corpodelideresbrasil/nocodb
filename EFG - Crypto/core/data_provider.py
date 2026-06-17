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
        # Carrega os mercados para garantir que as traduções de símbolos funcionem
        try:
            self.exchange.load_markets()
        except:
            pass

    def fetch_ohlcv(self, symbol, timeframe='1d', limit=500):
        """
        Busca dados de futuros. Binance Futures usa símbolos como BTC/USDT.
        Aumentado para 500 barras para garantir convergência matemática (EMA/ATR).
        """
        try:
            # Limpa o símbolo
            clean_symbol = symbol.replace(',', '').replace("'", "").replace('"', '').strip()

            # Se não houver barra, tenta formatar para o padrão CCXT
            if '/' not in clean_symbol:
                if clean_symbol.endswith('USDT'):
                    clean_symbol = clean_symbol[:-4] + '/USDT'

            ohlcv = self.exchange.fetch_ohlcv(clean_symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            # Tenta sem a barra se falhar
            try:
                raw_symbol = clean_symbol.replace('/', '')
                ohlcv = self.exchange.fetch_ohlcv(raw_symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
            except:
                print(f"Erro ao buscar dados para {symbol}: {e}")
                return None
