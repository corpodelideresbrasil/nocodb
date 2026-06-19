# Supertrend v3.6 - Python implementation

Este projeto é uma implementação robusta em Python do indicador **Supertrend v3.6**, otimizado para rodar em qualquer sistema operacional (Windows, Mac, Linux) sem erros de importação.

## Estrutura do Projeto

- `main.py`: Script consolidado que contém toda a lógica do scanner.
- `assets.json`: Arquivo de configuração para listar os ativos a serem monitorados.
- `requirements.txt`: Dependências do projeto (Pandas, NumPy, CCXT, Tabulate).

## Como Configurar os Ativos

Para monitorar novas moedas, edite o arquivo `assets.json` na raiz da pasta. Adicione os pares no formato `MOEDA/USDT`:

```json
{
    "assets": [
        "BTC/USDT",
        "ETH/USDT",
        "ADA/USDT",
        "SOL/USDT"
    ]
}
```

## Como Iniciar

1. **Abrir a pasta do projeto**:
   No VS Code, vá em `File > Open Folder...` e selecione `supertrend_v3_6`.

2. **Criar um Ambiente Virtual**:
   ```bash
   python -m venv venv
   ```

3. **Ativar o Ambiente Virtual**:
   - **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
   - **Windows (CMD)**: `venv\Scripts\activate`
   - **Mac / Linux / Git Bash**: `source venv/bin/activate`

4. **Instalar as Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Executar o Scanner**:
   ```bash
   python main.py
   ```

## Observações
O scanner utiliza a biblioteca `ccxt` com a exchange **Kraken** por padrão para garantir estabilidade global. Se um ativo não for encontrado, verifique se ele está listado na Kraken.
