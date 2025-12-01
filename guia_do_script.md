# Guia de Implementação do Google Apps Script para Agendamentos

Olá! Esta é a abordagem definitiva para automatizar sua planilha usando o Google Apps Script. Siga os passos abaixo com atenção. O script é muito mais robusto que as fórmulas e nos dará um controle preciso sobre a manipulação dos dados.

---

### **Visão Geral**

1.  **Abriremos o Editor de Scripts** na sua planilha.
2.  **Colaremos o código** que eu preparei.
3.  **Executaremos o script manualmente** uma vez para testar e autorizar.
4.  **Configuraremos um gatilho (trigger)** para que o script rode automaticamente a cada nova resposta do formulário.

---

### **Passo 1: Abrindo o Editor de Scripts**

1.  Abra sua planilha do Google Sheets.
2.  No menu superior, vá em **Extensões > Apps Script**.
3.  Uma nova aba ou janela abrirá com o editor de scripts. Ele pode ter um arquivo padrão chamado `Código.gs`.

### **Passo 2: Colando o Código**

1.  Apague todo o conteúdo que estiver no arquivo `Código.gs`.
2.  Copie o código abaixo na íntegra.
3.  Cole o código na janela do editor que você acabou de limpar.

```javascript
// --- CONFIGURAÇÃO ---
// Nomes das abas da sua planilha. ATENÇÃO: Altere o nome da aba de respostas para 'Respostas' se necessário.
const NOME_ABA_RESPOSTAS = 'Respostas';
const NOME_ABA_AGENDA = 'Agenda Final';

// IMPORTANTE: Ajuste os números das colunas aqui se o seu formulário mudar.
// A contagem começa em 1 (Coluna A = 1, B = 2, etc.)
const COLUNA_PARTICIPANTE = 2;
const COLUNA_COACH = 3;
const COLUNA_INICIAL_EPI = 5; // Primeira coluna com respostas "EPI/FULL"
const COLUNA_FINAL_EPI = 12;  // Última coluna com respostas "EPI/FULL"
const COLUNA_AE = 13;         // Coluna com respostas "AE"
// --------------------

/**
 * Função para converter o nome do mês (ex: 'dez') para o número do mês (ex: 12).
 */
function getNumeroDoMes(nomeDoMes) {
  const mapaDosMeses = {
    'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
  };
  return mapaDosMeses[nomeDoMes.toLowerCase().substring(0, 3)];
}

/**
 * Função principal que processa todas as respostas do formulário e as organiza na aba 'Agenda Final'.
 */
function processarTodasAsRespostas() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const abaRespostas = spreadsheet.getSheetByName(NOME_ABA_RESPOSTAS);
  const abaAgenda = spreadsheet.getSheetByName(NOME_ABA_AGENDA);
  const CABECALHOS = ['ID', 'Data', 'Dia da Semana', 'Horário', 'Tipo de Assistência', 'Participante', 'Coach'];

  if (!abaRespostas) {
    SpreadsheetApp.getUi().alert('Erro: A aba de respostas "' + NOME_ABA_RESPOSTAS + '" não foi encontrada.');
    return;
  }
  if (!abaAgenda) {
    SpreadsheetApp.getUi().alert('Erro: A aba de destino "' + NOME_ABA_AGENDA + '" não foi encontrada.');
    return;
  }

  // Limpa a aba de agenda e reescreve o cabeçalho.
  abaAgenda.clear();
  abaAgenda.getRange(1, 1, 1, CABECALHOS.length).setValues([CABECALHOS]).setFontWeight('bold');

  const dados = abaRespostas.getRange(2, 1, abaRespostas.getLastRow() - 1, abaRespostas.getLastColumn()).getValues();
  let agendaFinal = [];
  const diasDaSemana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

  dados.forEach(linha => {
    const participante = linha[COLUNA_PARTICIPANTE - 1];
    const coach = linha[COLUNA_COACH - 1];

    if (!participante) return; // Pula linhas sem participante.

    // Processa as colunas de agendamento "EPI/FULL"
    for (let i = COLUNA_INICIAL_EPI - 1; i < COLUNA_FINAL_EPI; i++) {
      if (linha[i]) {
        const agendamentos = linha[i].toString().split(', ');
        agendamentos.forEach(agendamento => {
          // Modificado para aceitar '1º' ou '1'
          const partes = agendamento.trim().match(/(\d{1,2})º?\/(\w+)\/(\d{2})\s+\(([^)]+)\)/);
          if (partes) {
            const dia = parseInt(partes[1], 10);
            const nomeDoMes = partes[2];
            const ano = 2000 + parseInt(partes[3], 10);
            const horario = partes[4];
            const mes = getNumeroDoMes(nomeDoMes);

            if (mes) {
              const data = new Date(ano, mes - 1, dia);
              agendaFinal.push([data, diasDaSemana[data.getDay()], horario, 'EPI/FULL', participante, coach]);
            }
          }
        });
      }
    }

    // Processa a coluna de agendamento "AE"
    if (linha[COLUNA_AE - 1]) {
      const agendamentosAE = linha[COLUNA_AE - 1].toString().split(/,|\n/);
      agendamentosAE.forEach(agendamento => {
        const partes = agendamento.trim().match(/(\d{2})\/(\d{2})\/(\d{2})\s*-\s*(\d{2}:\d{2})/);
        if (partes) {
          const dia = parseInt(partes[1], 10);
          const mes = parseInt(partes[2], 10);
          const ano = 2000 + parseInt(partes[3], 10);
          const horario = partes[4];
          const data = new Date(ano, mes - 1, dia);
          agendaFinal.push([data, diasDaSemana[data.getDay()], horario, 'AE', participante, coach]);
        }
      });
    }
  });

  // Ordena todos os agendamentos por data.
  agendaFinal.sort((a, b) => a[0] - b[0]);

  // Escreve os resultados na planilha se houver dados a serem escritos.
  if (agendaFinal.length > 0) {
    const output = agendaFinal.map((entry, index) => {
      return [
        index + 1, // ID sequencial
        entry[0],  // Data
        entry[1],  // Dia da Semana
        entry[2],  // Horário
        entry[3],  // Tipo
        entry[4],  // Participante
        entry[5]   // Coach
      ];
    });
    abaAgenda.getRange(2, 1, output.length, output[0].length).setValues(output);
    // Aplica o formato de data apenas na coluna B (Datas).
    abaAgenda.getRange(2, 2, output.length, 1).setNumberFormat('dd/mm/yyyy');
  }
}

/**
 * Função auxiliar para criar o gatilho 'onFormSubmit' programaticamente.
 * Execute esta função uma vez manualmente para configurar a automação.
 */
function configurarGatilho() {
  // Deleta gatilhos antigos para evitar duplicações.
  const todosOsGatilhos = ScriptApp.getProjectTriggers();
  todosOsGatilhos.forEach(gatilho => {
    if (gatilho.getHandlerFunction() === 'processarTodasAsRespostas') {
      ScriptApp.deleteTrigger(gatilho);
    }
  });

  // Cria o novo gatilho.
  ScriptApp.newTrigger('processarTodasAsRespostas')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onFormSubmit()
    .create();
}
```
4.  Clique no ícone de **Salvar projeto** (parece um disquete) no topo do editor.

