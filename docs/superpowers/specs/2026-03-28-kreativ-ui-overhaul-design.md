# Design Spec: Kreativ Education (TDS) UI & Translation Overhaul
**Data:** 2026-03-28
**Autor:** Gemini CLI

## 1. Visão Geral
Transformar a interface padrão do Frappe LMS em uma experiência premium, moderna e regionalizada (TDS), baseada no design "Kreativ Education" e concluir a tradução integral para pt-BR utilizando modelos locais (TeenyTinyLlama).

## 2. Arquitetura de Interface (LMS SPA Overrides)

### 2.1. Estratégia de Override Avançado
Pesquisas confirmam que o Frappe LMS utiliza Vue.js SPA, o que dificulta overrides simples via Jinja. A estratégia será:
- **Custom App:** Utilizar o `kreativ_theme` (ou criar `kreativ_portal`) para hospedar os overrides.
- **Routing Hijack:** Usar `website_route_rules` no `hooks.py` para redirecionar `/lms` para um template customizado (`lms_custom.html`).
- **Component Replacement:** Injetar um wrapper Vue ou manipular o DOM via `web_include_js` para inserir a Sidebar e o Header sem quebrar a reatividade do Vue original.

### 2.2. Componentes Visuais (Baseado em Imagens)
- **Sidebar (Desktop):** Barra lateral fixa branca com ícones minimalistas (Navy #003366).
- **Hero Section:** Gradiente de `#003366` para `#008080` com bordas arredondadas (40px no mobile).
- **Cards de Curso:** Estilo "Soft UI" com bordas de 14px e sombras leves.

## 3. Estratégia de Tradução (TeenyTinyLlama Local)

### 3.1. Infraestrutura de Inferência
- **Modelo:** TeenyTinyLlama (460M) otimizado para pt-BR.
- **Implementação:** Utilizar a biblioteca `transformers` em Python dentro do container Frappe ou um microserviço dedicado.
- **Pipeline de Tradução:**
    - O modelo será carregado via `AutoModelForCausalLM`.
    - Prompting especializado ("Few-shot") para forçar a tradução de English -> pt-BR, já que o modelo é monolíngual por design.
    - Sistema de cache JSON (`translation_cache.json`) para persistência.

## 4. Plano de Implementação

### Fase 1: Setup de Inferência Local
- [ ] Criar script `scripts/local_translate.py` usando `transformers` e TeenyTinyLlama 460M.
- [ ] Validar a qualidade da tradução com o modelo local.

### Fase 2: UI Overhaul (Kreativ Design)
- [ ] Configurar `website_route_rules` para interceptar as rotas do LMS.
- [ ] Implementar o layout Sidebar/Main em `lms_custom.html`.
- [ ] Refinar o CSS global em `lms_theme.css`.

### Fase 3: Tradução e Deploy
- [ ] Rodar a tradução em massa com o modelo local.
- [ ] Importar traduções para o site (`bench import-translations`).
- [ ] Realizar `bench build` e `bench clear-cache`.

## 5. Critérios de Aceite
- [ ] Dashboard do aluno com Sidebar funcional e estética Kreativ.
- [ ] Tradução pt-BR completa e fiel ao contexto acadêmico.
- [ ] Independência de APIs externas de tradução (Quota-free).
