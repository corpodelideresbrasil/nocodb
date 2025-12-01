# Guia: Criando um Formulário de Agendamento com Google Forms e Sheets

Este guia detalha o processo de criação de um sistema de agendamento onde os participantes escolhem horários pré-definidos, e as respostas são automaticamente organizadas em uma planilha para fácil visualização.

---

### **Visão Geral do Processo**

1.  **Preparar a Lista de Disponibilidade:** Definir todos os horários que serão oferecidos.
2.  **Configurar o Google Forms:** Criar o formulário com seções semanais e perguntas de múltipla escolha.
3.  **Conectar ao Google Sheets:** Salvar as respostas automaticamente em uma planilha.
4.  **Implementar a Fórmula Mágica:** Usar uma fórmula avançada no Google Sheets para transformar os dados brutos em uma agenda limpa e organizada.

---

### **Passo 1: Prepare sua Lista de Disponibilidade**

Antes de criar o formulário, tenha uma lista clara de todos os dias e períodos que você deseja oferecer até 30 de janeiro. Organize-a por semana para facilitar a configuração.

**Exemplo:**

*   **Semana 1 (02/Dez - 08/Dez):**
    *   02/12/2024 - Manhã
    *   03/12/2024 - Tarde
    *   05/12/2024 - Manhã
    *   05/12/2024 - Noite
*   **Semana 2 (09/Dez - 15/Dez):**
    *   09/12/2024 - Manhã
    *   11/12/2024 - Tarde
    *   11/12/2024 - Noite
*   ...e assim por diante.

---

### **Passo 2: Configurando o Formulário Google**

1.  **Acesse o [Google Forms](https://forms.google.com)** e crie um novo formulário.

2.  **Adicione Campos de Identificação:**
    *   **Nome Completo:** Pergunta do tipo "Resposta curta". Marque como "Obrigatória".
    *   **Seu melhor e-mail:** Pergunta do tipo "Resposta curta". Marque como "Obrigatória".

3.  **Crie Seções Semanais:**
    *   Clique em **"Adicionar seção"** (ícone de duas barras) para criar a primeira seção.
    *   **Título da Seção:** `Semana 1 (02/Dez a 08/Dez)`.

4.  **Adicione a Pergunta de Agendamento na Seção:**
    *   Dentro da seção, clique em **"Adicionar pergunta"**.
    *   **Título da Pergunta:** `Escolha até 2 horários disponíveis para a Semana 1:`
    *   **Tipo de Pergunta:** **Caixas de seleção**.
    *   **Opções:** Adicione os horários que você listou para a Semana 1, um por linha.
        *   `02/12/2024 - Manhã`
        *   `03/12/2024 - Tarde`
        *   `05/12/2024 - Manhã`
        *   `05/12/2024 - Noite`
    *   **Validação de Resposta (Fundamental):**
        *   Clique nos três pontinhos no canto inferior direito da pergunta.
        *   Selecione **"Validação de resposta"**.
        *   Configure a regra como: **"Selecionar no máximo"** e o número **"2"**.

5.  **Duplique para as Próximas Semanas:**
    *   Clique no ícone de duplicar na pergunta que você acabou de criar.
    *   Arraste a pergunta duplicada para a próxima seção (ou crie uma nova seção e arraste para lá).
    *   **Importante:** Altere o título da pergunta e, principalmente, **atualize as opções de horários** para corresponderem à nova semana.
    *   Repita o processo para todas as semanas até 30 de janeiro.

---

### **Passo 3: Conectando com o Google Sheets**

1.  No seu formulário, vá para a aba **"Respostas"**.
2.  Clique no ícone verde de Planilhas (Sheets).
3.  Selecione **"Criar uma nova planilha"**. Dê um nome claro (ex: `Agendamentos - Respostas Brutas`) e clique em "Criar".

Sua planilha será criada com colunas como: `Carimbo de data/hora`, `Nome Completo`, `Seu melhor e-mail`, `Escolha até 2 horários... (Semana 1)`, etc.

---

### **Passo 4: Implementando a Fórmula no Google Sheets**

Esta é a etapa final, onde transformamos os dados.

1.  **Crie uma Nova Aba:**
    *   Na planilha que acabou de ser criada, clique no ícone `+` no canto inferior esquerdo para adicionar uma nova página (aba).
    *   Renomeie esta nova aba para **`Agenda Final`**.

2.  **Defina os Cabeçalhos:**
    *   Na célula `A1` de `Agenda Final`, digite: **Nome**
    *   Na célula `B1`, digite: **Email**
    *   Na célula `C1`, digite: **Horário Escolhido**

3.  **Insira a Fórmula:**
    *   Clique na célula **`A2`**.
    *   Copie e cole a fórmula abaixo.

    **Antes de colar, você PRECISA verificar e ajustar os seguintes pontos na fórmula:**
    *   O nome da sua aba de respostas. No exemplo, usamos `'Página de respostas 1'`. **Altere se o seu for diferente!** (Ex: `'Respostas ao formulário 1'`).
    *   As letras das colunas. No exemplo, as respostas das semanas começam na coluna `D`. Verifique na sua planilha e ajuste se necessário.

    ```excel
    =QUERY(
      ARRAYFORMULA(
        SPLIT(
          FLATTEN({
            IF(ISBLANK('Página de respostas 1'!D2:D),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!D2:D, ", "));
            IF(ISBLANK('Página de respostas 1'!E2:E),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!E2:E, ", "));
            IF(ISBLANK('Página de respostas 1'!F2:F),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!F2:F, ", "));
            IF(ISBLANK('Página de respostas 1'!G2:G),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!G2:G, ", "));
            IF(ISBLANK('Página de respostas 1'!H2:H),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!H2:H, ", "));
            IF(ISBLANK('Página de respostas 1'!I2:I),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!I2:I, ", "));
            IF(ISBLANK('Página de respostas 1'!J2:J),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!J2:J, ", "));
            IF(ISBLANK('Página de respostas 1'!K2:K),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!K2:K, ", "));
            IF(ISBLANK('Página de respostas 1'!L2:L),, 'Página de respostas 1'!B2:B & "♦" & 'Página de respostas 1'!C2:C & "♦" & SPLIT('Página de respostas 1'!L2:L, ", "))
          }),
        "♦")
      ),
    "SELECT * WHERE Col3 IS NOT NULL")
    ```

    **Como Expandir a Fórmula:**
    *   A fórmula acima cobre 9 semanas de respostas (da coluna `D` até a `L`).
    *   Se você tiver mais semanas, simplesmente copie a linha `IF(ISBLANK...` e cole-a abaixo da última, **alterando a letra da coluna** para a próxima (ex: `M2:M`). Faça isso para cada coluna de resposta adicional.

### **Resultado**

A aba `Agenda Final` será preenchida automaticamente com cada escolha de horário em uma linha separada, vinculada ao nome e e-mail do participante, pronta para ser usada por outras pessoas.

| Nome | Email | Horário Escolhido |
| :--- | :--- | :--- |
| Maria Silva | maria@exemplo.com | 02/12/2024 - Manhã |
| João Santos | joao@exemplo.com | 03/12/2024 - Tarde |
| Maria Silva | maria@exemplo.com | 05/12/2024 - Noite |
| ... | ... | ... |

A planilha será atualizada em tempo real à medida que novas respostas forem enviadas.
