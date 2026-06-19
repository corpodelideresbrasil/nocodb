# Supertrend v3.6 - Python implementation

Este projeto é uma implementação em Python do indicador **Supertrend v3.6**, originalmente desenvolvido em Pine Script. Ele automatiza a geração de sinais de compra, venda e encerramento por inércia para múltiplos ativos.

## Estrutura do Projeto

- `core/`: Motores de cálculo (Supertrend) e lógica de sinais (Inércia).
- `data/`: Provedor de dados via `ccxt`.
- `main.py`: Script principal para execução do scanner.
- `requirements.txt`: Dependências do projeto.

## Como Iniciar no VS Code

1. **Abrir a pasta do projeto**:
   Abra o VS Code e vá em `File > Open Folder...` e selecione a pasta `supertrend_v3_6`.

2. **Criar um Ambiente Virtual (Recomendado)**:
   Abra o terminal integrado (`Ctrl + '` ou ``Ctrl + Shift + ` ``) e execute:
   ```bash
   python -m venv venv
   ```

3. **Ativar o Ambiente Virtual**:
   - **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar as Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Executar o Scanner**:
   ```bash
   python main.py
   ```

## Configurações

Você pode editar a lista de ativos e o timeframe diretamente no arquivo `main.py`.
O provedor de dados utiliza a biblioteca `ccxt`. Por padrão, está configurado para a exchange **Kraken** para evitar restrições regionais, mas pode ser alterado em `data/provider.py`.