### **Passo 3: Executando o Script Manualmente (Teste e Autorização)**

Esta etapa é **fundamental**. Você precisa executá-la uma vez para dar ao script permissão para gerenciar sua planilha.

1.  Ainda no editor de scripts, verifique se a função `processarTodasAsRespostas` está selecionada no menu dropdown ao lado do botão "Depurar".
2.  Clique no botão **Executar**.
3.  A primeira vez que você executar, o Google pedirá **"Revisar permissões"**.
4.  Clique em "Revisar permissões" e escolha sua conta do Google.
5.  Você verá um aviso de que "O Google não verificou este app". Isso é normal para scripts pessoais. Clique em **"Avançado"** e depois em **"Acessar (nome do seu projeto)"**.
6.  Clique em **"Permitir"** para conceder as permissões.
7.  O script será executado. Verifique sua aba `Agenda Final`. Ela deve ter sido preenchida e organizada corretamente!

### **Passo 4: Configurando o Gatilho Automático**

Agora vamos fazer com que o script rode sozinho sempre que um novo formulário for enviado.

1.  No editor de scripts, clique no ícone de **Acionadores** na barra lateral esquerda (parece um despertador).
2.  Na tela de acionadores, clique no botão **"+ Adicionar acionador"** no canto inferior direito.
3.  Configure o acionador da seguinte forma:
    *   **Escolha a função a ser executada:** `processarTodasAsRespostas`
    *   **Escolha a implantação que será executada:** `Principal`
    *   **Selecione a origem do evento:** `Da planilha`
    *   **Selecione o tipo de evento:** `Ao enviar formulário`
4.  Clique em **Salvar**.

**Pronto!** A partir de agora, a cada nova resposta, o script será executado automaticamente e sua `Agenda Final` será atualizada em tempo real.

---

### **Solução de Problemas Comuns**

*   **Erro: `TypeError: Cannot read properties of null (reading 'clear')`**
    *   **Causa:** Este é o erro mais comum. Significa que o script não conseguiu encontrar uma das abas da sua planilha (provavelmente a `Agenda Final` ou `Página de respostas 1`).
    *   **Solução:** Verifique se os nomes das suas abas na planilha são **idênticos** aos que estão na seção de `--- CONFIGURAÇÃO ---` no topo do script. Cuidado com espaços extras ou erros de digitação! Corrija o nome na planilha ou no script, salve e execute novamente.

---

Se ocorrer qualquer outro erro, o Apps Script geralmente mostra uma mensagem clara sobre a causa. Se isso acontecer, me informe o erro. Estou confiante que esta solução funcionará para você.