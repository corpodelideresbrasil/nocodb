import json
import os

class PortfolioManager:
    """
    Gerencia o estado das posições e as regras de risco do manual.
    Saldo: 200 USD | Risco/Ativo: 2% Margem | Alavancagem Total: 5X
    """

    def __init__(self, filename='portfolio.json', balance=200.0):
        self.filename = filename
        self.balance = balance
        self.margin_per_asset_pct = 0.02 # 2%
        self.max_total_leverage = 5.0
        self.positions = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {}

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.positions, f, indent=4)

    def get_total_notional(self):
        """Calcula o valor nocional total ocupado (Margem * Alavancagem)."""
        # Como cada posição usa 2% do saldo com alavancagem de 5x
        # O nocional de cada ativo é 10% do saldo total (0.02 * 5 = 0.1)
        total_margin = sum(p['margin_usd'] for p in self.positions.values())
        return total_margin * self.max_total_leverage

    def get_current_leverage(self):
        """Calcula a alavancagem atual da carteira."""
        if self.balance <= 0: return 0
        return self.get_total_notional() / self.balance

    def can_open_new(self):
        """Verifica se ainda há espaço na alavancagem total de 5x."""
        return self.get_current_leverage() < (self.max_total_leverage - 0.1)

    def open(self, symbol, side, price, strength):
        if not self.can_open_new(): return False

        self.positions[symbol] = {
            'side': side,
            'entry_price': price,
            'margin_usd': self.balance * self.margin_per_asset_pct,
            'markov_strength': strength,
            'notional_usd': (self.balance * self.margin_per_asset_pct) * self.max_total_leverage
        }
        self.save()
        return True

    def close(self, symbol):
        if symbol in self.positions:
            del self.positions[symbol]
            self.save()
