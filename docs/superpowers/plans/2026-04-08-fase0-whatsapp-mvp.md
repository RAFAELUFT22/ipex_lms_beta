# Fase 0 — WhatsApp MVP TDS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Colocar o agente WhatsApp TDS totalmente funcional hoje, antes da atividade de campo de 09/04/2026.

**Architecture:** Chatwoot (WhatsApp Cloud API) → Agent Bot webhook → n8n → AnythingLLM RAG → resposta automática; escalamento com label `escalonado` para estagiários supervisionarem via Chatwoot.

**Tech Stack:** Chatwoot REST API, n8n webhook, AnythingLLM REST API, curl, Python3

---

## Estado atual descoberto (08/04/2026)

| Componente | Status | Observação |
|---|---|---|
| N8N container | ✅ healthy | |
| Chatwoot container | ✅ healthy | |
| AnythingLLM | ✅ healthy | workspace `tds` existe |
| Agent Bot "Tutor IA" | ✅ existe | ID=1, NÃO atribuído à inbox |
| Workflow Chatwoot RAG | ✅ ativo | ID: XYcnRlPZSlfGXOWb, webhook: `chatwoot-kreativ` |
| Inbox "WhatsApp TDS" | ⚠️ Channel::Api | precisa virar Channel::Whatsapp |
| Labels Chatwoot | ⚠️ parcial | faltam: `pre-matricula`, `baseline`, `escalonado` |
| Time "Equipe TDS" | ❌ não existe | criar |
| Docs formulários no RAG | ❌ não existem | criar e fazer upload |

---

## Credenciais (todas em /root/kreativ-setup/.env.real)

```bash
CHATWOOT_URL=https://chat.ipexdesenvolvimento.cloud
CHATWOOT_TOKEN=w8BYLTQc1s5VMowjQw433rGy     # access_token do admin (obtido via sign_in — se expirar, renovar com POST /auth/sign_in)
CHATWOOT_ACCOUNT=1
CHATWOOT_INBOX_ID=1
CHATWOOT_BOT_ID=1                            # Agent Bot "Tutor IA"
N8N_WORKFLOW_ID=XYcnRlPZSlfGXOWb
N8N_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # ver .env.real
RAG_URL=https://rag.ipexdesenvolvimento.cloud
RAG_API_KEY=W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0
RAG_WORKSPACE=tds
```

---

## Task 1: Criar documento formulario-pre-matricula.md

**Files:**
- Create: `/root/projeto-tds/docs/rag/formulario-pre-matricula.md`

- [ ] **Step 1: Criar o arquivo**

```bash
mkdir -p /root/projeto-tds/docs/rag
```

- [ ] **Step 2: Escrever o conteúdo**

Criar `/root/projeto-tds/docs/rag/formulario-pre-matricula.md` com o seguinte conteúdo:

```markdown
# Formulário de Pré-Matrícula TDS — Guia Completo

## O que é este formulário?
O Formulário de Pré-Matrícula é o primeiro passo para participar dos cursos do 
Programa TDS (Território de Desenvolvimento Social e Inclusão Produtiva).
É simples, tem 4 partes e leva cerca de 5 minutos para preencher.

Link para acessar: https://forms.gle/SrtyUw8vmgKLWvuM6

## Parte 1 — Dados Pessoais

**E-mail:** Endereço de e-mail. Se não tiver, pode colocar o de um familiar ou deixar em branco e informar ao aplicador.

**Nome completo:** Seu nome como está no RG ou CPF.

**Data de nascimento:** Dia, mês e ano em que você nasceu. Exemplo: 15/03/1985.

**Idade:** Será calculada automaticamente a partir da data de nascimento.

**Gênero:** Marque uma opção:
- Feminino
- Masculino  
- Prefiro não dizer

**CPF:** Número do seu Cadastro de Pessoa Física. Fica no cartão CPF ou no RG.
Formato: 000.000.000-00

**Telefone/WhatsApp com DDD:** Seu número de celular incluindo o código da cidade.
Exemplo: (63) 99999-1234

## Parte 2 — Endereço

**Endereço:** Nome da sua rua, avenida ou travessa, com o número da casa.
Exemplo: Rua das Mangueiras, 42

**CEP:** O código postal da sua cidade. Se não souber, o aplicador pode ajudar.

**Cidade:** Nome do município onde você mora.

**Estado:** Sigla do estado. Para quem está no Tocantins: TO

## Parte 3 — Curso de Interesse

Escolha o curso que mais combina com você. Você pode marcar mais de um.

**Crédito e Cooperativismo**
Aprenda sobre cooperativismo e como acessar microcrédito para fortalecer 
sua renda e comunidade.

**Produção Audiovisual**
Aprenda a gravar vídeos, criar roteiros e divulgar conteúdo nas redes sociais.

**Educação Financeira**
Aprenda a organizar seu dinheiro, fazer planejamento e tomar decisões financeiras melhores.

**Planejamento Produtivo**
Aprenda a planejar e gerenciar sua produção, controlar custos e vender melhor.

**Inteligência Artificial e Inclusão Digital**
Aprenda informática básica, ferramentas digitais e como usar IA no dia a dia.

**Educação Financeira para Idosos**
Voltado especialmente para pessoas acima de 60 anos: como proteger seu dinheiro e 
evitar golpes.

**Culinária Saudável**
Aprenda receitas nutritivas, aproveitamento integral dos alimentos e alimentação saudável 
com ingredientes locais.

## Parte 4 — Disponibilidade de Horários

Marque os dias e horários em que você pode fazer o curso:
- De Segunda a Sexta - Tempo Integral
- De Segunda a Sexta - Manhã
- De Segunda a Sexta - Tarde
- De Segunda a Sexta - Noite
- Finais de Semana - Manhã e Tarde
- Finais de Semana - Manhã
- Finais de Semana - Tarde

## Perguntas frequentes sobre o formulário

**Precisa ter celular para preencher?**
Não. O aplicador pode preencher pelo celular ou tablet dele junto com você.

**Precisa ter internet?**
Sim, para enviar o formulário. Mas o aplicador já tem acesso.

**Posso me inscrever em mais de um curso?**
Sim, pode marcar mais de um curso de interesse.

**Quem pode se inscrever?**
Beneficiários do CadÚnico morando nos municípios atendidos pelo TDS no Tocantins 
(Bico do Papagaio e Jalapão), com 18 anos ou mais.

**Os cursos são pagos?**
Não. Todos os cursos do TDS são gratuitos.

**Vou receber certificado?**
Sim. Quem completar o curso com pelo menos 75% de presença recebe certificado 
da Universidade Federal do Tocantins (UFT), reconhecido pelo MDS.

**Quanto tempo dura o curso?**
De 40 a 80 horas, dependendo do curso escolhido.
```

