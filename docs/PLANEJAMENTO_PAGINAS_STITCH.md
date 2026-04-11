# Planejamento de Páginas TDS (Stitch Style) e Instruções Backend

Devido a uma limitação técnica no acesso ao Stitch (requer autenticação OAuth2 indisponível no momento), realizei o planejamento detalhado das páginas faltantes e as instruções para a configuração do backend.

## 1. Design das Páginas Faltantes

### A. Guia do Aluno (`/guia-aluno`)
- **Estilo:** Mobile-first, ícones grandes, linguagem simples (Paulo Freire).
- **Conteúdo:**
    - **Passo 1:** Como falar com o robô no WhatsApp.
    - **Passo 2:** Como pedir ajuda ao tutor (comando `/ajuda`).
    - **Passo 3:** Como fazer o quiz final e emitir o certificado.
- **Componentes:** `Accordion` para FAQs e `VideoPlayer` para tutorial rápido.

### B. Guia do Tutor (`/guia-tutor`)
- **Estilo:** Painel técnico, focado em produtividade.
- **Conteúdo:**
    - Fluxo de Transbordo (Handoff): Quando intervir.
    - Uso das notas privadas no Chatwoot.
    - Consulta de contexto SISEC do aluno para apoio personalizado.
- **Componentes:** `Flowchart` interativo e `CheatSheet` de comandos.

### C. Guia do Gestor (`/guia-gestor`)
- **Estilo:** Dashboard executivo.
- **Conteúdo:**
    - Como gerenciar listas de transmissão sem levar ban (SPAM).
    - Interpretação das métricas de engajamento.
    - Processo de sincronização Supabase ↔ LMS.
- **Componentes:** `TipsCard` e links rápidos para ferramentas de gestão.

### D. Informações SISEC (`/sisec-info`)
- **Conteúdo:** Transparência sobre o uso de dados socioeconômicos para fins de inclusão produtiva.
- **Componentes:** `DataSecuritySeal` e listagem de campos utilizados.

---

## 2. Instruções para o Claude (Configuração Backend)

**Copie e cole este comando para o Claude configurar o suporte a estas páginas:**

```text
Claude, precisamos configurar o backend e a integração para as novas páginas instrucionais do TDS. Siga este roteiro técnico:

1. **Estrutura de Conteúdo (Supabase):**
   - Crie uma tabela `public.knowledge_base` com as colunas: `id (uuid)`, `slug (text, unique)`, `title (text)`, `content (markdown/text)`, `role_access (text - 'student', 'tutor', 'manager')`.
   - Adicione políticas de RLS para que:
     - 'anon' e 'authenticated' possam ler slugs com role 'student'.
     - Somente 'authenticated' com role 'tutor'/'admin' possa ler slugs técnicos.

2. **API de Validação de Certificado:**
   - No arquivo `projeto-tds/lms_lite_api.py`, implemente um novo endpoint `GET /api/v1/validate/:hash`.
   - Este endpoint deve consultar a tabela `public.enrollments` filtrando pelo `certificate_hash`.
   - Retorne um JSON com: `{ valid: true, student_name, course_title, completion_date }`.

3. **Roteamento no React:**
   - Em `projeto-tds/dashboard-tds/src/App.jsx`, adicione as rotas para:
     - `StudentPortal` -> Adicionar sub-rotas para `/guia`.
     - `AdminDashboard` -> Adicionar links na sidebar para `/guia-tutor` e `/guia-gestor`.

4. **Componente de Visualização:**
   - Crie um componente genérico `GuideViewer.jsx` que recebe o `slug` via URL, busca o conteúdo no Supabase e renderiza usando uma biblioteca de Markdown (como `react-markdown`).

5. **Deploy:**
   - Execute o rebuild do container: `docker compose -f docker-compose.lite.yml up -d --build lms-lite-dashboard`.
```
