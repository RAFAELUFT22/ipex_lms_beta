# 🚀 Squad TDS - Plano de Aceleração

## 📋 Backlog Geral
- [ ] Refinar paleta de cores para os tons oficiais: #2E4053 (Azul), #8BC34A (Verde), #F7DC6F (Amarelo).
- [ ] Renomear módulos no sistema: "Cognitive Tutor" -> "Tutor Cognitivo", "Management Panel" -> "Painel de Gestão".
- [ ] Implementar templates de boas-vindas (WhatsApp/E-mail) conforme RAG.
- [ ] Customizar template de Certificado com logo TDS e assinaturas.

## 🤖 Atribuições

### 1. Executor (Agente Generalista)
**Tarefa:** Atualizar Branding e Traduções de Negócio.
- Aplicar as cores oficiais no `lms_theme.css`.
- Injetar as descrições do RAG (Tutor Cognitivo, Painel de Gestão) no banco de dados.
- Configurar os nomes de módulos via `Custom Field` ou `Translation`.

### 2. Testador (Agente Generalista)
**Tarefa:** Validação Multi-Papel e UX.
- Capturar screenshots dos perfis: Aluno, Professor e Gestor.
- Validar se as mensagens de boas-vindas aparecem corretamente nas rotas `/lms`.
- Verificar consistência do novo nome longo em todas as telas.

### 3. Buscador (Agente Generalista)
**Tarefa:** Pesquisa Técnica de Certificados.
- Pesquisar como injetar assinaturas e logos ACT em certificados do Frappe LMS (v15+).
- Propor o código Jinja para o `LMS Certificate`.

---
*Nota: Consulte sempre o RAG no AnythingLLM em caso de dúvida sobre termos institucionais.*
