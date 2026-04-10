# TDS — Catraca Pedagógica Genérica + Chatbot Audiovisual

**Data:** 2026-04-10
**Aprovado por:** Rafael Luciano (admin@neruds.org)
**Contexto:** Sistema TDS em produção — `https://lms.ipexdesenvolvimento.cloud` / `https://n8n.ipexdesenvolvimento.cloud`
**Abordagem:** C — Catraca genérica para todos os cursos (um workflow, múltiplos cursos)

---

## 1. Problema e Objetivo

O sistema TDS precisa entregar conteúdo pedagógico estruturado (leitura + quiz MCQ) via WhatsApp para beneficiários CadÚnico. Em vez de criar um workflow N8N por curso, implementar um único workflow genérico que serve todos os 7 cursos via keyword trigger.

**Login:** verificação por número de telefone (lookup no TDS Aluno) sem senha nesta fase.

---

## 2. Arquitetura Geral

```
WhatsApp (inbox 5, +351932439344)
    → Chatwoot
        → N8N: Enrollment Gateway (xRyfmH3HTSKGSirt)
              │
              ├── mensagem normal → RAG Flow (existente)
              │
              └── começa com "/" → Catraca Router
                                        │
                                        ├── /audiovisual ──┐
                                        ├── /agricultura  ──┤
                                        ├── /financas    ──┤  → TDS — Catraca Pedagógica (novo)
                                        ├── /educacao    ──┤        │
                                        ├── /associa     ──┤        ├── lookup TDS Aluno (Frappe)
                                        ├── /ia          ──┤        ├── carrega JSON do curso
                                        └── /sim         ──┘        ├── executa state machine
                                                                     ├── atualiza TDS Aluno (Frappe)
                                                                     └── responde via Chatwoot
```

**Dois workflows ativos:**
1. `xRyfmH3HTSKGSirt` — Enrollment Gateway v2 (existente, recebe update de roteamento)
2. `[novo]` — TDS — Catraca Pedagógica (criado nesta fase)

---

## 3. Sistema de Login (Verificação por Número)

- Quando aluno envia `/[keyword]`, o Gateway extrai o número de telefone do payload Chatwoot
- Faz lookup no Frappe: `GET /api/resource/TDS Aluno?filters=[["whatsapp","=","+55XXXXXXXXXXX"]]`
- **Encontrado** → prossegue para a catraca do curso
- **Não encontrado** → responde: "Você ainda não está inscrito no TDS. Acesse: lms.ipexdesenvolvimento.cloud/guia-aluno ou envie mensagem para iniciar seu cadastro."
- Sem senha nesta fase — o número de telefone é o único fator de autenticação

---

## 4. Máquina de Estados

Estado armazenado nos campos `estado_catraca`, `modulo_atual`, `secao_atual`, `respostas_mcq`, `modulos_concluidos`, `curso_ativo` no TDS Aluno (Frappe).

```
/[keyword] recebido
    │
    ├── aluno NÃO encontrado → orientação + link guia-aluno
    │
    └── aluno encontrado
            │
            ├── estado = inativo | curso_ativo diferente
            │       → se curso_ativo diferente e estado != inativo:
            │           → "Você está no curso [curso_atual]. Para trocar para [novo], responda SIM."
            │           → aguarda confirmação → se sim: reinicia no novo curso
            │           → se não: continua no curso atual
            │       → se inativo: "Bem-vindo ao curso [nome]! Vou guiar você pelo módulo 1."
            │       → set: estado=aguardando_leitura, modulo=1, secao=1, curso_ativo=[keyword]
            │
            ├── estado = aguardando_leitura
            │       → envia texto da seção atual
            │       → aguarda confirmação: "li|ok|pronto|entendi|sim|certo|combinado|feito|lido|claro"
            │       → confirmado → set estado=aguardando_mcq
            │       → não confirmado → reenvia seção (sem punição)
            │
            ├── estado = aguardando_mcq
            │       → envia pergunta + opções A / B / C / D
            │       → recebe A|B|C|D → registra em respostas_mcq (qualquer resposta vale)
            │       → tem próxima seção? → aguardando_leitura (secao+1)
            │       → fim do módulo? → modulo_completo
            │       → não é A/B/C/D → passa para RAG (AnythingLLM workspace do curso)
            │
            ├── estado = modulo_completo
            │       → "Parabéns! Você concluiu o Módulo [N] — [titulo]!"
            │       → tem próximo módulo? → aguardando_leitura (modulo+1, secao=1)
            │       → fim do curso? → trigger certificado → certificado_emitido
            │
            ├── estado = certificado_emitido
            │       → "Você já concluiu este curso! Seu certificado: lms.../lms/certification/[id]"
            │
            └── QUALQUER estado + handoff trigger → transbordo humano (fluxo existente)
```

**Palavras de confirmação de leitura:** `li|ok|pronto|entendi|sim|certo|combinado|feito|lido|claro`

**Palavras de handoff (já no N8N):** `tutor|prova|exame|humano|operador|atendente|reclamação|ajuda humana|falar com alguém|não consigo|problema técnico`

---

## 5. Campo Novo no TDS Aluno

| Campo | Tipo Frappe | Descrição |
|---|---|---|
| `curso_ativo` | Data | Keyword do curso em andamento (`audiovisual`, `agricultura`, etc.) |

Os demais campos (`estado_catraca`, `modulo_atual`, `secao_atual`, `respostas_mcq`, `modulos_concluidos`, `data_ultimo_acesso_whatsapp`) já foram especificados no design de 2026-04-09.

Criação via `POST /api/resource/DocType` com `Authorization: token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}`.

---

## 6. Estrutura JSON dos Cursos (node Set no N8N)

