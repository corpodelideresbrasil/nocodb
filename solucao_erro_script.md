# Guia de Correção: Erro "Cannot read properties of null (reading 'clear')"

Olá! Este é um erro muito comum e fácil de resolver no Apps Script. A mensagem é técnica, mas a causa é simples.

### O Que o Erro Significa?

`TypeError: Cannot read properties of null (reading 'clear')`

Traduzindo: "O script tentou executar a ação `.clear()` (limpar a planilha) em um objeto que está `null` (vazio/não encontrado)."

Isso acontece porque o script não conseguiu encontrar uma ou ambas as abas da planilha que você especificou na seção de configuração.

### Causa Provável

Há uma pequena diferença entre o nome da aba na sua planilha e o nome que está no código do script.

No script, os nomes estão definidos assim:
```javascript
const NOME_ABA_RESPOSTAS = 'Página de respostas 1';
const NOME_ABA_AGENDA = 'Agenda Final';
```

### Como Corrigir (em 30 segundos)

Você tem duas opções, ambas funcionam:

#### Opção A: Renomear as Abas na Planilha (Recomendado)

1.  Vá para a sua planilha Google Sheets.
2.  Verifique o nome da aba que recebe as respostas do formulário. **Garanta que o nome seja exatamente `Página de respostas 1`**. Cuidado com espaços extras no final!
3.  Verifique o nome da aba onde a agenda deve ser criada. **Garanta que o nome seja exatamente `Agenda Final`**.
4.  Execute o script novamente.

#### Opção B: Alterar o Nome no Script

1.  Vá para a sua planilha e anote os nomes exatos das suas abas (a de respostas e a de destino).
2.  Abra o editor de scripts (`Extensões > Apps Script`).
3.  No topo do código, altere os valores das constantes `NOME_ABA_RESPOSTAS` e `NOME_ABA_AGENDA` para que correspondam **exatamente** aos nomes das suas abas.

    **Exemplo:** Se sua aba de respostas se chama `Respostas`, o código ficaria assim:
    ```javascript
    const NOME_ABA_RESPOSTAS = 'Respostas';
    const NOME_ABA_AGENDA = 'Agenda Final';
    ```
4.  Clique no ícone de **Salvar** e execute o script novamente.

---

Após fazer essa verificação e ajuste, o script encontrará as abas corretamente e será executado sem erros. Estamos quase lá!