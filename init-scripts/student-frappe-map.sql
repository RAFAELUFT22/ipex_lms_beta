-- =============================================================================
-- student_frappe_map — Bridge phone → frappe_email
-- Usado pelo N8N para resolver telefone WhatsApp em email Frappe
-- =============================================================================

CREATE TABLE IF NOT EXISTS student_frappe_map (
    phone           VARCHAR(20)  PRIMARY KEY,
    frappe_email    VARCHAR(255) NOT NULL,
    frappe_user_name VARCHAR(255),
    synced_at       TIMESTAMP    DEFAULT NOW(),
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sfm_email ON student_frappe_map(frappe_email);

-- Mapeamento de cursos PG → Frappe (para migração)
CREATE TABLE IF NOT EXISTS course_frappe_map (
    pg_course_id    INTEGER PRIMARY KEY,
    frappe_course   VARCHAR(255) NOT NULL,
    pg_course_name  VARCHAR(255),
    synced_at       TIMESTAMP DEFAULT NOW()
);

-- Seed de mapeamento padrão
INSERT INTO course_frappe_map (pg_course_id, frappe_course, pg_course_name) VALUES
    (1, 'gestao-financeira-para-empreendimentos', 'Gestão Financeira'),
    (2, 'boas-praticas-na-producao-e-manipulacao-de-alimentos', 'Boas Práticas Alimentos'),
    (3, 'organizacao-da-producao-para-o-mercado', 'Organização da Produção')
ON CONFLICT DO NOTHING;