- [ ] **Step 3: Verificar o arquivo criado**

```bash
wc -l /root/projeto-tds/docs/rag/formulario-pre-matricula.md
```

Esperado: mais de 80 linhas

---

## Task 2: Criar documento formulario-baseline-tds.md

**Files:**
- Create: `/root/projeto-tds/docs/rag/formulario-baseline-tds.md`

- [ ] **Step 1: Escrever o conteúdo**

Criar `/root/projeto-tds/docs/rag/formulario-baseline-tds.md`:

```markdown
# Formulário de Inscrição Individual — Baseline TDS — Guia de Preenchimento

## O que é este formulário?
Este é o formulário completo de inscrição do Programa TDS. Tem 11 blocos de perguntas 
(18 seções) e é preenchido com apoio do aplicador de campo. Leva cerca de 30–40 minutos.

---

## Glossário de Termos Técnicos

**CadÚnico / Cadastro Único:** Cadastro do Governo Federal para famílias de baixa renda.
Quem tem CadÚnico pode acessar programas como Bolsa Família. O número NIS fica 
no cartão do CadÚnico ou pode ser consultado no CRAS.

**NIS:** Número de Identificação Social. É o número do CadÚnico, com 11 dígitos.
Exemplo: 12345678901

**DAP / CAF:** Declaração de Aptidão ao Pronaf / Cadastro da Agricultura Familiar.
Documento que comprova que a pessoa é agricultora familiar. Emitido na Emater ou Sindicato Rural.

**PAA:** Programa de Aquisição de Alimentos. O governo compra alimentos de 
agricultores familiares para distribuir para escolas e entidades.

**PNAE:** Programa Nacional de Alimentação Escolar. Compra alimentos de 
agricultores para merenda escolar.

**SINE:** Sistema Nacional de Emprego. Serviço gratuito que ajuda a encontrar emprego.
Presente nas prefeituras de muitos municípios.

**BPC:** Benefício de Prestação Continuada. Benefício pago pelo INSS para idosos 
acima de 65 anos ou pessoas com deficiência que comprovem baixa renda.

**Pronaf B:** Linha de crédito rural do Banco do Brasil para pequenos agricultores 
familiares com renda muito baixa.

**ATER:** Assistência Técnica e Extensão Rural. Serviço gratuito de orientação técnica 
para agricultores, oferecido por Emater, Seagro e outros órgãos.

**MEI:** Microempreendedor Individual. Pessoa que tem CNPJ próprio com faturamento 
anual de até R$ 81 mil. Facilita emitir nota fiscal e acessar crédito.

---

## BLOCO 1 — Dados do Curso

**Q1. Qual curso?**
Nome do curso em que o participante está se inscrevendo. Opções disponíveis:
- Crédito e Cooperativismo
- Produção Audiovisual
- Educação Financeira
- Planejamento Produtivo
- Inteligência Artificial e Inclusão Digital
- Educação Financeira para Idosos
- Culinária Saudável

**Q2. Carga Horária:** Número de horas do curso. Os cursos TDS têm de 40 a 80 horas.

**Q3. Data de Início:** Quando o curso começa. O aplicador preenche.

**Q4. Previsão de Término:** Quando o curso deve terminar. O aplicador preenche.

**Q5. Local:** Onde as aulas vão acontecer. O aplicador preenche.

---

## BLOCO 2 — Dados Básicos e Identificação

**Q6. Nome Completo:** Nome como está no documento oficial (RG ou CPF).

**Q7. Data de Nascimento:** Dia, mês e ano. Exemplo: 14/05/1975.

**Q8. Mais de 60 anos?** Calculado automaticamente. Apenas confirmar.

**Q9. CPF:** 11 dígitos. Fica no cartão CPF, RG ou aplicativo Gov.br.

**Q10. RG:** Número do Registro Geral. Fica na Carteira de Identidade.

**Q11. Naturalidade:** Cidade onde nasceu. Exemplo: Araguaína - TO.

**Q12. Estado Civil:** 
- Solteiro(a): nunca casou
- Casado(a): casamento no cartório
- União estável: mora junto com companheiro(a) sem ter casado no cartório
- Divorciado(a): foi casado e separou legalmente
- Viúvo(a): o cônjuge faleceu

**Q13. Gênero:** Masculino, Feminino, ou Outro.

**Q14. Cor/Raça (critério IBGE):**
- Branca
- Preta
- Parda: mistura de raças
- Indígena: pertence a povo indígena
- Amarela: descendência asiática
- Prefere não declarar

**Q15. Quilombola:** Pertence a comunidade remanescente de quilombo.

**Q16. Telefone:** Com DDD. Exemplo: (63) 99999-1234. Colocar o WhatsApp se tiver.

**Q17. E-mail:** Endereço eletrônico. Opcional — deixar em branco se não tiver.

---

## BLOCO 2 — Endereço Residencial (Q18–Q24)

**Q18. Logradouro:** Nome da rua, avenida, travessa, ou "Sítio [nome]" para zona rural.

**Q19. Número:** Número da casa. Se não tiver número, colocar "S/N" (sem número).

**Q20. Bairro / Assentamento:** Nome do bairro, vila, assentamento ou comunidade rural.

**Q21. Complemento:** Informação adicional. Exemplo: "casa dos fundos", "apto 2".

**Q22. CEP:** 8 dígitos. Exemplo: 77800-000. Se não souber, o aplicador consulta.

**Q23. Município:** Nome da cidade onde mora.

**Q24. Estado:** Para Tocantins: TO

---

## BLOCO 3 — Educação e Acessibilidade (Q25–Q28)

**Q25. Escolaridade:**
- Nunca estudou
- Ens. Fund. Incompleto: não terminou o fundamental (1º ao 9º ano)
- Ens. Fund. Completo: terminou o fundamental
- Ens. Médio Incompleto: não terminou o ensino médio
- Ens. Médio Completo: tem o diploma do ensino médio
- Ensino Técnico: fez curso técnico profissionalizante
- Ens. Superior Incompleto: está ou esteve na faculdade mas não terminou
- Ens. Superior Completo: tem diploma universitário
- Pós-Graduado: fez especialização, mestrado ou doutorado

**Q26–28. Deficiência e atendimento especial:**
Informar se tem deficiência física, visual, auditiva, intelectual ou múltipla.
Se precisar de adaptação para participar das aulas, descrever qual.

---

## BLOCO 4 — Perfil Socioeconômico SISEC/MDS (Q29–Q44)

São 15 perguntas de Sim ou Não sobre situação de trabalho e programas sociais.
Cada uma tem espaço para observação (ex: NIS do CadÚnico, número do SINE).

**Q31. CadÚnico:** Dizer Sim se a família está cadastrada. Anotar o NIS na observação.

**Q44. Benefícios Sociais:** Marcar todos que recebe:
- Bolsa Família: benefício mensal para famílias de baixa renda
- BPC: para idosos 65+ ou pessoas com deficiência
- Tarifa Social: desconto na conta de energia elétrica
- Nenhum

---

## BLOCO 5 — Composição Familiar e Habitação (Q45–Q56)

**Q45–Q49.** Número de pessoas na casa, separado por faixa etária.

**Q50. Tipo de residência:**
- Própria quitada: a família é dona e não tem financiamento
- Própria financiada: está pagando ainda
- Alugada: paga aluguel todo mês
- Cedida: mora sem pagar e sem ser dono (ex: casa de parente)

**Q51. Material das paredes:** Alvenaria (tijolo), madeira, taipa (barro), outro.

**Q52–Q56.** Acesso a serviços básicos: água tratada, energia elétrica, coleta de lixo,
internet, e se tem banheiro dentro de casa.

---

## BLOCO 6 — Renda e Ocupação (Q57–Q61)

**Q57. Situação ocupacional:**
- Desempregado: está buscando trabalho
- Empreendedor informal: trabalha por conta sem CNPJ
- MEI: tem CNPJ de microempreendedor
- Autônomo: presta serviços sem carteira ou CNPJ
- Empregado com carteira: tem registro em carteira de trabalho
- Empregado sem carteira: trabalha mas não tem carteira assinada
- Agricultor familiar: produz alimentos na propriedade rural
- Trabalho eventual/bico: faz serviços ocasionais

**Q58 e Q60. Faixas de renda:** Marcar a faixa que mais se aproxima da renda mensal.

**Q59 e Q61. Valor exato:** Colocar o valor real se souber. Aproximado está bom.

---

## BLOCO 7 — Atividade Produtiva (Q62–Q71)

Preencher apenas se a pessoa desenvolve alguma atividade produtiva.

**Q63. Tipo de atividade:**
- Agropecuária: criação de animais, roça, horta, pomar
- Artesanato: bordado, cerâmica, bijuteria, trabalhos manuais
- Serviços: corte de cabelo, costura, limpeza, manutenção
- Comércio: venda de produtos em casa, banca, mercadinho
- Transporte: mototaxi, carreteiro, frete

**Q66. DAP/CAF:** Documento da Emater que comprova ser agricultor familiar.
Dizer Sim se tem, Não se não tem.

**Q67. Destino da produção:**
- Consumo próprio: para a família comer
- Venda local: vende para vizinhos, no município
- Feiras: feiras livres ou da agricultura familiar
- PAA/PNAE: vende para o governo (escola, CRAS)

---

## BLOCO 8 — Acesso a Crédito (Q72–Q76)

**Q72. Conta bancária:** Banco como BB, Caixa, Bradesco, Itaú, etc.

**Q73. Conta digital:** Nubank, Picpay, Mercado Pago, conta da Caixa no app, etc.

**Q74. Microcrédito:** Empréstimo de pequeno valor para produção. 
Instituições: Credibel, Banco da Família, Agroamigo, Pronaf B.

---

## BLOCO 9 — Saúde e Uso de Tecnologia (Q77–Q83)

**Q77. Plano de saúde:** Plano particular de saúde (diferente do SUS).

**Q78. SUS:** Se usa o Sistema Único de Saúde regularmente (UBS, CRAS, hospital público).

**Q81–Q83. Tecnologia:** Se tem celular próprio, se acessa internet, se já usou 
computador ou internet para estudar.

---

## BLOCO 10 — Território e Políticas Públicas (Q84–Q91)

**Q84. Organizações:** Associação de moradores, cooperativa, grupo de mulheres, etc.

**Q86–Q88. Políticas públicas:** Se já acessou algum programa antes do TDS.
Exemplos: PAA, PNAE, Pronaf, ATER, crédito rural.

**Q91. Expectativa com o projeto:** Se acredita que o TDS vai melhorar o acesso 
a políticas públicas.

---

## BLOCO 11 — Histórico Profissional e Expectativas (Q92–Q102)

**Q92. Empregos:** Quantos empregos teve nos últimos 2 anos.

**Q95/Q97. Capacitações:** Se já fez algum curso de qualificação antes.

**Q99. Expectativa:** O que espera aprender ou conquistar com o curso.

**Q100. Como aplicar:** Como pretende usar o que vai aprender.

**Declaração (Q101–Q102):** Confirmar que as informações são verdadeiras e 
aceitar a frequência mínima de 75% para receber o certificado.

---

## Perguntas frequentes sobre o Baseline

**Por que tem tantas perguntas?**
O formulário completo é exigido pela UFT e pelo MDS para comprovar que o projeto
está atendendo o público correto e para emitir os certificados.

**Sou obrigado a responder tudo?**
Não. Campos marcados com asterisco (*) são obrigatórios. Os demais são opcionais.

**Meus dados são protegidos?**
Sim. Todos os dados são tratados com sigilo conforme a LGPD (Lei nº 13.709/2018).
Só a equipe do projeto TDS tem acesso.
```

