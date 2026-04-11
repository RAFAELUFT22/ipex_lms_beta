# Prompt de Apoio - Lapidação Final com Claude

Copie e cole o texto abaixo em uma conversa com o Claude (ou na ferramenta assistente de sua preferência) logo após implantar e testar o ecossistema (N8N, Evolution, Chatwoot, AnythingLLM, OpenRouter). Este prompt o ajudará a preencher eventuais lacunas e melhorar o fluxo conversacional final:

---
**PROMPT:**

`Olá Claude! Acabei de implantar minha arquitetura completa de atendimento educacional do Projeto TDS (*Produção Audiovisual*). A pilha de tecnologia atual tem:`
`- **Evolution API:** cuidando dos Webhooks do WhatsApp Cloud/QR Code.`
`- **Chatwoot:** como CRM para que os suportes/tutores humanos loguem com as suas contas e atendam os alunos na Inbox.`
`- **N8N:** orchestrando a triagem. O N8N manda as dúvidas dos alunos para o **AnythingLLM** e permite o "hand-off" (transferência para o Chatwoot) caso o bot não saiba responder.`
`- **AnythingLLM (RAG com OpenRouter/Llama-3):** responde com base em um documento atualizado.`
`- **Portal LMS Lite:** exibe o progresso e chama a emissão automática do N8N para certificados HTML.`

`Tudo está funcionalmente ligado, mas preciso da sua ajuda para *lapidar as lacunas* em 3 frentes:`

`1. **Regras de Negócio do RAG:** Como posso estruturar o *documento de contexto base* em TXT ou PDF (o que injeto no AnythingLLM) para garantir que o bot sempre saiba como instruir o aluno na "Produção Audiovisual", mas sempre sugira o "Falar com suporte" quando a dúvida for sobre cronogramas exatos não listados? Crie um template do system prompt ou desse PDF inicial.`

`2. **Linguagem e Tom de Voz no N8N:** Os retornos em caso de "Aluno não autorizado" e as mensagens de "Transferindo para atendente..." no fluxo do N8N podem parecer mecânicas. Crie textos breves e acolhedores, usando emojis educacionais, para eu substituir nos nós de 'Respond Webhook / HTTP Request' da resposta do bot.`

`3. **Dicas Operacionais de Atendimento:** Dê de 3 a 5 diretrizes rápidas (exemplo de labels, status resolvido/pendente) para treinar minha equipe humana a usar o **Chatwoot** de forma alinhada a esse fluxo onde o bot "mutou" (handoff) e eles precisam "retomar o bot" fechando a conversa.`

`Responda em formato Markdown, focando na aplicabilidade imediata do meu contexto de Produção Audiovisual.`

---

⭐ **Por que usar este prompt?**
Como o setup estrutural foi concluído, a melhor habilidade do LLM (Claude) agora é atuar como seu **Designer Conversacional**. Ele montará o esqueleto do texto RAG, de forma que o AnyhtingLLM faça roteamentos suaves e sua equipe saiba exatamente onde clicar no Chatwoot.
