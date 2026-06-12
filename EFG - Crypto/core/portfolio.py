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

        # Inicializa campos se o arquivo for novo ou inválido
        if 'balance' not in self.data: self.data['balance'] = default_balance
        if 'positions' not in self.data: self.data['positions'] = {}

        self.margin_per_asset_pct = 0.02 # 2%
        self.max_total_margin_pct = 0.20 # 20%
        self.max_leverage_per_asset = 15
        self.max_total_leverage = 5.0

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    content = json.load(f)
                    return content if isinstance(content, dict) else {}
            except Exception:
                return {}
        return {}

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
        """Calcula alavancagem inteira (1-15x)."""
        suggested = int(round(markov_strength * 30.0))
        return min(self.max_leverage_per_asset, max(1, suggested))

    def update_balance(self, profit_loss):
        self.data['balance'] += profit_loss
        self.save()

    def open_position(self, symbol, side, price, strength, leverage):
        margin = self.balance * self.margin_per_asset_pct
        notional = margin * leverage
        self.data['positions'][symbol] = {
            'side': side,
            'entry_price': price,
            'margin_usd': margin,
            'leverage': int(leverage),
            'notional_usdt': notional,
            'quantity': notional / price if price > 0 else 0
        }
        self.save()

    def reduce_position(self, symbol, pct):
        """Reduz a margem e o nocional de uma posição."""
        if symbol in self.positions:
            pos = self.data['positions'][symbol]
            reduction_factor = 1 - (pct / 100)
            pos['margin_usd'] *= reduction_factor
            pos['notional_usdt'] *= reduction_factor
            pos['quantity'] *= reduction_factor
            self.save()

    def close_position(self, symbol):
        if symbol in self.data['positions']:
            del self.data['positions'][symbol]
            self.save()
