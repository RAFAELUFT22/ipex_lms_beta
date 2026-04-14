# Guia do Administrador — TDS LMS Lite

Este guia descreve as operações críticas para gerenciar a plataforma TDS.

## 1. Segurança e Acesso
O acesso ao Dashboard e aos endpoints administrativos exige a `ADMIN_KEY`.
- **Dashboard:** Insira a senha na tela de login.
- **API:** Use o header `X-Admin-Key: <sua_chave>`.

### Alterando a Senha
Edite o arquivo `.env.tds` no servidor e altere a variável `ADMIN_KEY`. O Dokploy aplicará a mudança automaticamente.

## 2. Gestão de Conteúdo (RAG)
O Tutor IA utiliza o AnythingLLM para responder dúvidas.
1. No Dashboard, vá em **Base de Conhecimento**.
2. Faça o upload de manuais (PDF/TXT).
3. Vincule o curso ao Workspace correto em **Configurações**.

## 3. Conexão com WhatsApp
Suportamos dois métodos:
- **Baileys (Evolution API):** Mais flexível, permite uso de números comuns. Escaneie o QR Code no painel Evolution.
- **Cloud API (Oficial):** Mais estável para escala. Requer configuração no portal Meta for Developers.

## 4. Backups e Recuperação
O sistema realiza backups automáticos em cada gravação no banco de dados.
- **Localização:** `/data/backups/`
- **Recuperação:** Copie o arquivo de backup desejado para `/data/lms_lite_db.json` e reinicie o container.

## 5. Exportação de Dados
Na aba **Métricas**, você pode baixar o relatório completo de alunos em CSV, contendo dados do SISEC, progresso detalhado e interações com a IA.
