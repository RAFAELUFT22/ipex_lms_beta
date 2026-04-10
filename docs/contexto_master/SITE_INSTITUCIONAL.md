# Site Institucional TDS — Estrutura de Conteúdo

## Objetivo

Página principal do portal (`/`) que explica o programa TDS aos parceiros
institucionais, alunos e ao público geral. Deve ser clara, objetiva e
converter visitantes em matrículas.

---

## 1. Seções da Home Page

### Hero (Topo)

```
┌─────────────────────────────────────────────────────────┐
│  [Logo TDS]                    [Acesse sua conta →]     │
│                                                         │
│  Transformação Digital          Inclua-se no mercado   │
│  para Inclusão Social           de trabalho digital.   │
│                                                         │
│  Cursos gratuitos com certificado reconhecido para      │
│  empreendedores, artesãos e trabalhadores informais.   │
│                                                         │
│  [Quero me Matricular]    [Conheça os Cursos]          │
└─────────────────────────────────────────────────────────┘
```

**Tagline:** "Do saber à prática — qualificação que transforma vidas."

---

### Seção: O que é o TDS?

**Texto curto (para o site):**

> O **Transformação Digital para Inclusão Social (TDS)** é um programa de
> qualificação profissional gratuito desenvolvido em parceria com instituições
> de ensino e organizações do terceiro setor. Nossos cursos são 100% online,
> acessíveis pelo celular e com certificado emitido automaticamente ao final.

**3 pilares visuais (ícones + texto):**
1. **Gratuito** — sem taxas de matrícula ou mensalidade
2. **Certificado** — emitido digitalmente e verificável online
3. **Pelo WhatsApp** — conteúdo acessível direto no seu celular

---

### Seção: Cursos Disponíveis

Exibir cards dos cursos registrados no AnythingLLM:

| Curso | Carga Horária | Público-alvo |
| :--- | :--- | :--- |
| Gestão Financeira para Empreendimentos | 8h | Empreendedores |
| Boas Práticas na Produção e Manipulação de Alimentos | 6h | Manipuladores de alimentos |
| Organização da Produção para o Mercado | 6h | Produtores locais |
| Marketing Digital para Pequenos Negócios | 8h | Comerciantes |

> Os cursos são carregados dinamicamente via API do n8n — nunca precisam ser
> editados manualmente no HTML.

---

### Seção: Como Funciona?

**3 passos ilustrados:**

```
[1] Matricule-se       [2] Estude no WhatsApp    [3] Receba o Certificado
Preencha o            Acesse as aulas e          Ao concluir todos os
formulário online.    converse com o             quizzes, seu certificado
É rápido e gratuito.  assistente de IA.          é gerado automaticamente.
```

---

### Seção: Parceiros Institucionais

Logos dos parceiros (carregados dinamicamente por tenant):
- UFT (Universidade Federal do Tocantins)
- IPEX
- FAPTO (a confirmar)
- Sebrae-TO (a confirmar)

---

### Seção: Depoimentos

Placeholder para depoimentos de alunos. Integrar futuramente com formulário
de coleta via WhatsApp.

---

### Rodapé (Footer)

- Links: Política de Privacidade | Verificar Certificado | Contato
- WhatsApp de suporte: integrado via Chatwoot (botão flutuante)
- Endereço institucional do parceiro (dinâmico por tenant)

---

## 2. Formulário de Matrícula

Campos mínimos:
- Nome completo
- CPF (validação de formato)
- WhatsApp (com DDI)
- Curso desejado (dropdown)
- Município

Ao submeter:
1. n8n recebe via webhook
2. Cria registro no PostgreSQL (`students`)
3. Envia mensagem de boas-vindas via Evolution API (WhatsApp)
4. Adiciona aluno ao Chatwoot com tag do tenant

---

## 3. Instruções para o Agente Implementar

Para implementar o site institucional, o agente deve:

1. Criar o componente `app/page.tsx` no Next.js com as seções acima
2. Usar **shadcn/ui** para cards e botões
3. Usar **Tailwind CSS** para layout responsivo (mobile-first)
4. Consumir a rota `/webhook/cursos` do n8n para listar cursos dinamicamente
5. O formulário de matrícula deve fazer POST para `/webhook/matricula`
6. Inserir o widget do Chatwoot no `layout.tsx` (script tag do Chatwoot)
7. O logo e nome do parceiro devem ser lidos de uma variável de ambiente:
   `NEXT_PUBLIC_TENANT_NAME` e `NEXT_PUBLIC_TENANT_LOGO_URL`

**Paleta de Cores TDS:**
- Primária: `#1B4F72` (azul institucional)
- Secundária: `#28B463` (verde progresso)
- Fundo: `#F8F9FA`
- Texto: `#212529`
