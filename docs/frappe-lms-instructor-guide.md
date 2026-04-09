# 🎓 Guia de Funcionalidades para Instrutores - Frappe LMS (TDS)

Este guia descreve como utilizar as ferramentas de instrutor para o projeto TDS, incluindo integração com Google Meet, calendários e gestão de presença.

## 1. Integração com Google Meet
A integração permite que instrutores agendem aulas ao vivo diretamente pelo Frappe LMS.

*   **Configuração**: O administrador deve configurar as credenciais no DocType `LMS Google Meet Settings` (OAuth 2.0).
*   **Agendamento**: Ao criar uma **Live Class** (Aula ao Vivo) vinculada a uma **Turma (Batch)**, o link do Google Meet é gerado automaticamente se o instrutor tiver sincronizado sua conta Google.
*   **Visibilidade**: O link aparece no dashboard do aluno e do instrutor minutos antes do início da aula.

## 2. Calendário Acadêmico
O Frappe LMS utiliza o DocType `Event` e integrações nativas para manter o calendário atualizado.

*   **Sincronização**: Eventos criados no LMS (Avaliações, Aulas ao Vivo) são sincronizados com o Google Calendar do instrutor.
*   **Timetable**: O DocType `LMS Batch Timetable` permite definir o cronograma semanal de aulas da turma.

## 3. Gestão de Presença (Attendance)
A presença é gerenciada de forma híbrida no Frappe LMS.

*   **Aulas ao Vivo**: O sistema registra automaticamente a presença (ou marca a lição como concluída) quando o aluno clica no botão **"Entrar na Reunião"**.
*   **DocTypes Envolvidos**: 
    *   `LMS Live Class Participant`: Registra quem entrou na sessão ao vivo.
    *   `Student Attendance`: Registro formal de presença para fins acadêmicos.
*   **Manual**: Instrutores podem marcar a presença em massa através do portal administrativo para aulas presenciais.

## 4. Terminolgia Corrigida (TDS)
Para facilitar a comunicação com o público do projeto, padronizamos os termos:
*   **Batch** → Turma
*   **Course** → Curso
*   **Lesson** → Lição / Aula
*   **Quiz** → Questionário / Avaliação

---
*Documento gerado para o Projeto TDS - IPEX/UFT/MDS.*
