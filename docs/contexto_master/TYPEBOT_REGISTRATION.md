# Fluxo de Matrícula via Typebot — Sem Risco de Perda de Dados

## Por que Typebot e não Google Forms?

| Critério | Google Forms | Typebot |
| :--- | :--- | :--- |
| Experiência conversacional | Não | Sim |
| Salva progresso parcial | Não | Sim (via webhook) |
| Pode ser embutido no WhatsApp | Não | Sim (link Typebot) |
| Lógica condicional | Limitada | Completa |
| Integração n8n | Manual | Webhook nativo |
| Risco de perda ao fechar | Alto | Baixo (salva a cada step) |

---

## Arquitetura Anti-Perda de Dados

```
Aluno abre o Typebot (link enviado via WhatsApp)
         |
         ↓
[Step 1] Telefone → POST /webhook/matricula/step
         | (dados salvos no banco como rascunho)
         ↓
[Step 2] Nome → POST /webhook/matricula/step
         | (atualiza rascunho)
         ↓
[Step 3] CPF → POST /webhook/matricula/step
         ↓
...
[Step N] Confirmação → POST /webhook/matricula/finalizar
         | (rascunho → registro oficial)
         ↓
n8n: envia boas-vindas + inicia tutoria no WhatsApp
```

**Princípio:** cada passo do formulário aciona um webhook n8n que grava
imediatamente no PostgreSQL. Se o aluno fechar, os dados já estão salvos.
Na próxima vez que abrir o link, o Typebot detecta o telefone e retoma.

---

## Tabela de Rascunho (PostgreSQL)

```sql
CREATE TABLE enrollment_drafts (
    id              SERIAL PRIMARY KEY,
    phone           VARCHAR(20) UNIQUE NOT NULL,  -- chave de retomada
    tenant_id       VARCHAR(50) DEFAULT 'tds_001',
    nome            VARCHAR(255),
    cpf             VARCHAR(14),
    data_nascimento DATE,
    municipio       VARCHAR(100),
    escolaridade    VARCHAR(50),
    renda_familiar  VARCHAR(50),
    curso_escolhido VARCHAR(100),
    nis_cadunico    VARCHAR(20),       -- NIS/CadÚnico (opcional)
    status          VARCHAR(20) DEFAULT 'rascunho',  -- rascunho | completo
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Fluxo Typebot — Passo a Passo

### Bloco 0 — Identificação (Anti-perda)

```
[Mensagem] Olá! Bem-vindo(a) ao Programa TDS 🌱
           Antes de começar, me diz seu número de WhatsApp
           com DDD (ex: 63 99999-9999):

[Input: Telefone]
    ↓
[Webhook n8n] GET /webhook/matricula/retomar?phone={telefone}
    ↓
Se registro existe → Mostrar resumo dos dados já salvos
                  → "Encontrei seu cadastro! Quer continuar de onde parou?"
                  → [Sim: ir para próximo step vazio] [Não: recomeçar]
Se não existe    → Continuar normalmente
```

### Bloco 1 — Apresentação do Programa

```
[Texto] O TDS é um programa gratuito de qualificação profissional.
        Você vai aprender, receber um certificado reconhecido
        e o melhor: no seu tempo, pelo celular. 📱

[Texto] Para garantir sua vaga e o certificado, preciso de
        algumas informações. Vou explicar pra que serve cada uma.

[Botão] Vamos começar! →
```

### Bloco 2 — Dados Pessoais

```
[Pergunta] Qual é o seu nome completo?
[Input: Texto longo]
[Webhook] POST /webhook/matricula/step {phone, nome}

[Pergunta] Qual é o seu CPF?
[Explicação] 💡 Precisamos do CPF para emitir o certificado pelo IPEX.
             Seus dados ficam protegidos e não são compartilhados.
[Input: CPF com máscara 000.000.000-00]
[Validação: 11 dígitos]
[Webhook] POST /webhook/matricula/step {phone, cpf}

