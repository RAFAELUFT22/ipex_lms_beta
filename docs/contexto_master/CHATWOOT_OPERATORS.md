# Configuração do Chatwoot — Contas de Operadores

## Objetivo

Configurar o Chatwoot como central de atendimento humano para o ecossistema
TDS, com operadores segmentados por tenant (parceiro institucional).

---

## 1. Arquitetura de Atendimento

```
Aluno (WhatsApp)
      |
Evolution API (recebe mensagem)
      |
n8n (classifica a conversa)
      |
      ├── Assunto acadêmico? → AnythingLLM (bot responde)
      |
      └── Solicita humano / bot não sabe? → Chatwoot (operador assume)
                                                 |
                                           Operador responde
                                                 |
                                           n8n retorna ao bot
```

---

## 2. Estrutura de Contas no Chatwoot

### Hierarquia de Roles

| Role | Permissões | Quem ocupa |
| :--- | :--- | :--- |
| `administrator` | Acesso total, configurações globais | Equipe TDS / Kreativ |
| `agent` | Atende conversas, não altera configurações | Operadores dos parceiros |

### Contas a criar por tenant

Cada parceiro institucional deve ter **pelo menos 2 operadores**:

```
Tenant: TDS / IPEX
├── operador1@ipex.edu.br  (role: agent) — Atendimento principal
├── operador2@ipex.edu.br  (role: agent) — Backup
└── admin@kreativ.com.br   (role: administrator) — Supervisão geral
```

---

## 3. Passo a Passo de Configuração

### 3.1 Criar conta no Chatwoot

```
Dashboard Chatwoot → Settings → Agents → Invite Agent
- Email: operador@parceiro.com.br
- Nome: Nome do Operador
- Role: agent
```

O operador recebe e-mail de convite para definir senha.

### 3.2 Criar Inbox (Canal de Entrada)

Cada número de WhatsApp do parceiro = 1 inbox separada:

```
Settings → Inboxes → Add Inbox
- Channel Type: API (integração via Evolution API)
- Nome: "WhatsApp TDS [Parceiro]"
- Anotar o API Access Token gerado
```

### 3.3 Conectar Evolution API ao Chatwoot

No painel da Evolution API, configurar o webhook da instância:

```json
{
  "webhook": {
    "url": "https://chatwoot.seuservidor.com/api/v1/accounts/1/inboxes/{INBOX_ID}/events",
    "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"]
  }
}
```

Ou via n8n: o nó de transbordo faz POST para a API do Chatwoot:

```http
POST /api/v1/accounts/{account_id}/conversations
Authorization: user_access_token {TOKEN_OPERADOR}
{
  "inbox_id": 1,
  "contact_id": "{ID_CONTATO}",
  "assignee_id": "{ID_OPERADOR_DISPONIVEL}"
}
```

### 3.4 Criar Labels (Etiquetas) por Tenant

```
Settings → Labels → Add Label
- tds-ipex       (azul)
- tds-fapto      (verde)
- aguardando-bot (cinza)
- urgente        (vermelho)
```

O n8n aplica automaticamente a label do tenant ao criar a conversa.

### 3.5 Configurar Respostas Rápidas (Canned Responses)

```
Settings → Canned Responses → Add Canned Response
```

Exemplos essenciais:

| Atalho | Mensagem |
| :--- | :--- |
| `/boas-vindas` | Olá! Sou [Nome], do suporte TDS. Como posso ajudar? |
| `/certificado` | Seu certificado é emitido automaticamente ao concluir todos os quizzes. Você pode baixá-lo em: [link] |
| `/prazo` | Os cursos não têm prazo fixo. Você pode estudar no seu ritmo! |
| `/problema-tecnico` | Entendido! Vou registrar e retorno em até 24h. |

---

## 4. Regras de Transbordo (n8n → Chatwoot)

O n8n deve transferir para o Chatwoot quando:

1. O aluno digita **"falar com humano"** / **"atendente"** / **"suporte"**
2. O bot do AnythingLLM retorna `confidence_score < 0.4`
3. O aluno envia mensagem de voz (áudio)
4. O aluno envia imagem ou documento

### Regra de retorno ao bot:
Após o operador fechar a conversa no Chatwoot, o n8n detecta o evento
`conversation_resolved` via webhook e reativa o fluxo automático para aquele contato.

---

## 5. Variáveis de Ambiente Necessárias (n8n)

| Chave | Descrição |
| :--- | :--- |
| `CHATWOOT_URL` | `https://chatwoot.seuservidor.com` |
| `CHATWOOT_API_KEY` | Token de acesso do usuário administrador |
| `CHATWOOT_ACCOUNT_ID` | ID numérico da conta (ver na URL do dashboard) |
| `CHATWOOT_INBOX_TDS` | ID da inbox do canal WhatsApp TDS principal |

---

## 6. Checklist de Verificação

- [ ] Operadores criados e convites aceitos
- [ ] Inbox conectada à Evolution API (mensagens chegam no Chatwoot)
- [ ] Labels configuradas por tenant
- [ ] Canned responses cadastradas
- [ ] Webhook do Chatwoot → n8n configurado (evento `conversation_resolved`)
- [ ] Teste de transbordo: digitar "falar com humano" no WhatsApp e verificar
      se a conversa aparece no Chatwoot atribuída ao operador correto
