import json
import os

class PortfolioManager:
    """
    Gerencia o estado das posições e as regras de risco do manual.
    - Saldo: 200 USD
    - Margem Total Máxima: 20% ($40)
    - Margem/Ativo: 2% ($4)
    - Alavancagem Máxima/Ativo: 15x
    - Alavancagem Total Carteira: 5x
    """

    def __init__(self, filename='portfolio.json', balance=200.0):
        self.filename = filename
        self.balance = balance
        self.margin_per_asset_pct = 0.02 # 2% ($4)
        self.max_total_margin_pct = 0.20 # 20% ($40)
        self.max_leverage_per_asset = 15.0
        self.max_total_leverage = 5.0
        self.positions = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.positions, f, indent=4)

    def get_current_total_margin(self):
        """Soma da margem usada em todas as posições abertas."""
        return sum(p.get('margin_usd', 0) for p in self.positions.values())

    def get_current_total_notional(self):
        """Soma do valor nominal (nocional) de todas as posições."""
        return sum(p.get('notional_usd', 0) for p in self.positions.values())

    def get_current_total_leverage(self):
        """Calcula a alavancagem efetiva da carteira (Notional Total / Saldo)."""
        if self.balance <= 0: return 0.0
        return self.get_current_total_notional() / self.balance

    def calculate_suggested_leverage(self, markov_strength):
        """
        Calcula a alavancagem sugerida para maximizar o lucro.
        Baseada na força de Markov, limitada a 15x.
        """
        # Exemplo: Se força é 50%, 0.5 * 30 = 15x. Se 40%, 0.4 * 30 = 12x.
        # Ajustamos o multiplicador para que forças altas cheguem no teto de 15x.
        suggested = markov_strength * 30.0
        return min(self.max_leverage_per_asset, max(1.0, suggested))

    def can_add_position(self):
        """Verifica limites de margem total (20%) e alavancagem total (5x)."""
        margin_ok = self.get_current_total_margin() < (self.balance * self.max_total_margin_pct)
        leverage_ok = self.get_current_total_leverage() < self.max_total_leverage
        return margin_ok and leverage_ok

    def open(self, symbol, side, price, strength, leverage):
        if not self.can_add_position(): return False

        margin = self.balance * self.margin_per_asset_pct
        notional = margin * leverage

        self.positions[symbol] = {
            'side': side,
            'entry_price': price,
            'margin_usd': margin,
            'leverage': leverage,
            'notional_usd': notional,
            'quantity': notional / price if price > 0 else 0
        }
        self.save()
        return True

    def close(self, symbol):
        if symbol in self.positions:
            del self.positions[symbol]
            self.save()
