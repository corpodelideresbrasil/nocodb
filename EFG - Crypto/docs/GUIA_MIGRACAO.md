# Guia de Migração e Configuração do Projeto

Este documento fornece as instruções necessárias para transferir este projeto para o seu ambiente local e manter a sincronia com o repositório oficial.

## 1. Endereço do Repositório
O código base e os registros de desenvolvimento estão hospedados em:
**URL:** `https://github.com/corpodelideresbrasil/nocodb`

## 2. Como passar o código para o novo projeto?

Para configurar este projeto em uma nova pasta ou máquina (como o seu macOS Desktop), siga estes passos:

1.  **Clone o Repositório (ou baixe os arquivos):**
    ```bash
    git clone https://github.com/corpodelideresbrasil/nocodb.git
    ```
2.  **Localize a pasta do projeto:**
    O projeto de automação Python está contido na pasta `EFG - Crypto`.
3.  **Configure o Ambiente Python:**
    Certifique-se de estar usando o Python 3.14 (ou superior).
    ```bash
    cd "EFG - Crypto"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  **Arquivo de Ativos:**
    Edite o arquivo `assets.txt` para incluir os símbolos da Binance Futures que você deseja monitorar (ex: `BTCUSDT`, `ETHUSDT`).

## 3. Como passar as instruções escritas (arquivos)?

As instruções conceituais, manuais e materiais de origem foram organizados para facilitar a portabilidade:

1.  **Manual do Usuário:** Localizado em `docs/manual_usuario_python.md`. Este arquivo contém a tradução dos conceitos de física (Inércia, Atrito, Markov) para as fórmulas Python.
2.  **Materiais de Origem:** Todos os prompts e conceitos originais foram salvos na pasta `source_material/`.
3.  **Persistência:** O arquivo `portfolio.json` carrega o estado da sua banca e posições. Para mover seu progresso, basta copiar este arquivo para a nova pasta do projeto.

## 4. Estrutura do Projeto
- `main.py`: Ponto de entrada (Modo Oficial vs. Acompanhamento).
- `core/`: Motores de cálculo (Física, Markov, Risco).
- `assets.txt`: Lista de ativos para monitoramento.
- `portfolio.json`: Banco de dados local da sua carteira.

---
**Dica Jules:** Mantenha a pasta `EFG - Crypto` como uma unidade independente. Sempre que houver uma atualização no repositório `nocodb`, você pode copiar as melhorias da pasta `core/` para o seu projeto de execução.