- [ ] **Step 2: Verificar o arquivo**

```bash
wc -l /root/projeto-tds/docs/rag/formulario-baseline-tds.md
```

Esperado: mais de 200 linhas

---

## Task 3: Upload dos documentos no AnythingLLM

**Files:** nenhum — apenas chamadas de API

- [ ] **Step 1: Upload formulario-pre-matricula.md**

```bash
curl -s -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/document/raw-text" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d "{
    \"textContent\": $(python3 -c "import json; print(json.dumps(open('/root/projeto-tds/docs/rag/formulario-pre-matricula.md').read()))"),
    \"metadata\": {\"title\": \"Formulário de Pré-Matrícula TDS\", \"docAuthor\": \"TDS\", \"description\": \"Guia de preenchimento do formulário de pré-matrícula\"}
  }" | python3 -m json.tool
```

Esperado: `{"success": true, "documents": [{"id": "...", "title": "...", ...}]}`

Guardar o `location` retornado — exemplo: `custom-documents/formulario-pre-matricula.md-abc123.json`

- [ ] **Step 2: Upload formulario-baseline-tds.md**

```bash
curl -s -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/document/raw-text" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d "{
    \"textContent\": $(python3 -c "import json; print(json.dumps(open('/root/projeto-tds/docs/rag/formulario-baseline-tds.md').read()))"),
    \"metadata\": {\"title\": \"Formulário Baseline TDS — Guia de Preenchimento\", \"docAuthor\": \"TDS\", \"description\": \"Guia dos 11 blocos do formulário de inscrição individual baseline\"}
  }" | python3 -m json.tool
```

