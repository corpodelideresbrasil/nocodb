# Guia da Fórmula Avançada para Agendamentos

Olá! Conforme solicitado, preparei uma fórmula robusta e centralizada para transformar os dados brutos do seu Google Forms na agenda organizada que você precisa.

A fórmula foi projetada para ser copiada e colada em uma única célula. Ela irá processar todos os dados, separar os tipos de assistência (EPI/FULL e AE), formatar as datas, extrair os horários e calcular o dia da semana automaticamente.

---

### **Passo 1: Prepare sua Planilha**

1.  Abra a sua planilha Google Sheets que recebe as respostas do formulário.
2.  Clique no ícone `+` no canto inferior esquerdo para **adicionar uma nova aba**.
3.  Renomeie esta nova aba para `Agenda Final` (ou o nome que preferir).
4.  Na primeira linha (linha 1) desta nova aba, cole os seguintes cabeçalhos nas suas respectivas células:
    *   `A1`: **ID**
    *   `B1`: **Data**
    *   `C1`: **Dia da Semana**
    *   `D1`: **Horário**
    *   `E1`: **Tipo de Assistência**
    *   `F1`: **Participante**
    *   `G1`: **Coach**

### **Passo 2: Insira a Fórmula Mágica**

1.  Clique na célula **`A2`** (logo abaixo do cabeçalho "ID") da sua aba `Agenda Final`.
2.  Copie a fórmula inteira abaixo e cole-a na célula `A2`.

```excel
=LET(
    -- CONFIGURAÇÃO --
    respostas_sheet, 'Página de respostas 1'!A2:M,

    -- DADOS FONTES --
    participantes, CHOOSECOLS(respostas_sheet, 2),
    coaches, CHOOSECOLS(respostas_sheet, 3),
    epi_full_selections, CHOOSECOLS(respostas_sheet, 5, 6, 7, 8, 9, 10, 11, 12),
    ae_selections, CHOOSECOLS(respostas_sheet, 13),

    -- 1. PROCESSAR DADOS EPI/FULL --
    epi_full_flat, FLATTEN(
        IF(epi_full_selections = "",,
            participantes & "♦" & coaches & "♦" & SPLIT(epi_full_selections, ", ")
        )
    ),
    epi_full_split, SPLIT(FILTER(epi_full_flat, epi_full_flat <> ""), "♦"),

    epi_full_processed, ARRAYFORMULA(
        IFERROR(
            HSTACK(
                -- Data --
                DATEVALUE(
                    REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), "(\d{1,2}/\d{1,2})") & "/" &
                    IF(VALUE(REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), "/(\d{1,2})"))=12, 2024, 2025)
                ),
                -- Horário --
                REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), " - (.*)"),
                -- Tipo de Assistência --
                "EPI/FULL",
                -- Participante --
                CHOOSECOLS(epi_full_split, 1),
                -- Coach --
                CHOOSECOLS(epi_full_split, 2)
            )
        )
    ),

    -- 2. PROCESSAR DADOS AE --
    ae_selections_clean, IF(ae_selections = "",, REGEXREPLACE(ae_selections, "\n", ",")),
    ae_flat, FLATTEN(
        IF(ae_selections_clean = "",,
            participantes & "♦" & coaches & "♦" & SPLIT(ae_selections_clean, ",")
        )
    ),
    ae_split, SPLIT(FILTER(ae_flat, ae_flat <> ""), "♦"),

    ae_processed, ARRAYFORMULA(
        IFERROR(
            HSTACK(
                -- Data --
                DATEVALUE(REGEXEXTRACT(TRIM(CHOOSECOLS(ae_split, 3)), "(.*) - ")),
                -- Horário --
                REGEXEXTRACT(TRIM(CHOOSECOLS(ae_split, 3)), " - (.*)"),
                -- Tipo de Assistência --
                "AE",
                -- Participante --
                CHOOSECOLS(ae_split, 1),
                -- Coach --
                CHOOSECOLS(ae_split, 2)
            )
        )
    ),

    -- 3. COMBINAR E ORGANIZAR --
    all_data, VSTACK(epi_full_processed, ae_processed),
    all_data_clean, QUERY(all_data, "SELECT * WHERE Col1 IS NOT NULL"),
    sorted_data, QUERY(all_data_clean, "ORDER BY Col1, Col5, Col4"),

    -- 4. MONTAR TABELA FINAL --
    data_final, CHOOSECOLS(sorted_data, 1),

    HSTACK(
        SEQUENCE(ROWS(sorted_data)),
        data_final,
        TEXT(data_final, "dddd"),
        CHOOSECOLS(sorted_data, 2), -- Horário
        CHOOSECOLS(sorted_data, 3), -- Tipo
        CHOOSECOLS(sorted_data, 4), -- Participante
        CHOOSECOLS(sorted_data, 5)  -- Coach
    )
)
```

**Importante:** Pressione **Enter**. A planilha pode demorar um momento para processar, mas logo toda a sua agenda aparecerá formatada corretamente a partir da célula `A2`.

---

### **Como a Fórmula Funciona e Como Ajustá-la**

Você só precisa se preocupar com a seção **`-- CONFIGURAÇÃO --`** no início da fórmula se algo mudar no seu formulário.

`respostas_sheet, 'Página de respostas 1'!A2:M,`

*   **`'Página de respostas 1'`**: Este é o nome da aba que recebe as respostas do formulário. Se o seu tiver um nome diferente (ex: `'Respostas ao formulário 1'`), **altere-o aqui**.
*   **`A2:M`**: Este é o intervalo de colunas que a fórmula irá ler.
    *   `A2` significa que a fórmula começa a ler da segunda linha (para ignorar os cabeçalhos).
    *   `M` é a última coluna com dados (`Qual a data e horário de suas AEs?...`). Se você adicionar mais perguntas que gerem novas colunas, precisará ajustar `M` para a nova última letra da coluna.

O resto da fórmula cuida de tudo:
1.  **Processa EPI/FULL:** Pega todas as seleções das colunas semanais, desmembra-as, e formata os dados.
2.  **Processa AE:** Pega os dados da última coluna, desmembra-os, e formata.
3.  **Combina e Organiza:** Junta os dois tipos de agendamento e ordena por data.
4.  **Monta a Tabela Final:** Adiciona o ID sequencial e a coluna "Dia da Semana" calculada.

Sua `Agenda Final` será atualizada automaticamente sempre que uma nova resposta chegar no formulário.