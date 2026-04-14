# Integração Telegram Beta (AnythingLLM + Godfather)

Esta documentação descreve como ativar o bot do Telegram para os alunos do TDS.

## 1. Criando o Bot (Godfather)
1. No Telegram, procure pelo `@BotFather`.
2. Use o comando `/newbot` e siga os passos para obter o **API Token**.
3. Guarde este token com segurança.

## 2. Configurando no AnythingLLM
1. Acesse seu painel do AnythingLLM (`rag.ipexdesenvolvimento.cloud`).
2. Vá em **Settings -> Live Chat**.
3. Selecione a aba **Telegram**.
4. Insira o **Token** obtido no BotFather.
5. Em **Workspace Mapping**, selecione o workspace `tds`.
6. Ative o bot.

## 3. Vínculo com o Aluno
Para que o sistema saiba quem é o aluno no Telegram:
- O aluno deve acessar o Portal Web.
- Clicar no botão "Vincular Telegram".
- Informar seu `@username` ou ID.

## 4. Comandos Suportados (Beta)
- `/start`: Inicia a conversa com o Tutor IA.
- `/reset`: Limpa o histórico da sessão atual.
- Qualquer pergunta: A IA responderá usando o contexto do curso vinculado.

---
**Nota Técnica:** O AnythingLLM gerencia a fila de mensagens e o histórico. O nosso backend (`lms_lite_api`) serve apenas para auditoria e gestão de permissões.