Esperado: `{"success": true, ...}`

- [ ] **Step 3: Adicionar os documentos ao workspace `tds`**

```bash
# Listar documentos disponíveis para obter os slugs
curl -s "https://rag.ipexdesenvolvimento.cloud/api/v1/documents" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
for item in d.get('localFiles',{}).get('items',[]):
    for doc in item.get('items',[]):
        if 'formulario' in doc.get('name','').lower():
            print(doc['name'])
"
```

Copiar os nomes dos dois arquivos `formulario-*.json` retornados.

- [ ] **Step 4: Embedar os documentos no workspace `tds`**

```bash
# Substituir <DOC1> e <DOC2> pelos nomes retornados no step anterior
curl -s -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/update-embeddings" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d "{
    \"adds\": [\"custom-documents/<DOC1>\", \"custom-documents/<DOC2>\"],
    \"deletes\": []
  }" | python3 -m json.tool
```

Esperado: `{"workspace": {...}, "message": "Embeddings for tds updated"}`

- [ ] **Step 5: Verificar com query de teste**

```bash
curl -s -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d '{"message": "O que é NIS e onde encontro?", "mode": "query"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Sources:', len(d.get('sources',[]))); print(d.get('textResponse','')[:300])"
```

Esperado: `Sources: 1` ou mais, com resposta mencionando NIS/CadÚnico

