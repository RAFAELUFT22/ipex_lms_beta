# Guia de Operação Multi-tenant

Este guia detalha o processo de adição de um novo domínio (inquilino) ao ecossistema TDS no Dokploy.

## 1. Configuração de DNS (Ponta do Cliente)

Para cada novo domínio (ex: `ead.parceiro.com.br`), o parceiro deve criar os seguintes registros:

-   **Tipo A:** `@` ou subdomínio apontando para o IP da VPS: `147.93.102.246`.
-   **Tipo CNAME (Opcional):** `www` apontando para o subdomínio principal.

## 2. Configuração no Dokploy (Ponta da Infra)

No dashboard do Dokploy:

1.  Acesse o projeto `LMS_LITE`.
2.  No serviço `frontend`, vá em **Domains**.
3.  Adicione o novo domínio `ead.parceiro.com.br`. O Dokploy gerenciará o certificado SSL (Let's Encrypt) automaticamente através do Traefik.

## 3. Configuração do Motor de IA (AnythingLLM)

Cada inquilino precisa de um contexto isolado de IA (Workspace):

1.  Acesse a URL do seu `AnythingLLM`.
2.  Crie uma nova **Workspace** com o nome do parceiro (Ex: `parceiro_ead`).
3.  Anote o `slug` gerado (será usado no n8n).
4.  Certifique-se de que a Workspace está usando o motor **Gemini 1.5 Flash**.

## 4. Mapeamento no Orquestrador (n8n)

O n8n precisa saber qual domínio pertence a qual Workspace:

1.  Acesse o fluxo `Kreativ-Unified-API`.
2.  No nó de **Map_Domain_to_Tenant**, adicione uma nova regra:
    -   `domain`: `ead.parceiro.com.br`
    -   `workspace_slug`: `parceiro_ead`
    -   `tenant_id`: `par_001` (ID interno único)

## 5. Script de Automação (Optional)

Você pode usar o script `/root/projeto-tds/add_domains_v2.py` para automatizar o passo 2 e 4. 

```bash
python3 /root/projeto-tds/add_domains_v2.py --domain ead.parceiro.com.br --tenant parceiro_ead
```

## 6. Verificação de Saúde (Checklist)

- [ ] O domínio resolve para o IP correto? (`ping ead.parceiro.com.br`)
- [ ] O certificado SSL está ativo? (Acessar via Browser)
- [ ] O bot responde perguntas específicas do novo parceiro? (Teste via WhatsApp)