```json
{
  "audiovisual": {
    "nome": "Audiovisual e Produção de Conteúdo Digital",
    "workspace_slug": "tds-audiovisual-e-conteudo",
    "modulos": [
      {
        "titulo": "Módulo 1 — [título a preencher]",
        "secoes": [
          {
            "texto": "[texto da seção — a preencher com cartilha]",
            "pergunta": "[pergunta MCQ]",
            "opcoes": {
              "A": "[opção A]",
              "B": "[opção B]",
              "C": "[opção C]",
              "D": "[opção D]"
            }
          }
        ]
      }
    ]
  },
  "agricultura": {
    "nome": "Agricultura Sustentável — SAFs",
    "workspace_slug": "tds-agricultura-sustentavel",
    "modulos": []
  },
  "financas": {
    "nome": "Finanças e Empreendedorismo",
    "workspace_slug": "tds-financas-e-empreendedorismo",
    "modulos": []
  },
  "educacao": {
    "nome": "Educação Financeira Melhor Idade",
    "workspace_slug": "tds-educacao-financeira-terceira-idade",
    "modulos": []
  },
  "associa": {
    "nome": "Associativismo e Cooperativismo",
    "workspace_slug": "tds-associativismo-e-cooperativismo",
    "modulos": []
  },
  "ia": {
    "nome": "IA no meu Bolso",
    "workspace_slug": "tds-ia-no-meu-bolso",
    "modulos": []
  },
  "sim": {
    "nome": "SIM — Serviço de Inspeção Municipal",
    "workspace_slug": "tds-sim",
    "modulos": []
  }
}
```

**Nota:** O conteúdo dos módulos (texto + MCQs) do curso Audiovisual deve ser fornecido por Rafael/equipe pedagógica. Os demais cursos ficam com `modulos: []` para expansão futura.

---

## 7. Nodes do Workflow "TDS — Catraca Pedagógica"

```
[Execute Workflow trigger]          ← chamado pelo Enrollment Gateway
    │
    ▼
[Set: Cursos JSON]                  ← JSON completo de todos os cursos
    │
    ▼
[HTTP Request: GET TDS Aluno]       ← lookup por whatsapp no Frappe
    │
    ├── 404 / lista vazia
    │       ▼
    │   [Set: msg orientação]
    │       ▼
    │   [HTTP: Chatwoot send message]
    │
    └── encontrado
            ▼
        [Set: extrai campos do aluno]
            ▼
        [Switch: estado_catraca]
            │
            ├── inativo/novo ──→ [Set: inicializa estado] → [HTTP: PATCH TDS Aluno] → [Chatwoot: boas-vindas + seção 1]
            │
            ├── aguardando_leitura
            │       ▼
            │   [IF: mensagem é confirmação?]
            │       ├── sim → [Set: avança para MCQ] → [HTTP: PATCH] → [Chatwoot: pergunta MCQ]
            │       └── não → [Chatwoot: reenvia texto da seção]
            │
            ├── aguardando_mcq
            │       ▼
            │   [IF: mensagem é A/B/C/D?]
            │       ├── sim → [Set: registra resposta + calcula próximo estado]
            │       │           → [HTTP: PATCH TDS Aluno]
            │       │           → [IF: fim de curso?]
            │       │               ├── sim → [HTTP: POST LMS Certificate] → [Chatwoot: certificado]
            │       │               └── não → [Chatwoot: próxima seção ou parabéns módulo]
            │       └── não → [HTTP: GET AnythingLLM RAG] → [Chatwoot: resposta RAG]
            │
            └── certificado_emitido
                    ▼
                [Chatwoot: "Curso concluído! Certificado: [url]"]
```

**Total estimado:** ~22 nodes.

---

## 8. Certificado

1. N8N faz `POST /api/resource/LMS Certificate` no Frappe com `member`, `course`, `issue_date`
2. Frappe retorna o ID do certificado
3. N8N envia via Chatwoot: `"🎓 Parabéns [nome]! Seu certificado está disponível em: lms.ipexdesenvolvimento.cloud/lms/certification/[id]"`

Template customizado (glassmorphism) fica para fase posterior.

---

## 9. Alteração no Enrollment Gateway

Adicionar no início do workflow `xRyfmH3HTSKGSirt` (antes do roteador atual):

```
[IF: mensagem começa com "/"]
    ├── sim → [Set: extrai keyword (ex: "audiovisual" de "/audiovisual")]
    │           → [Execute Workflow: TDS — Catraca Pedagógica]
    └── não → fluxo atual (RAG / enrollment)
```

---

## 10. Escopo

### No escopo
- Campo `curso_ativo` no TDS Aluno (Frappe API)
- Campos catraca no TDS Aluno (6 campos do design 09/04/2026)
- Workflow N8N "TDS — Catraca Pedagógica" (~22 nodes)
- Roteamento `/[keyword]` no Enrollment Gateway
- JSON de todos os 7 cursos (conteúdo Audiovisual a ser fornecido pela equipe)
- RAG fallback para perguntas livres via AnythingLLM workspace por curso
- Emissão de certificado via Frappe LMS API (template padrão)

### Fora do escopo
- Senha/PIN de login (fase futura)
- Template de certificado customizado (glassmorphism)
- Conteúdo pedagógico dos outros 6 cursos (só Audiovisual nesta fase)
- Portal web de progresso
- Catraca para visitantes não matriculados

---

## 11. Dependências

```
1. Criar campo curso_ativo no TDS Aluno (Frappe API)
2. Criar campos catraca (6 campos) no TDS Aluno — se ainda não criados
3. Obter conteúdo pedagógico Audiovisual (módulos + MCQs) com equipe
4. Criar workflow TDS — Catraca Pedagógica no N8N
5. Atualizar Enrollment Gateway com roteamento por "/"
6. Testar: aluno 63999374165 envia /audiovisual
```
