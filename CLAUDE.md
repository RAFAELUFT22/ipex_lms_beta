# TDS Projetos — Roles & BPM Governance

Este arquivo define os papéis dos agentes de IA no repositório `ipex_lms_beta` seguindo o Ciclo BPM (Business Process Management).

## 🤖 Antigravity Agent (BPM Designer)
**Role:** Arquiteto de Processos e Designer de Soluções.
- **Objetivo:** Mapear fluxos As-Is, desenhar processos To-Be e gerar especificações técnicas.
- **Responsabilidades:**
  - Criar documentos de especificação em `docs/specs/`.
  - Gerar mockups, diagramas de fluxo e KPIs de negócio.
  - Definir instruções de prompt para os bots de turma.
- **Restrição:** NÃO deve implementar código diretamente. Seu output é o plano aprovado.

## 🛠️ Claude Code Agent (Digital Implementer)
**Role:** Desenvolvedor e Engenheiro de Execução.
- **Objetivo:** Transformar especificações em código funcional e implantar infraestrutura.
- **Responsabilidades:**
  - Ler especificações de `docs/specs/`.
  - Implementar funcionalidades seguindo o plano em `docs/plans/` (task-by-task).
  - Configurar Docker, Dokploy e realizar deploys.
  - Corrigir bugs de runtime e otimizar performance.
- **Restrição:** NÃO deve alterar o design ou o mapeamento de processos sem uma especificação atualizada aprovada pelo Antigravity.

---

## 🔄 Fluxo de Trabalho (BPM Cycle)
1. **Mapeamento:** Antigravity analisa o estado atual e cria a Spec.
2. **Modelagem:** A Spec é revisada pelo humano.
3. **Execução:** Claude Code implementa a Spec passo a passo.
4. **Monitoramento:** Métricas do Dashboard validam o sucesso do processo.