[Pergunta] Qual é a sua data de nascimento?
[Input: Data DD/MM/AAAA]
[Webhook] POST /webhook/matricula/step {phone, data_nascimento}
```

### Bloco 3 — Localização

```
[Pergunta] Em qual município você mora?
[Input: Texto]
[Webhook] POST /webhook/matricula/step {phone, municipio}
```

### Bloco 4 — Perfil Socioeconômico

```
[Texto] 💡 As próximas perguntas são solicitadas pela FAPTO,
        que financia o programa. Elas comprovam que estamos
        chegando a quem mais precisa. Não afetam sua matrícula.

[Pergunta] Qual é a renda mensal da sua família?
[Opções Botão]
  → Até R$ 218 (extrema pobreza)
  → De R$ 218 a R$ 660 (pobreza)
  → De R$ 660 a R$ 2.640 (baixa renda)
  → Acima de R$ 2.640
  → Prefiro não informar
[Webhook] POST /webhook/matricula/step {phone, renda_familiar}

[Pergunta] Você tem NIS (número do CadÚnico)?
[Opções Botão] → Sim  → Não  → Não sei o número
[Se Sim]
  [Pergunta] Qual é o seu NIS? (11 dígitos)
  [Webhook] POST /webhook/matricula/step {phone, nis_cadunico}
```

### Bloco 5 — Escolha do Curso

```
[Texto] Agora a parte mais legal: escolha seu curso! 🎓

[Pergunta] Qual curso você quer fazer primeiro?
[Opções Botão — carregar da API n8n]
  → Gestão Financeira para Empreendimentos
  → Boas Práticas na Manipulação de Alimentos
  → Organização da Produção para o Mercado
  → Marketing Digital para Pequenos Negócios
[Webhook] POST /webhook/matricula/step {phone, curso_escolhido}
```

### Bloco 6 — Confirmação Final

```
[Texto] ✅ Perfeito! Aqui está o resumo do seu cadastro:

        👤 Nome: {nome}
        📋 CPF: {cpf}
        📍 Município: {municipio}
        📚 Curso: {curso_escolhido}

[Pergunta] As informações estão certas?
[Botões] → Sim, confirmar!  → Não, quero corrigir

[Se Sim]
  [Webhook] POST /webhook/matricula/finalizar {todos os dados}
  [Texto] 🎉 Sua matrícula foi confirmada!
          Em instantes você receberá uma mensagem no WhatsApp
          com o acesso ao seu curso. Bem-vindo(a) ao TDS!

[Se Não]
  → Voltar para o bloco correspondente ao campo que quer corrigir
```

---

## Webhook n8n — Lógica Anti-Perda

### Endpoint: `POST /webhook/matricula/step`

```javascript
// Nó Code no n8n
const { phone, ...fields } = $input.item.json;

// UPSERT — cria ou atualiza rascunho
await $db.query(`
  INSERT INTO enrollment_drafts (phone, ${Object.keys(fields).join(', ')}, updated_at)
  VALUES ($1, ${Object.keys(fields).map((_, i) => '$' + (i+2)).join(', ')}, NOW())
  ON CONFLICT (phone) DO UPDATE SET
  ${Object.keys(fields).map(k => `${k} = EXCLUDED.${k}`).join(', ')},
  updated_at = NOW()
`, [phone, ...Object.values(fields)]);

return { success: true };
```

### Endpoint: `POST /webhook/matricula/finalizar`

1. Atualiza `status = 'completo'` no rascunho
2. Insere na tabela `students` (oficial)
3. Envia mensagem de boas-vindas via **Chatwoot API** (WhatsApp Cloud API — Evolution API foi descartada)
   - `POST /api/v1/accounts/{id}/conversations` + `POST .../messages`
4. Cria contato no Chatwoot com tag do tenant (`tds-ipex`, `tds-fapto`, etc.)
5. Registra o aluno no workspace do AnythingLLM via `POST /api/v1/workspace/{slug}/thread`

---

## Deploy do Typebot

O Typebot pode ser:

| Modo | Uso |
| :--- | :--- |
| **Link direto** (typebot.io ou self-hosted) | Enviado via WhatsApp → aluno abre no browser |
| **Embutido no site** | iFrame na página de matrícula do portal Next.js |
| **WhatsApp nativo** | n8n simula o fluxo step-by-step dentro do próprio chat |

**Recomendação MVP:** Link enviado via WhatsApp + embutido no site.
O Typebot pode ser self-hosted no Dokploy (imagem: `baptistearno/typebot-builder`).
