# Guia Rápido: Resolvendo o Erro de "Excesso de Redirecionamentos"

Olá! O erro `ERR_TOO_MANY_REDIRECTS` (ou similar) é um problema comum e frustrante ao acessar algumas ferramentas do Google, como o Apps Script. **A boa notícia é que não é um erro no script**, mas sim um conflito de autenticação no seu navegador.

A causa quase sempre é estar logado em **múltiplas contas Google** ao mesmo tempo no mesmo navegador.

Siga as soluções abaixo, começando pela mais rápida e provável.

---

### **Solução 1: A Mais Rápida - Usar uma Janela Anônima (ou Privada)**

Esta é a forma mais eficaz e rápida de contornar o problema sem alterar suas configurações.

1.  Abra uma **nova janela anônima** no seu navegador:
    *   **Chrome:** `Ctrl + Shift + N`
    *   **Firefox:** `Ctrl + Shift + P`
    *   **Edge:** `Ctrl + Shift + N`
2.  Nesta nova janela anônima, acesse sua planilha do Google Sheets.
3.  Faça login **apenas na conta Google** que tem acesso à planilha.
4.  Vá em **Extensões > Apps Script**.

O editor de scripts deve abrir sem nenhum erro. Depois de colar o código e configurar o gatilho, você pode fechar a janela anônima e voltar a usar seu navegador normalmente.

---

### **Solução 2: Sair de Todas as Contas Secundárias**

Se preferir não usar a janela anônima, a alternativa é garantir que você está logado em apenas uma conta na sua sessão normal do navegador.

1.  Vá para a página inicial do [Google](https://www.google.com).
2.  Clique no ícone do seu perfil no canto superior direito.
3.  No menu que aparece, clique em **"Sair de todas as contas"**.
4.  Depois de deslogado, faça login novamente **apenas com a conta principal** que você usa para a planilha.
5.  Tente acessar o editor de scripts novamente.

---

### **Solução 3: Limpar os Cookies do Navegador**

Se nenhuma das opções acima funcionar, limpar os cookies do Google pode resolver o problema de forma mais definitiva.

1.  Vá para as configurações de privacidade do seu navegador.
2.  Procure pela opção de limpar dados de navegação ou gerenciar dados de sites.
3.  Encontre e remova os cookies associados a `google.com` e `accounts.google.com`.
4.  **Atenção:** Isso pode te deslogar de vários serviços Google.
5.  Após a limpeza, feche o navegador, abra-o novamente e faça login apenas com a conta necessária.

---

A **Solução 1 (Janela Anônima)** é a mais recomendada por ser rápida e não interferir com seu ambiente de trabalho normal. Por favor, tente-a primeiro e me informe se conseguir acessar o editor.