# 🤖 Manual de Gerenciamento da IA — Projeto TDS

Este guia explica como controlar o comportamento do seu Tutor Cognitivo (Bot WhatsApp) utilizando a infraestrutura atual (AnythingLLM + OpenRouter + n8n).

---

## 1. Alterando o Comportamento (Personalidade)
O "cérebro" do robô é o Workspace do **AnythingLLM**. Para mudar o modo como ele responde:

1.  Aponte seu navegador para: `https://rag.ipexdesenvolvimento.cloud`
2.  Acesse o workspace **`tds`** (ou o workspace que você estiver usando para os cursos).
3.  Clique em **"Workspace Settings"** (ícone de engrenagem no canto inferior esquerdo do workspace).
4.  Procure pelo campo **"System Prompt"** (ou "Instructions").
5.  **Exemplo de Comando:**
    > "Você é o Tutor Cognitivo do Projeto TDS. Sua missão é auxiliar beneficiários do Tocantins. Use uma linguagem simples, acolhedora e evite termos técnicos complicados. Se o aluno não entender, use analogias com o dia a dia do campo ou da cidade dele."
6.  Clique em **Save**. O bot mudará de comportamento imediatamente no WhatsApp.

---

## 2. Alimentando o RAG (Conteúdo)
Para que o bot saiba responder sobre novos cursos ou regras do MDS:

1.  Acesse o workspace no AnythingLLM.
2.  Faça o upload de documentos (PDF, DOCX, TXT) ou URLs na área de **"Upload"**.
3.  **Importante:** Após o upload, selecione os documentos e clique em **"Move to Workspace"** e depois em **"Save and Embed"**.
4.  Agora o robô usará essas informações para responder às perguntas dos alunos.

---

## 3. Configurando o OpenRouter
Para garantir que o bot use a sua chave do OpenRouter (mais rápida e inteligente):

1.  No AnythingLLM, vá em **"Settings"** (ícone de engrenagem no menu lateral principal).
2.  Selecione **"LLM Provider"**.
3.  Escolha **"OpenRouter"**.
4.  Insira sua chave: `sk-or-v1-d0a332de7...da70dc17` (Copie do seu arquivo `.env.real`).
5.  Selecione o modelo desejado (Recomendado: `google/gemini-flash-1.5` ou `deepseek/deepseek-chat`).

---

## 4. Filtrando o "Raciocínio" da IA (Filtro `<think>`)
Se você usar modelos como o DeepSeek, ele pode enviar mensagens estranhas começando com `<think>`. Para resolver isso no n8n:

1.  Abra seu workflow no n8n (Ex: **Kreativ TDS — Chatwoot RAG Flow**).
2.  **Antes** do nó que envia a mensagem para o Chatwoot/WhatsApp, adicione um nó do tipo **"Code"**.
3.  Escolha a opção **"Run Code Once for All Items"**.
4.  Cole o seguinte código:

```javascript
for (const item of $input.all()) {
  const raw = item.json.textResponse || "";
  // Remove tudo entre as tags <think> e </think>
  item.json.response_clean = raw.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
}
return $input.all();
```

5.  No nó seguinte (Chatwoot/WhatsApp), troque a variável que envia o texto para usar o novo campo `response_clean`.

---

> [!TIP]
> **Dica de Ouro:** Se o bot estiver "alucinando", adicione no System Prompt: "Responda apenas com base nos documentos fornecidos. Se não souber a resposta, peça para o aluno aguardar um tutor humano."
