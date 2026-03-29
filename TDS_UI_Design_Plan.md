# 🎨 Projeto de Design: Kreativ Education (TDS)
**Conceito:** Moderno, Clean, Inclusivo e Regionalizado.

## 🌈 Sistema de Design (Baseado em UFT/IPEX)

- **Paleta de Cores:**
  - **Primária:** `#003366` (Azul Marinho UFT - Confiança e Seriedade)
  - **Secundária:** `#008080` (Teal/Verde Água - Natureza e Sustentabilidade)
  - **Acento:** `#FFCC00` (Amarelo Sol - Energia e Inovação)
  - **Neutros:** `#F8F9FA` (Fundo), `#333333` (Texto principal), `#FFFFFF` (Cards)
- **Tipografia:**
  - **Headings:** Inter (Bold) - Moderno e legível.
  - **Body:** Montserrat (Regular) - Acessível e amigável.
- **Componentes:** Bordas arredondadas (8px), Sombras leves (Soft UI), Ícones minimalistas.

---

## 📱 1. Dashboard de Boas-vindas do Aluno
**Objetivo:** Facilitar o acesso imediato ao conteúdo e motivar o progresso.

- **Topo (Navbar):**
  - Logotipo **Kreativ Education** à esquerda.
  - Avatar do aluno e sino de notificações à direita.
- **Banner de Boas-vindas (Hero):**
  - Fundo em degradê Azul Marinho para Teal.
  - Texto: "Olá, João! Que bom ter você de volta."
  - Botão de Ação Rápida: **[Continuar: Empreendedorismo Popular]** (Amarelo).
- **Corpo Central:**
  - **Meus Cursos (Cards):** Lista horizontal de cursos em andamento com barra de progresso circular.
  - **Trilhas Formativas:** Visualização em "Pipeline" do caminho do aluno (ex: de 'Educação Financeira' para 'Sistemas Produtivos').
- **Barra Lateral/Acesso Rápido:**
  - Atalho flutuante para o **Tutor Cognitivo**.
  - Próximos eventos (Aulas síncronas/Encontros IPEX).

---

## 🤖 2. Interface do 'Tutor Cognitivo' (RAG Integration)
**Objetivo:** Interação fluida com a IA (AnythingLLM) consumindo os documentos do TDS (RAG).

- **Layout de Conversa:**
  - **Header:** "Tutor Cognitivo TDS" com status "Online" em verde.
  - **Balões de Chat:** Usuário (Azul Marinho), Tutor (Teal suave).
  - **Referências (RAG):** Pequenos ícones de documentos abaixo das respostas da IA. Ao clicar, abre o PDF (ex: Ementas) no ponto exato da citação.
- **Painel de Contexto (Direita):**
  - "Perguntas Frequentes sobre [Curso Atual]".
  - Lista de documentos base (Ementas, Projeto TDS V3).
- **Input:**
  - Campo de texto limpo com suporte a **Mensagem de Voz** (Crucial para o público-alvo de vulnerabilidade).
  - Sugestões de perguntas automáticas: "Quais são os ODS do projeto?", "Como acessar o PAA?".

---

## 🏛️ 3. Portal de Gestão para Diretores
**Objetivo:** Visão analítica macro para múltiplas escolas e controle de impacto.

- **Seletor de Escola (Top Bar):**
  - Dropdown: **[Todas as Escolas | IPEX | UFT | Outras]**.
- **Métricas de Impacto (KPI Cards):**
  - Total de Alunos Ativos (Contagem em tempo real).
  - Taxa de Conclusão (Gráfico de Rosca).
  - Engajamento com IA (Média de perguntas por aluno).
- **Tabela de Gestão:**
  - Filtros por Município (ex: Bico do Papagaio, Jalapão).
  - Status de certificação e participação em trilhas.
- **Relatórios:**
  - Botão de exportação para MDS/FAPTO em PDF/Excel.

---

## 🛠️ Notas de Implementação (LMS + Chatwoot + AnythingLLM)
- **Frappe Education:** Customização do `User Dashboard` via Hooks e CSS Global.
- **Chatwoot Integration:** O ícone do Tutor Cognitivo abre o widget do Chatwoot que está integrado ao bot AnythingLLM.
- **Acessibilidade:** Alto contraste disponível e suporte total a leitores de tela.
