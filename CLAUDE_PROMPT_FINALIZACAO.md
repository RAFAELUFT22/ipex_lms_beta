## Copie e cole o texto abaixo exatamente como está no seu Claude Code Web / Terminal:

```text
Olá Claude! Eu criei um grupo no WhatsApp (https://chat.whatsapp.com/ImWI77LFmbIElp4S8mB6Wm) com as minhas duas contas conectadas no Evolution API (a normal e a Cloud API). Nosso objetivo é finalizar a implantação do bot "Kreativ TDS" usando N8N, Evolution API e AnythingLLM. 

Aqui estão as suas tarefas para agir diretamente na minha VPS para 'lapidar as lacunas':

1. **Atualizar o System Prompt do AnythingLLM via API:**
Acesse o banco de dados do meu AnythingLLM (`producao-audiovisual` ou `tds-audiovisual-e-conteudo`) via API local (porta 3001) e atualize o `openAiPrompt` (Sistema) para que ele aja como um tutor interativo do grupo. Ele deve focar em economizar tokens, ser altamente didático e sempre instruir que os comandos corretos no grupo são `/ajuda` e `/tds [pergunta]`. Use o seu melhor conhecimento de RAG para criar este "System Prompt" infalível.

2. **Forçar a Importação do Workflow do N8N:**
Existe um JSON atualizado em `/root/projeto-tds/n8n-workflows/tds-auth-rag-flow.json` com toda a lógica de roteamento de grupos (IF Comandos /ajuda e /tds). Use comandos Docker para importar/sobrescrever esse workflow no container `kreativ-n8n`, ativá-lo pelo banco de dados ou me dar um comando cURL direto na API do N8N local que faça o deploy ativado automaticamente.

3. **Verificar os Webhooks da Evolution API:**
Consulte o container `kreativ-evolution` (porta 8080) e garanta que a instância `tds_suporte_audiovisual` está roteando tudo perfeitamente para o N8N (url do webhook) e ignorando confirmações de leitura soltas (para não gastar processamento do N8N).

4. **Teste de Validação:**
Simule via cURL um POST no webhook do N8N (whatsapp-kreativ) imitando uma mensagem que tenha o formato `/tds O que é Roteiro?` advinda de um grupo, e verifique se o fluxo chega ao final (Evolution: Responder) com Status 200.

Pode executar esses passos autonomamente analisando as rotas da minha máquina! Quando finalizar, confirme para podermos mandar a primeira mensagem no grupo real!
```