---

## Task 4: Criar labels no Chatwoot

**Files:** nenhum

Labels existentes: agricultura, aguardando-tutor, artesanato, certificado, cooperativismo, empreendedorismo, prova, tdstest, tecnologia

Labels a criar: `pre-matricula`, `baseline`, `escalonado`

- [ ] **Step 1: Criar label `pre-matricula`**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/labels" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"title": "pre-matricula", "description": "Dúvida sobre inscrição ou pré-matrícula", "color": "#4CAF50", "show_on_sidebar": true}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('payload',{}).get('id') else d)"
```

Esperado: `OK`

- [ ] **Step 2: Criar label `baseline`**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/labels" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"title": "baseline", "description": "Dúvida sobre formulário baseline (18 seções)", "color": "#2196F3", "show_on_sidebar": true}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('payload',{}).get('id') else d)"
```

Esperado: `OK`

- [ ] **Step 3: Criar label `escalonado`**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/labels" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"title": "escalonado", "description": "Bot não soube responder — aguarda humano", "color": "#FF5722", "show_on_sidebar": true}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('payload',{}).get('id') else d)"
```

Esperado: `OK`

- [ ] **Step 4: Verificar as 3 labels foram criadas**

```bash
curl -s "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/labels" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" | \
  python3 -c "import sys,json; [print(l['title']) for l in json.load(sys.stdin).get('payload',[])]"
