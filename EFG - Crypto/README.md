# EFG - Crypto: Automação MPRM V14.1

Este projeto automatiza a geração de sinais de trading baseados no modelo **Market Physics Regime Model (MPRM V14.1)**.

## 🚀 Configuração Inicial (macOS)

### 1. Preparar a Pasta no Desktop
Abra o **Terminal** e execute:
```bash
cd ~/Desktop
mkdir "EFG - Crypto"
cd "EFG - Crypto"
```

### 2. Abrir no Visual Studio Code
1. Abra o **Visual Studio Code**.
2. Vá em **File > Open Folder...** (Arquivo > Abrir Pasta).
3. Selecione a pasta `EFG - Crypto` no seu Desktop.

### 3. Configurar Ambiente Python
No terminal do VS Code:
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## 🛠 Estrutura do Projeto
- `main.py`: Script principal para monitoramento de múltiplos ativos.
- `core/`:
  - `calculator.py`: Cálculos de física de preço e Cadeia de Markov.
  - `engine.py`: Lógica de sinais, trailing stop e saídas parciais.
  - `data_provider.py`: Conexão com exchanges via CCXT.
- `docs/`: Manual de operação em Python.
- `source_material/`: Código original Pine Script e manuais de referência.

## 📈 Lógica de Operação (Resumo)
- **Ignition:** Sinais de entrada baseados em regime dominante (Bull/Bear).
- **Validade:** Sinais expiram após 20 candles de inércia.
- **Saídas Parciais:**
  - 50% se a linha de trail ficar "Flat" por 3 candles.
  - 30% se o preço esticar > 1 ATR da linha de trail.

## 🔗 Repositório Remoto
Para sincronizar com seu GitHub:
```bash
git init
git remote add origin https://github.com/corpodelideresbrasil/python
git add .
git commit -m "Initial MPRM Python Setup"
git push -u origin main
```

---
*Desenvolvido para alta precisão na termodinâmica de criptoativos.*
