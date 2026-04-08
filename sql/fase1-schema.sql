-- ============================================================
-- TDS Fase 1 — Schema PostgreSQL
-- Banco: kreativ_edu | User: kreativ
-- ============================================================

CREATE TABLE IF NOT EXISTS alunos (
  id           SERIAL PRIMARY KEY,
  nome         VARCHAR(200) NOT NULL,
  cpf          VARCHAR(14)  UNIQUE,
  telefone     VARCHAR(20)  UNIQUE NOT NULL,
  email        VARCHAR(200),
  municipio    VARCHAR(100),
  status       VARCHAR(20)  NOT NULL DEFAULT 'pre-matricula'
                 CHECK (status IN ('pre-matricula','matriculado','concluido','reprovado')),
  dados_baseline JSONB NOT NULL DEFAULT '{}',
  typebot_session_id VARCHAR(100),
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS turmas (
  id           SERIAL PRIMARY KEY,
  nome         VARCHAR(200) NOT NULL,
  curso        VARCHAR(100) NOT NULL,
  tutor_nome   VARCHAR(200),
  data_inicio  DATE,
  data_fim     DATE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matriculas (
  id             SERIAL PRIMARY KEY,
  aluno_id       INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  turma_id       INTEGER NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
  data_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
  status         VARCHAR(20) NOT NULL DEFAULT 'ativa'
                   CHECK (status IN ('ativa','concluida','cancelada')),
  UNIQUE (aluno_id, turma_id)
);

CREATE TABLE IF NOT EXISTS aulas (
  id                SERIAL PRIMARY KEY,
  turma_id          INTEGER NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
  titulo            VARCHAR(300) NOT NULL,
  data_hora         TIMESTAMPTZ NOT NULL,
  link_meet         VARCHAR(500),
  thread_anythingllm VARCHAR(200),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS presenca (
  id           SERIAL PRIMARY KEY,
  aluno_id     INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  aula_id      INTEGER NOT NULL REFERENCES aulas(id) ON DELETE CASCADE,
  presente     BOOLEAN NOT NULL DEFAULT FALSE,
  obs          TEXT,
  registrado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (aluno_id, aula_id)
);

CREATE TABLE IF NOT EXISTS typebot_sessoes (
  id                        SERIAL PRIMARY KEY,
  telefone                  VARCHAR(20) UNIQUE NOT NULL,
  session_id                VARCHAR(200) NOT NULL,
  chatwoot_conversation_id  INTEGER,
  status                    VARCHAR(20) NOT NULL DEFAULT 'ativo'
                              CHECK (status IN ('ativo','concluido','abandonado')),
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alunos_telefone    ON alunos(telefone);
CREATE INDEX IF NOT EXISTS idx_alunos_cpf         ON alunos(cpf);
CREATE INDEX IF NOT EXISTS idx_matriculas_turma   ON matriculas(turma_id);
CREATE INDEX IF NOT EXISTS idx_aulas_turma_data   ON aulas(turma_id, data_hora);
CREATE INDEX IF NOT EXISTS idx_presenca_aula      ON presenca(aula_id);
CREATE INDEX IF NOT EXISTS idx_typebot_telefone   ON typebot_sessoes(telefone);