```

Esperado: lista incluindo `pre-matricula`, `baseline`, `escalonado`

---

## Task 5: Criar Time "Equipe TDS" no Chatwoot

**Files:** nenhum

Agentes existentes: Admin TDS (ID:1), Atendimento TDS (ID:4), Coordenação TDS (ID:3), Rafael Luciano (ID:2)

- [ ] **Step 1: Criar o time**

```bash
TEAM_RESP=$(curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/teams" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"name": "Equipe TDS", "description": "Estagiários e coordenadores do programa TDS"}')
echo $TEAM_RESP | python3 -m json.tool
TEAM_ID=$(echo $TEAM_RESP | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Team ID: $TEAM_ID"
```

Esperado: JSON com `id` numérico (ex: `1`)

- [ ] **Step 2: Adicionar todos os agentes ao time**

```bash
# Substitua TEAM_ID pelo valor obtido no step anterior
TEAM_ID=1  # ajustar se necessário

curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/teams/$TEAM_ID/team_members" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [1, 2, 3, 4]}' | python3 -m json.tool
```

Esperado: lista dos 4 agentes

- [ ] **Step 3: Atribuir o time à inbox "WhatsApp TDS"**

```bash
curl -s -X PATCH "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inbox_members/1" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [1, 2, 3, 4]}' | python3 -m json.tool
```

Esperado: JSON confirmando os membros

---

## Task 6: Atribuir Agent Bot "Tutor IA" à inbox

O Agent Bot "Tutor IA" (ID: 1) existe mas não está atribuído à inbox "WhatsApp TDS" (ID: 1).

- [ ] **Step 1: Atribuir o agent bot à inbox**

```bash
curl -s -X PATCH "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/1" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"channel": {}, "agent_bot": 1}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('agent_bot:', d.get('agent_bot'))"
```

Esperado: `agent_bot: 1` (ou similar indicando que foi atribuído)

- [ ] **Step 2: Verificar a atribuição**

```bash
curl -s "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/1" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('agent_bot:', d.get('agent_bot')); print('channel_type:', d.get('channel_type'))"
```

Esperado: `agent_bot: 1` (não null)

---

## Task 7: Melhorar workflow n8n (escalação com label + confiança)

O workflow atual não: (a) adiciona label `escalonado` ao escalar; (b) verifica confiança do RAG.

**Files:**
- Modify: workflow n8n ID `XYcnRlPZSlfGXOWb` via API

- [ ] **Step 1: Baixar o workflow atual**

```bash
curl -s "https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows/XYcnRlPZSlfGXOWb" \
  -H "X-N8N-API-KEY: $(grep N8N_API_KEY /root/kreativ-setup/.env.real | cut -d= -f2-)" \
  > /tmp/workflow-chatwoot-rag.json
echo "Nodes:"
python3 -c "import json; [print(' -', n['name']) for n in json.load(open('/tmp/workflow-chatwoot-rag.json'))['nodes']]"
```

Esperado: lista com 9 nodes

- [ ] **Step 2: Atualizar código do nó "Extrair Dados Chatwoot"**

Abrir o arquivo `/tmp/workflow-chatwoot-rag.json` e localizar o node com `"name": "Extrair Dados Chatwoot"`. Substituir o campo `jsCode` pelo seguinte código atualizado (remove `cadunico` do handoff pattern e mantém CadÚnico para o RAG responder):

```javascript
const input = $input.first().json;
const body = input.body || input;

// Ignorar eventos que não sejam criação de mensagem
if (body.event && body.event !== 'message_created') {
  return [];
}

// Ignorar mensagens do bot ou de agentes humanos
const msgType = String(body.message_type ?? body.message?.message_type ?? '');
if (msgType === 'outgoing' || msgType === '1') return [];

const senderType = String(body.sender?.type ?? '');
if (senderType === 'agent_bot' || senderType === 'user') return [];

// sessionId = telefone do contato (garante memória por aluno)
const sessionId = String(
  body.meta?.sender?.identifier ||
  body.sender?.phone_number ||
  body.conversation?.meta?.sender?.identifier ||
  body.contact?.phone_number ||
  ''
);

const conversationId = String(body.conversation?.id || '');
const accountId      = String(body.conversation?.account_id || '1');
const contactName    = String(body.meta?.sender?.name || body.sender?.name || '');
const contentType    = String(body.content_type ?? body.message?.content_type ?? 'text');
const messageText    = String(body.content || body.message?.content || '').trim();

// Áudio → rota especial
if (contentType === 'audio' || contentType === 'voice') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'audio' } }];
}

// Imagem / arquivo → redirecionar
if (contentType === 'image' || contentType === 'file' || contentType === 'sticker') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'media' } }];
}

// Palavras-chave de handoff — REMOVIDO: cadunico (o RAG responde sobre CadÚnico)
const handoffPattern = /tutor|prova|exame|humano|operador|atendente|reclama[cç][aã]o|ajuda humana|falar com algu[eé]m|n[aã]o consigo|problema t[eé]cnico/i;
const route = handoffPattern.test(messageText) ? 'handoff' : 'rag';

return [{ json: { conversationId, accountId, sessionId, contactName, messageText, route } }];
```

Fazer o update usando Python:

```bash
python3 << 'EOF'
import json

NEW_CODE = r"""const input = $input.first().json;
const body = input.body || input;
if (body.event && body.event !== 'message_created') { return []; }
const msgType = String(body.message_type ?? body.message?.message_type ?? '');
if (msgType === 'outgoing' || msgType === '1') return [];
const senderType = String(body.sender?.type ?? '');
if (senderType === 'agent_bot' || senderType === 'user') return [];
const sessionId = String(body.meta?.sender?.identifier || body.sender?.phone_number || body.conversation?.meta?.sender?.identifier || body.contact?.phone_number || '');
const conversationId = String(body.conversation?.id || '');
const accountId = String(body.conversation?.account_id || '1');
const contactName = String(body.meta?.sender?.name || body.sender?.name || '');
const contentType = String(body.content_type ?? body.message?.content_type ?? 'text');
const messageText = String(body.content || body.message?.content || '').trim();
if (contentType === 'audio' || contentType === 'voice') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'audio' } }];
}
if (contentType === 'image' || contentType === 'file' || contentType === 'sticker') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'media' } }];
}
const handoffPattern = /tutor|prova|exame|humano|operador|atendente|reclama[cç][aã]o|ajuda humana|falar com algu[eé]m|n[aã]o consigo|problema t[eé]cnico/i;
const route = handoffPattern.test(messageText) ? 'handoff' : 'rag';
return [{ json: { conversationId, accountId, sessionId, contactName, messageText, route } }];"""

