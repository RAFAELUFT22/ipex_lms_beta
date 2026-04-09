# 🚀 Análise Técnica: Futuro do LMS TDS

## 1. Diagnóstico de Infraestrutura (Modelos de IA)

| Modelo | Localização | Latência | Recomendação de Uso |
| :--- | :--- | :--- | :--- |
| **Qwen 2.5 (7b)** | Ollama (Local) | **ALTA** (CPU Only: ~440% load) | Tarefas assíncronas, resumo de logs, triagem de dados sensíveis. |
| **Gemini 1.5 Flash** | Cloud (API) | **BAIXA** (Instante) | **Interface do Aluno**, Tutor Cognitivo, Geração de conteúdo dinâmico. |

> [!IMPORTANT]
> O servidor atual não possui aceleração por GPU (NVIDIA). Por isso, rodar modelos de 7B ou maiores no Ollama prejudica o desempenho global de outros serviços como n8n e Chatwoot.

## 2. A "Armadilha" do Frappe LMS
O Frappe é robusto no backend, mas as tentativas de customização de branding (`fix_landing_final.py`, `apply_native_branding.py`) geram dívida técnica. 
- **Problema:** Cada atualização do Frappe pode quebrar os scripts de injeção de CSS/JS.
- **Sintoma:** Você gasta mais tempo corrigindo o "vazamento" do design original do Frappe do que criando novas funcionalidades.

## 3. Proposta: TDS LMS Lite (Arquitetura Desacoplada)

A alternativa provisória — e talvez definitiva — é criar uma **View Layer** moderna que consuma as APIs que você já tem.

### Arquitetura Sugerida:
1. **Database/SSO (Frappe):** Continua sendo a fonte da verdade para Alunos, Cursos e Matrículas.
2. **Cérebro (AnythingLLM RAG):** Fornece o conteúdo e o suporte via RAG das ementas do TDS.
3. **Frontend (LMS Lite):** Uma aplicação SPA (Vite + Tailwind) focada em 3 telas:
   - **Dashboard:** Simples, com os cards de cursos vindos da API do Frappe.
   - **Aula:** Leitor de conteúdo limpo que consulta o RAG para tirar dúvidas.
   - **Tutor:** Chat persistente integrado ao Chatwoot.

### Vantagens:
- **Velocidade de Dev:** Criar um card em HTML/Tailwind é 10x mais rápido que customizar um template Jinja2 do Frappe.
- **Performance:** App extremamente leve, carregando apenas o necessário.
- **Independência:** Se você decidir trocar o Frappe pelo Moodle ou um banco de dados próprio amanhã, o Frontend continua o mesmo.

## 4. Próximos Passos Sugeridos

1. **POC de Interface:** Criar uma página única (ex: `aluno.ipexdesenvolvimento.cloud`) que liste os cursos consumindo a API `/api/resource/LMS Course`.
2. **Integração RAG-First:** Fazer com que o conteúdo das aulas seja enriquecido por chamadas ao AnythingLLM, corrigindo lacunas nas ementas originais.
3. **Monitoramento do Ollama:** Reduzir o modelo local para um **TinyLlama (1.1B)** ou **Gemma 2B** para tarefas básicas, liberando CPU para o resto do sistema.

---
**Pergunta para o usuário:** Deseja que eu esboce uma estrutura básica (HTML/JS) de como seria essa tela de Dashboard "LMS Lite" consumindo a sua API real do Frappe?
