// =====================================================
// DEFINIÇÃO DOS CAMPOS DO FORMULÁRIO TDS
// 102 campos + campos auxiliares
// =====================================================

export const FORM_FIELDS = [
  // ── CABEÇALHO DO CURSO ──────────────────────────────────────────────────────
  { id: 'timestamp',          label: 'Carimbo de data/hora',            type: 'datetime',  block: 0 },
  { id: 'campo_1',            label: '1. Qual é o nome do curso em que você está inscrito? *', type: 'text',     block: 1 },
  { id: 'campo_2',            label: '2. Carga Horária',                type: 'text',      block: 1 },
  { id: 'campo_3',            label: '3. Data de Início',               type: 'date',      block: 1 },
  { id: 'campo_4',            label: '4. Previsão de Término',          type: 'date',      block: 1 },
  { id: 'campo_5',            label: '5. Local',                        type: 'text',      block: 1 },

  // ── BLOCO 1: IDENTIFICAÇÃO ─────────────────────────────────────────────────
  { id: 'campo_6',            label: '6. Nome Completo *',              type: 'text',      block: 1 },
  { id: 'campo_7',            label: '7. Data de Nascimento',           type: 'date',      block: 1 },
  { id: 'campo_8',            label: '8. Mais de 60 anos?',             type: 'select',    block: 1, options: ['Sim','Não'] },
  { id: 'campo_9',            label: '9. CPF',                          type: 'text',      block: 1 },
  { id: 'campo_10',           label: '10. RG',                          type: 'text',      block: 1 },
  { id: 'campo_11',           label: '11. Naturalidade',                type: 'text',      block: 1 },
  { id: 'campo_12',           label: '12. Estado Civil',                type: 'select',    block: 1, options: ['Solteiro(a)','Casado(a)','Divorciado(a)','Viúvo(a)','União estável','Outro'] },
  { id: 'campo_13',           label: '13. Gênero',                      type: 'select',    block: 1, options: ['Masculino','Feminino','Não-binário','Prefiro não informar','Outro'] },
  { id: 'campo_14',           label: '14. Cor/Raça',                    type: 'select',    block: 1, options: ['Branca','Preta','Parda','Amarela','Indígena','Prefiro não informar'] },
  { id: 'campo_15',           label: '15. Você se identifica como Quilombola?', type: 'select', block: 1, options: ['Sim','Não'] },
  { id: 'campo_16',           label: '16. Telefone/Celular',            type: 'text',      block: 1 },
  { id: 'campo_17',           label: '17. E-mail',                      type: 'email',     block: 1 },

  // ── BLOCO 1: ENDEREÇO ─────────────────────────────────────────────────────
  { id: 'campo_18',           label: '18. Logradouro',                  type: 'text',      block: 1 },
  { id: 'campo_19',           label: '19. Número',                      type: 'text',      block: 1 },
  { id: 'campo_20',           label: '20. Bairro / Assentamento',       type: 'text',      block: 1 },
  { id: 'campo_21',           label: '21. Complemento',                 type: 'text',      block: 1 },
  { id: 'campo_22',           label: '22. CEP',                         type: 'text',      block: 1 },
  { id: 'campo_23',           label: '23. Município',                   type: 'text',      block: 1 },
  { id: 'campo_24',           label: '24. Estado',                      type: 'text',      block: 1 },
  { id: 'campo_25',           label: '25. Escolaridade',                type: 'select',    block: 1, options: ['Sem instrução','Fundamental incompleto','Fundamental completo','Médio incompleto','Médio completo','Superior incompleto','Superior completo','Pós-graduação'] },

  // ── BLOCO 2: SAÚDE E CONDIÇÃO SOCIOECONÔMICA ──────────────────────────────
  { id: 'campo_26',           label: '26. Possui algum tipo de deficiência?',    type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_27',           label: '27. Se sim, especifique o tipo',           type: 'text',   block: 2 },
  { id: 'campo_28',           label: '28. Necessita de algum Atendimento Especial', type: 'text', block: 2 },
  { id: 'campo_29',           label: '29. Está trabalhando atualmente com Carteira Assinada?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_30',           label: '30. Está recebendo o Seguro Desemprego?',  type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_31',           label: '31. Está regularmente inscrito no CadÚnico?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_32',           label: '32. Está cadastrado no banco de dados do SINE?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_33',           label: '33. Já foi beneficiário de políticas de inclusão social, desenvolvimento regional ou local?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_34',           label: '34. É ou já foi interno/egresso do sistema prisional / cumpriu medidas socioeducativas?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_35',           label: '35. Já foi resgatado de situação de trabalho forçado ou condição análoga à escravidão?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_36',           label: '36. Tem ou teve familiares em situações de trabalho infantil?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_37',           label: '37. É trabalhador de setor estratégico da economia sustentável?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_38',           label: '38. Se considera trabalhador cooperativado, associativo, autogestionado ou MEI?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_39',           label: '39. Pertence a Povos e Comunidades Tradicionais?', type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_40',           label: '40. É trabalhador rural?',                 type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_41',           label: '41. É pescador artesanal?',                type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_42',           label: '42. É estagiário?',                        type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_43',           label: '43. É aprendiz?',                          type: 'select', block: 2, options: ['Sim','Não'] },
  { id: 'campo_obs_bloco4',   label: 'Obs. Bloco 4 — Observações adicionais (ex: NIS do CadÚnico, nº de registro SINE...)', type: 'textarea', block: 2 },
  { id: 'campo_44',           label: '44. Recebe algum benefício social? (Marque todos que se aplicam)', type: 'multicheck', block: 2,
    options: ['Bolsa Família / Auxílio Brasil','BPC/LOAS','Seguro Desemprego','Auxílio Acidente','Benefício Aposentadoria (INSS)','Outro'] },

  // ── BLOCO 3: COMPOSIÇÃO FAMILIAR E MORADIA ────────────────────────────────
  { id: 'campo_45',           label: '45. Nº de pessoas no domicílio',           type: 'number', block: 3 },
  { id: 'campo_46',           label: '46. Crianças (0–12)',                       type: 'number', block: 3 },
  { id: 'campo_47',           label: '47. Adolescentes (13–17)',                  type: 'number', block: 3 },
  { id: 'campo_48',           label: '48. Idosos (60+)',                          type: 'number', block: 3 },
  { id: 'campo_49',           label: '49. Pessoas com renda própria',             type: 'number', block: 3 },
  { id: 'campo_50',           label: '50. Tipo de residência',                   type: 'select', block: 3, options: ['Própria quitada','Própria financiada','Alugada','Cedida','Outra'] },
  { id: 'campo_51',           label: '51. Material predominante nas paredes',    type: 'select', block: 3, options: ['Alvenaria/tijolo','Madeira','Taipa/adobe','Outro'] },
  { id: 'campo_52',           label: '52. Tem acesso à água tratada?',            type: 'select', block: 3, options: ['Sim','Não'] },
  { id: 'campo_53',           label: '53. Tem acesso à energia elétrica?',        type: 'select', block: 3, options: ['Sim','Não'] },
  { id: 'campo_54',           label: '54. Tem coleta de lixo?',                  type: 'select', block: 3, options: ['Sim','Não'] },
  { id: 'campo_55',           label: '55. Tem acesso à internet?',               type: 'select', block: 3, options: ['Sim','Não'] },
  { id: 'campo_56',           label: '56. Tem banheiro?',                        type: 'select', block: 3, options: ['Sim','Não'] },

  // ── BLOCO 4: SITUAÇÃO OCUPACIONAL E RENDA ─────────────────────────────────
  { id: 'campo_57',           label: '57. Situação ocupacional atual',            type: 'multicheck', block: 4, options: ['Empregado com carteira','Empregado sem carteira','Autônomo/Informal','Desempregado','Aposentado/Pensionista','Do lar','Estudante','Agricultor familiar','Trabalho eventual / bico','Outro'] },
  { id: 'campo_58',           label: '58. Renda pessoal mensal (faixa)',          type: 'select', block: 4, options: ['Sem renda','Até R$ 300','R$ 301 a R$ 600','R$ 601 a R$ 1.200','R$ 1.201 a R$ 2.000','R$ 2.001 a R$ 3.000','R$ 3.001 a R$ 4.000','Mais de R$ 4.000'] },
  { id: 'campo_59',           label: '59. Valor exato da renda pessoal: R$',     type: 'text',   block: 4 },
  { id: 'campo_60',           label: '60. Renda familiar mensal (faixa)',         type: 'select', block: 4, options: ['Sem renda','Até R$ 300','R$ 301 a R$ 600','R$ 601 a R$ 1.200','R$ 1.201 a R$ 2.000','R$ 2.001 a R$ 3.000','R$ 3.001 a R$ 4.000','Mais de R$ 4.000'] },
  { id: 'campo_61',           label: '61. Valor exato da renda familiar: R$',    type: 'text',   block: 4 },

  // ── BLOCO 5: ATIVIDADE PRODUTIVA ──────────────────────────────────────────
  { id: 'campo_62',           label: '62. Desenvolve alguma atividade produtiva?', type: 'select', block: 5, options: ['Sim','Não'] },
  { id: 'campo_63',           label: '63. Qual atividade? (Marque todas que se aplicam)', type: 'multicheck', block: 5,
    options: ['Agricultura familiar','Pecuária','Pesca','Artesanato','Serviços','Comércio','Agropecuária','Outro'] },
  { id: 'campo_64',           label: '64. Tamanho da área (ha)',                  type: 'text',   block: 5 },
  { id: 'campo_65',           label: '65. Principais produtos',                   type: 'text',   block: 5 },
  { id: 'campo_66',           label: '66. Possui DAP / CAF?',                    type: 'select', block: 5, options: ['Sim','Não'] },
  { id: 'campo_67',           label: '67. A produção é principalmente para',      type: 'multicheck', block: 5, options: ['Consumo próprio','Venda local','Feiras','Venda para cooperativa','Mercado Institucional (PAA/PNAE)','Exportação','Outro'] },
  { id: 'campo_68',           label: '68. Dificuldades para produzir: (Marque as que se aplicam)', type: 'multicheck', block: 5,
    options: ['Falta de crédito','Falta de assistência técnica','Insumos caros','Falta de insumos','Falta de equipamentos','Clima/seca','Pragas','Falta de documentação','Falta de conhecimento técnico','Outro'] },
  { id: 'campo_69',           label: '69. Dificuldades para vender: (Marque as que se aplicam)', type: 'multicheck', block: 5,
    options: ['Dif. acesso a mercados','Falta de mercado','Preço baixo','Falta de transporte','Falta de beneficiamento','Falta de equipamentos','Falta de conhecimento técnico','Falta de documentação','Outro'] },
  { id: 'campo_70',           label: '70. Renda da atividade produtiva (faixa)', type: 'select', block: 5, options: ['Sem renda','Até R$ 300','R$ 301 a R$ 600','R$ 601 a R$ 1.200','R$ 1.201 a R$ 2.000','R$ 2.001 a R$ 3.000','R$ 3.001 a R$ 4.000','Mais de R$ 4.000'] },
  { id: 'campo_71',           label: '71. Valor exato da renda da atividade: R$', type: 'text',  block: 5 },

  // ── BLOCO 6: FINANÇAS E CRÉDITO ───────────────────────────────────────────
  { id: 'campo_72',           label: '72. Possui conta bancária?',                type: 'select', block: 6, options: ['Sim','Não'] },
  { id: 'campo_73',           label: '73. Possui conta digital?',                 type: 'select', block: 6, options: ['Sim','Não'] },
  { id: 'campo_74',           label: '74. Já tomou microcrédito?',                type: 'select', block: 6, options: ['Sim','Não'] },
  { id: 'campo_75',           label: '75. Tem interesse em crédito produtivo?',   type: 'select', block: 6, options: ['Sim','Não'] },
  { id: 'campo_76',           label: '76. Se sim, para qual finalidade?',         type: 'text',   block: 6 },

  // ── BLOCO 7: SAÚDE ────────────────────────────────────────────────────────
  { id: 'campo_77',           label: '77. Possui plano de saúde particular?',     type: 'select', block: 7, options: ['Sim','Não'] },
  { id: 'campo_78',           label: '78. Utiliza SUS regularmente?',             type: 'select', block: 7, options: ['Sim','Não'] },
  { id: 'campo_79',           label: '79. Tem doença crônica diagnosticada?',     type: 'select', block: 7, options: ['Sim','Não'] },
  { id: 'campo_80',           label: '80. Se sim, qual(is)',                      type: 'text',   block: 7 },

  // ── BLOCO 8: ACESSO A TECNOLOGIAS ─────────────────────────────────────────
  { id: 'campo_81',           label: '81. Possui celular próprio?',               type: 'select', block: 8, options: ['Sim','Não'] },
  { id: 'campo_82',           label: '82. Possui acesso à internet?',             type: 'select', block: 8, options: ['Sim','Não'] },
  { id: 'campo_83',           label: '83. Já usou PC/internet para fins educacionais?', type: 'select', block: 8, options: ['Sim','Não'] },

  // ── BLOCO 9: PARTICIPAÇÃO SOCIAL ──────────────────────────────────────────
  { id: 'campo_84',           label: '84. Participa de organizações locais? (Marque todas que se aplicam)', type: 'multicheck', block: 9,
    options: ['Associação de moradores','Cooperativa','Sindicato','Igreja/Grupo religioso','ONG','Nenhuma','Outro'] },
  { id: 'campo_85',           label: '85. Se sim, qual organização',              type: 'text',   block: 9 },

  // ── BLOCO 10: ACESSO A POLÍTICAS PÚBLICAS ─────────────────────────────────
  { id: 'campo_86',           label: '86. Antes deste projeto, já acessou política pública de apoio à produção/renda?', type: 'select', block: 10, options: ['Sim','Não'] },
  { id: 'campo_87',           label: '87. Quais políticas públicas você já acessou?', type: 'text', block: 10 },
  { id: 'campo_88',           label: '88. Como foi seu acesso a essas políticas?', type: 'text', block: 10 },
  { id: 'campo_89',           label: '89. Principais dificuldades para acessar políticas públicas:', type: 'text', block: 10 },
  { id: 'campo_90',           label: '90. Que política pública faria mais diferença para sua atividade hoje', type: 'text', block: 10 },
  { id: 'campo_91',           label: '91. Você acredita que este projeto pode melhorar seu acesso a políticas públicas?', type: 'select', block: 10, options: ['Sim','Não','Talvez'] },

  // ── BLOCO 11: HISTÓRICO DE EMPREGO ────────────────────────────────────────
  { id: 'campo_92',           label: '92. Qtd. empregos últimos 2 anos',          type: 'number', block: 11 },
  { id: 'campo_93',           label: '93. Área de atuação principal',             type: 'text',   block: 11 },
  { id: 'campo_94',           label: '94. Motivo de saída do último emprego',     type: 'text',   block: 11 },
  { id: 'campo_95',           label: '95. Já realizou curso/capacitação para o mercado de trabalho?', type: 'select', block: 11, options: ['Sim','Não'] },
  { id: 'campo_96',           label: '96. Se sim, quais cursos',                  type: 'text',   block: 11 },
  { id: 'campo_97',           label: '97. Já realizou curso/capacitação para sua atividade produtiva?', type: 'select', block: 11, options: ['Sim','Não'] },
  { id: 'campo_98',           label: '98. Se sim, quais cursos',                  type: 'text',   block: 11 },

  // ── BLOCO 12: EXPECTATIVAS ────────────────────────────────────────────────
  { id: 'campo_99',           label: '99. Qual sua principal expectativa em relação ao curso', type: 'text', block: 12 },
  { id: 'campo_100',          label: '100. Como pretende aplicar os conhecimentos adquiridos', type: 'text', block: 12 },

  // ── DECLARAÇÃO / ASSINATURA ───────────────────────────────────────────────
  { id: 'campo_101',          label: '101. Declaro que li e aceito os termos acima *', type: 'select', block: 13, options: ['Sim','Não'] },
  { id: 'campo_assinatura',   label: 'Assinatura do Aluno — Nome Completo *',     type: 'text',   block: 13 },
  { id: 'campo_102',          label: '102. Data de preenchimento *',              type: 'date',   block: 13 },

  // ── CAMPO OPERADOR (não extraído pelo OCR, preenchido manualmente) ──────────
  { id: 'campo_cadunico_verificado', label: 'Verificação CadÚnico', type: 'select', block: 0,
    options: ['Não verificado', 'Inscrito', 'Não inscrito', 'Pendente'], operator: true },
];

// Nomes das colunas para o cabeçalho do CSV/Sheets (na ordem exata)
export const COLUMN_HEADERS = FORM_FIELDS.map(f => f.label);

// Mapa id → field para acesso rápido
export const FIELD_MAP = Object.fromEntries(FORM_FIELDS.map(f => [f.id, f]));

// Blocos para organizar o formulário manual
export const BLOCKS = {
  0:  { title: '📋 Identificação do Curso', color: '#6366f1' },
  1:  { title: '👤 Bloco 1 — Dados Pessoais e Endereço', color: '#3b82f6' },
  2:  { title: '⚕️ Bloco 2 — Saúde e Vulnerabilidade Social', color: '#10b981' },
  3:  { title: '🏠 Bloco 3 — Composição Familiar e Moradia', color: '#f59e0b' },
  4:  { title: '💼 Bloco 4 — Situação Ocupacional e Renda', color: '#ef4444' },
  5:  { title: '🌾 Bloco 5 — Atividade Produtiva', color: '#8b5cf6' },
  6:  { title: '🏦 Bloco 6 — Finanças e Crédito', color: '#06b6d4' },
  7:  { title: '🩺 Bloco 7 — Saúde', color: '#ec4899' },
  8:  { title: '💻 Bloco 8 — Acesso a Tecnologias', color: '#14b8a6' },
  9:  { title: '🤝 Bloco 9 — Participação Social', color: '#f97316' },
  10: { title: '📜 Bloco 10 — Acesso a Políticas Públicas', color: '#84cc16' },
  11: { title: '🏢 Bloco 11 — Histórico de Emprego', color: '#a855f7' },
  12: { title: '🎯 Bloco 12 — Expectativas', color: '#0ea5e9' },
  13: { title: '✍️ Declaração e Assinatura', color: '#64748b' },
};