with open('/tmp/workflow-chatwoot-rag.json') as f:
    wf = json.load(f)

for node in wf['nodes']:
    if node['name'] == 'Extrair Dados Chatwoot':
        node['parameters']['jsCode'] = NEW_CODE
        print('Updated: Extrair Dados Chatwoot')

with open('/tmp/workflow-chatwoot-rag-updated.json', 'w') as f:
    json.dump(wf, f)
print('Saved to /tmp/workflow-chatwoot-rag-updated.json')
EOF
```

- [ ] **Step 3: Adicionar nó "Etiquetar Escalonado" e nó "Verificar Confiança RAG"**

```bash
python3 << 'EOF'
import json

with open('/tmp/workflow-chatwoot-rag-updated.json') as f:
    wf = json.load(f)

# Obter posição do nó "Desatribuir Conversa" para posicionar novo nó próximo
desat_node = next(n for n in wf['nodes'] if n['name'] == 'Desatribuir Conversa')
dx, dy = desat_node['position'][0], desat_node['position'][1]

# Novo nó: Etiquetar Escalonado
label_node = {
    "id": "node-etiquetar-escalonado",
    "name": "Etiquetar Escalonado",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [dx + 300, dy],
    "parameters": {
        "method": "POST",
        "url": "={{ 'https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/' + $('Extrair Dados Chatwoot').item.json.accountId + '/conversations/' + $('Extrair Dados Chatwoot').item.json.conversationId + '/labels' }}",
        "specifyBody": "json",
        "jsonBody": "={{ { \"labels\": [\"escalonado\"] } }}",
        "headerParameters": {
            "parameters": [
                {"name": "api_access_token", "value": "w8BYLTQc1s5VMowjQw433rGy"},
                {"name": "Content-Type", "value": "application/json"}
            ]
        },
        "options": {}
    }
}

# Novo nó: Verificar Confiança RAG (IF após "Consultar RAG")
rag_node = next(n for n in wf['nodes'] if n['name'] == 'Consultar RAG')
rx, ry = rag_node['position'][0], rag_node['position'][1]

confidence_node = {
    "id": "node-verificar-confianca",
    "name": "Verificar Confiança RAG",
    "type": "n8n-nodes-base.if",
    "typeVersion": 2,
    "position": [rx + 250, ry],
    "parameters": {
        "conditions": {
            "options": {"caseSensitive": False},
            "combinator": "or",
            "conditions": [
                {
                    "id": "cond-no-sources",
                    "operator": {"type": "number", "operation": "equals"},
                    "leftValue": "={{ $json.sources.length }}",
                    "rightValue": 0
                },
                {
                    "id": "cond-low-confidence",
                    "operator": {"type": "string", "operation": "contains"},
                    "leftValue": "={{ $json.textResponse }}",
                    "rightValue": "não tenho informação"
                },
                {
                    "id": "cond-low-confidence2",
                    "operator": {"type": "string", "operation": "contains"},
                    "leftValue": "={{ $json.textResponse }}",
                    "rightValue": "não sei responder"
                }
            ]
        }
    }
}

wf['nodes'].append(label_node)
wf['nodes'].append(confidence_node)

with open('/tmp/workflow-chatwoot-rag-updated.json', 'w') as f:
    json.dump(wf, f)
print('Added 2 nodes. Total nodes:', len(wf['nodes']))
EOF
```

- [ ] **Step 4: Fazer PUT do workflow atualizado no n8n**

```bash
N8N_KEY=$(grep N8N_API_KEY /root/kreativ-setup/.env.real | cut -d= -f2-)

# O n8n PUT exige apenas os campos nodes, connections, settings, staticData
python3 -c "
import json
wf = json.load(open('/tmp/workflow-chatwoot-rag-updated.json'))
payload = {
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': wf.get('settings', {}),
    'staticData': wf.get('staticData', None)
}
print(json.dumps(payload))
" > /tmp/workflow-put-payload.json

curl -s -X PUT "https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows/XYcnRlPZSlfGXOWb" \
  -H "X-N8N-API-KEY: $N8N_KEY" \
  -H "Content-Type: application/json" \
  --data @/tmp/workflow-put-payload.json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('OK, nodes:', len(d.get('nodes',[])))"
