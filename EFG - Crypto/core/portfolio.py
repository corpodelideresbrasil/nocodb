import json
import os

class PortfolioManager:
    """
    Gerencia o estado das posições e as regras de risco.
    - Saldo Dinâmico
    - Margem Total Máxima: 20%
    - Alavancagem Inteira (1x a 15x)
    """

    def __init__(self, filename='portfolio.json', default_balance=200.0):
        self.filename = filename
        self.default_balance = default_balance
        self.data = self._load()

        # Garante que os campos existem
        if 'balance' not in self.data: self.data['balance'] = default_balance
        if 'positions' not in self.data: self.data['positions'] = {}

        self.margin_per_asset_pct = 0.02 # 2% ($4.00)
        self.max_total_margin_pct = 0.20 # 20% ($40.00)
        self.max_leverage_per_asset = 15
        self.max_total_leverage = 5.0

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        return content
            except Exception:
                pass
        return {'balance': self.default_balance, 'positions': {}}

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    @property
    def balance(self):
        return self.data.get('balance', self.default_balance)

    @property
    def positions(self):
        return self.data.get('positions', {})

    def get_current_total_margin(self):
        return sum(p.get('margin_usd', 0) for p in self.positions.values())

    def get_current_total_notional(self):
        return sum(p.get('notional_usdt', 0) for p in self.positions.values())

    def get_current_total_leverage(self):
        if self.balance <= 0: return 0.0
        return self.get_current_total_notional() / self.balance

    def calculate_suggested_leverage(self, markov_strength):
        """Calcula alavancagem inteira (1-15x) baseada na força."""
        suggested = int(round(markov_strength * 30.0))
        return min(self.max_leverage_per_asset, max(1, suggested))

    def update_balance(self, profit_loss):
        self.data['balance'] += profit_loss
        self.save()

    def can_open_new(self):
        """Verifica se ainda há espaço na margem total (20%)."""
        limit = self.balance * self.max_total_margin_pct
        return self.get_current_total_margin() + (self.balance * self.margin_per_asset_pct) <= limit

    def open_position(self, symbol, side, price, strength, leverage):
        if not self.can_open_new():
            return False

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
        return True

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
