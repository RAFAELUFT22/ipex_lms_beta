# DocTypes do Frappe LMS — Referência Completa

> Listagem dos 67 DocTypes disponíveis no Frappe LMS v2.44 (branch develop).

## DocTypes Principais (CRUD via API)

| DocType | Descrição | Uso Principal |
|---------|-----------|---------------|
| `LMS Course` | Curso | Criar/gerenciar cursos |
| `Course Chapter` | Capítulo | Agrupar lições |
| `Course Lesson` | Lição | Conteúdo (texto, vídeo, quiz) |
| `LMS Quiz` | Quiz | Avaliações |
| `LMS Question` | Pergunta | Banco de questões |
| `LMS Option` | Opção | Alternativas de resposta |
| `LMS Enrollment` | Matrícula | Vincular aluno ↔ curso |
| `LMS Certificate` | Certificado | Emitir certificados |
| `LMS Batch` | Turma | Agrupar cursos + alunos |
| `LMS Category` | Categoria | Classificar cursos |
| `LMS Settings` | Configurações | Config global do LMS |

## DocTypes de Child Table

| DocType | Pai | Descrição |
|---------|-----|-----------|
| `Course Instructor` | `LMS Course` | Instrutores do curso |
| `Course Evaluator` | `LMS Course` | Avaliadores |
| `Chapter Reference` | `LMS Course` | Referência a capítulos |
| `Lesson Reference` | `Course Chapter` | Referência a lições |
| `LMS Quiz Question` | `LMS Quiz` | Questões do quiz |
| `Related Courses` | `LMS Course` | Cursos relacionados |
| `Batch Course` | `LMS Batch` | Cursos da turma |
| `LMS Coupon Item` | `LMS Coupon` | Itens do cupom |
| `LMS Sidebar Item` | `LMS Settings` | Menu lateral |

## DocTypes de Progresso / Submissão

| DocType | Descrição |
|---------|-----------|
| `LMS Course Progress` | Progresso por lição |
| `LMS Quiz Result` | Resultado individual |
| `LMS Quiz Submission` | Submissão de quiz |
| `LMS Assignment Submission` | Entrega de tarefa |
| `LMS Video Watch Duration` | Tempo assistido |

## DocTypes de Avaliação

| DocType | Descrição |
|---------|-----------|
| `LMS Assessment` | Avaliação |
| `LMS Assignment` | Tarefa |
| `LMS Certificate Evaluation` | Avaliação para certificado |
| `LMS Certificate Request` | Solicitação de certificado |
| `Evaluator Schedule` | Agenda do avaliador |

## DocTypes de Perfil

| DocType | Descrição |
|---------|-----------|
| `Education Detail` | Formação do usuário |
| `Work Experience` | Experiência profissional |
| `Skills` | Habilidades |
| `User Skill` | Skill vinculada ao user |
| `Preferred Industry` | Indústria preferida |
| `Preferred Function` | Função preferida |

## DocTypes Avançados

| DocType | Descrição |
|---------|-----------|
| `LMS Batch Enrollment` | Matrícula em turma |
| `LMS Batch Feedback` | Feedback de turma |
| `LMS Batch Timetable` | Grade horária |
| `LMS Timetable Legend` | Legenda da grade |
| `LMS Timetable Template` | Template de grade |
| `LMS Live Class` | Aula ao vivo |
| `LMS Live Class Participant` | Participante de aula |
| `LMS Program` | Programa (sequência de cursos) |
| `LMS Program Course` | Curso vinculado ao programa |
| `LMS Program Member` | Membro do programa |
| `LMS Course Interest` | Interesse em curso |
| `LMS Course Mentor Mapping` | Mentor ↔ curso |
| `LMS Course Review` | Avaliação do curso |
| `LMS Lesson Note` | Anotações por lição |
| `LMS Payment` | Pagamento |
| `LMS Coupon` | Cupom de desconto |
| `LMS Badge` | Badge/medalha |
| `LMS Badge Assignment` | Atribuição de badge |
| `LMS Source` | Origem do aluno |
| `Certification` | Configuração de certificados |

## DocTypes de Exercícios (Code)

| DocType | Descrição |
|---------|-----------|
| `LMS Programming Exercise` | Exercício de código |
| `LMS Programming Exercise Submission` | Submissão |
| `LMS Test Case` | Caso de teste |
| `LMS Test Case Submission` | Resultado do teste |
| `LMS Section` | Seção de exercício |
| `Function` | Definição de função |
| `Scheduled Flow` | Fluxo agendado |

## DocTypes de Integrações

| DocType | Descrição |
|---------|-----------|
| `LMS Zoom Settings` | Configuração do Zoom |
| `Zoom Settings` | Zoom global |
| `Payment Country` | País de pagamento |
| `Industry` | Indústria (lista) |
