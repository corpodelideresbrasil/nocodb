# Guia da Fórmula Avançada para Agendamentos (Versão Corrigida)

Olá! Peço desculpas pelo erro na versão anterior. A causa mais provável são as configurações de localidade da sua planilha, que podem interferir na interpretação de datas.

Preparei uma **versão mais robusta e universal** da fórmula que não depende dessas configurações. Ela extrai manualmente cada componente da data (dia, mês, ano) e a reconstrói, garantindo que funcione em qualquer planilha.

---

### **Passo 1: Prepare sua Planilha**

1.  Abra a sua planilha Google Sheets que recebe as respostas do formulário.
2.  Se já tiver uma aba `Agenda Final`, **limpe a célula `A2`** onde a fórmula anterior estava.
3.  Se ainda não tiver, crie a aba `Agenda Final` e adicione os seguintes cabeçalhos na primeira linha:
    *   `A1`: **ID**
    *   `B1`: **Data**
    *   `C1`: **Dia da Semana**
    *   `D1`: **Horário**
    *   `E1`: **Tipo de Assistência**
    *   `F1`: **Participante**
    *   `G1`: **Coach**

### **Passo 2: Insira a Nova Fórmula Robusta**

1.  Clique na célula **`A2`** da sua aba `Agenda Final`.
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
                -- Data (Lógica Robusta) --
                DATE(
                    IF(VALUE(REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), "/(\d{1,2})"))=12, 2024, 2025), -- Ano
                    VALUE(REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), "/(\d{1,2})")), -- Mês
                    VALUE(REGEXEXTRACT(CHOOSECOLS(epi_full_split, 3), "(\d{1,2})/\d{1,2}")) -- Dia
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
                -- Data (Lógica Robusta) --
                DATE(
                    2000 + VALUE(REGEXEXTRACT(TRIM(CHOOSECOLS(ae_split, 3)), "\/(\d{2}) -")), -- Ano
                    VALUE(REGEXEXTRACT(TRIM(CHOOSECOLS(ae_split, 3)), "\/(\d{2})\/")), -- Mês
                    VALUE(REGEXEXTRACT(TRIM(CHOOSECOLS(ae_split, 3)), "(\d{2})\/")) -- Dia
                ),
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

**Importante:** Pressione **Enter**. Esta versão é muito mais resiliente a diferenças de formatação e deve funcionar corretamente.

---

### **Como Ajustar a Nova Fórmula**

A lógica de ajuste permanece a mesma. Se precisar modificar o intervalo de dados, altere apenas a seção de **`-- CONFIGURAÇÃO --`**:

`respostas_sheet, 'Página de respostas 1'!A2:M,`

*   **`'Página de respostas 1'`**: Altere se o nome da sua aba de respostas for diferente.
*   **`A2:M`**: Altere a letra da coluna final (`M`) se você adicionar mais perguntas ao seu formulário.

Espero que agora funcione perfeitamente!
