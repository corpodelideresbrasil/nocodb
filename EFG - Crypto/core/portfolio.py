import json
import os

class PortfolioManager:
    """
    Gerencia o estado das posições e as regras de risco.
    - Saldo Dinâmico
    - Margem Total Máxima: 25% ($50.00 para saldo de $200.00)
    - Margem/Ativo: 2% ($4.00 para saldo de $200.00)
    - Alavancagem Inteira (1x a 15x)
    """

    def __init__(self, filename='portfolio.json', default_balance=200.0):
        self.filename = filename
        self.default_balance = default_balance
        self.data = self._load()

        # Inicializa se o arquivo for novo
        if 'balance' not in self.data: self.data['balance'] = default_balance
        if 'positions' not in self.data: self.data['positions'] = {}

        self.margin_per_asset_pct = 0.02
        self.max_total_margin_pct = 0.25 # Ajustado para 25% conforme solicitado
        self.max_leverage_per_asset = 15
        self.max_total_leverage = 5.0

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    content = json.load(f)
                    return content if isinstance(content, dict) else {}
            except Exception:
                pass
        return {}

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    @property
    def balance(self):
        return float(self.data.get('balance', self.default_balance))

    @property
    def positions(self):
        return self.data.get('positions', {})

    def get_current_total_margin(self):
        """Soma da margem usada em todas as posições no JSON."""
        return sum(float(p.get('margin_usd', 0)) for p in self.positions.values())

    def get_current_total_notional(self):
        """Soma do valor nominal (USDT) de todas as posições."""
        return sum(float(p.get('notional_usdt', 0)) for p in self.positions.values())

    def get_current_total_leverage(self):
        """Alavancagem real da carteira (Notional / Saldo)."""
        b = self.balance
        return self.get_current_total_notional() / b if b > 0 else 0.0

    def calculate_suggested_leverage(self, markov_strength):
        """Calcula alavancagem inteira (1-15x) para maximizar lucro."""
        suggested = int(round(markov_strength * 30.0))
        return min(self.max_leverage_per_asset, max(1, suggested))

    def can_open_new(self, margin_needed):
        """Verifica se a nova posição cabe nos 25% de margem total."""
        limit = self.balance * self.max_total_margin_pct
        return (self.get_current_total_margin() + margin_needed) <= limit

    def open_position(self, symbol, side, price, strength, leverage):
        margin = self.balance * self.margin_per_asset_pct
        notional = margin * leverage

        self.data['positions'][symbol] = {
            'side': side,
            'entry_price': float(price),
            'margin_usd': float(margin),
            'leverage': int(leverage),
            'notional_usdt': float(notional),
            'markov_strength': float(strength)
        }
        self.save()

    def update_balance(self, profit_loss):
        self.data['balance'] = self.balance + profit_loss
        self.save()

    def close_position(self, symbol):
        if symbol in self.data['positions']:
            del self.data['positions'][symbol]
            self.save()

    def reduce_position(self, symbol, pct):
        if symbol in self.data['positions']:
            pos = self.data['positions'][symbol]
            factor = 1 - (pct / 100)
            pos['margin_usd'] *= factor
            pos['notional_usdt'] *= factor
            self.save()