```

Esperado: `OK, nodes: 11`

- [ ] **Step 5: Ativar o workflow (caso tenha ficado inativo)**

```bash
N8N_KEY=$(grep N8N_API_KEY /root/kreativ-setup/.env.real | cut -d= -f2-)
curl -s -X POST "https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows/XYcnRlPZSlfGXOWb/activate" \
  -H "X-N8N-API-KEY: $N8N_KEY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('active:', d.get('active'))"
```

Esperado: `active: True`

- [ ] **Step 6: Commit**

```bash
cd /root/projeto-tds
git add docs/rag/
git commit -m "docs: adiciona docs RAG dos formulários pré-matrícula e baseline TDS

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Configurar WhatsApp Cloud API no Chatwoot

Esta tarefa requer credenciais Meta (Phone Number ID + WhatsApp Access Token).

- [ ] **Step 1: Obter credenciais Meta**

No Meta Business Manager (business.facebook.com):
1. Apps → selecionar app TDS → WhatsApp → Começar
2. Anotar:
   - `Phone Number ID` (ex: `123456789012345`)
   - `WhatsApp Business Account ID`
   - Gerar token: System User → gerar token permanente com permissão `whatsapp_business_messaging`

- [ ] **Step 2: Criar nova inbox WhatsApp no Chatwoot**

```bash
# Substituir <PHONE_NUMBER_ID> e <WA_TOKEN> pelos valores obtidos
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WhatsApp TDS Cloud",
    "channel": {
      "type": "whatsapp",
      "phone_number": "+55SEUNUMERO",
      "provider": "whatsapp_cloud",
      "provider_config": {
        "api_key": "<WA_TOKEN>",
        "phone_number_id": "<PHONE_NUMBER_ID>",
        "business_account_id": "<WA_BUSINESS_ACCOUNT_ID>"
      }
    }
  }' | python3 -m json.tool
```

Anotar o `id` da nova inbox.

- [ ] **Step 3: Atribuir Agent Bot à nova inbox**

```bash
NEW_INBOX_ID=<id_retornado_acima>
curl -s -X PATCH "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/$NEW_INBOX_ID" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"channel": {}, "agent_bot": 1}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('agent_bot:', d.get('agent_bot'))"
```

- [ ] **Step 4: Configurar webhook no Meta**

No Meta Business Manager:
1. App → WhatsApp → Configuração → URL de callback:
   `https://chat.ipexdesenvolvimento.cloud/webhooks/whatsapp`
2. Token de verificação: (gerado pelo Chatwoot ao criar a inbox)
3. Campos a assinar: `messages`
4. Verificar e salvar

---

## Task 9: Teste End-to-End

- [ ] **Step 1: Testar RAG diretamente**

```bash
curl -s -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d '{"message": "Como preencho o campo NIS no formulário?", "mode": "query"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Sources:', len(d.get('sources',[]))); print(d.get('textResponse','')[:400])"
```

Esperado: `Sources: 1+` e resposta explicando NIS/CadÚnico

- [ ] **Step 2: Testar webhook n8n simulando Chatwoot**

```bash
curl -s -X POST "https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message_created",
    "message_type": "incoming",
    "content": "Quero me inscrever no TDS, o que preciso fazer?",
    "content_type": "text",
    "sender": {"type": "contact", "name": "Teste Campo", "phone_number": "+5563999999999"},
    "conversation": {"id": "999", "account_id": "1"},
    "meta": {"sender": {"identifier": "+5563999999999", "name": "Teste Campo"}}
  }'
```

Esperado: HTTP 200. Verificar no Chatwoot se uma mensagem de resposta chegou na conversa 999 (ou nova conversa).

- [ ] **Step 3: Verificar no Chatwoot**

Acessar https://chat.ipexdesenvolvimento.cloud e verificar:
- [ ] Conversa aparece na inbox "WhatsApp TDS"
- [ ] Mensagem de resposta do agente está presente
- [ ] Para mensagem de handoff, label `escalonado` é aplicada

- [ ] **Step 4: Testar cenário de escalamento**

```bash
curl -s -X POST "https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message_created",
    "message_type": "incoming",
    "content": "quero falar com um atendente humano por favor",
    "content_type": "text",
    "sender": {"type": "contact", "name": "Teste Handoff", "phone_number": "+5563988888888"},
    "conversation": {"id": "998", "account_id": "1"},
    "meta": {"sender": {"identifier": "+5563988888888", "name": "Teste Handoff"}}
  }'
```

Esperado: mensagem de escalamento enviada + label `escalonado` na conversa

---

## Checklist final antes do campo

- [ ] AnythingLLM responde perguntas sobre NIS, CadÚnico, formulários
- [ ] Agent Bot atribuído à inbox
- [ ] Labels criadas: `pre-matricula`, `baseline`, `escalonado`
- [ ] Time "Equipe TDS" criado com 4 agentes
- [ ] Webhook n8n responde mensagens de texto
- [ ] Escalamento aplica label `escalonado`
- [ ] WhatsApp Cloud API configurado (ou número de contingência ativo)
