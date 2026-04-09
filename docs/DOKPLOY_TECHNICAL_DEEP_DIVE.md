# Research Report

# Technical Deep Dive: Ecossistema Dokploy (v0.x e v1.x) e Base de Conhecimento para Agentes de IA

**Resumo Executivo e Pontos-Chave**

*   **Arquitetura Consolidada**: O Dokploy atua como um PaaS (Platform as a Service) self-hosted, unificando a orquestração do Docker Swarm com o roteamento dinâmico do Traefik, gerenciado por um backend Node.js/Next.js e persistência em PostgreSQL.
*   **Comunicação Baseada em tRPC**: A API interna é fortemente tipada via tRPC, exposta como REST através de adaptadores OpenAPI. É crucial notar que respostas muito aninhadas (como o endpoint `/api/project.all`) podem gerar erros 500 na camada REST devido a falhas de serialização no adaptador [cite: 1].
*   **Orquestração e Roteamento**: O Traefik utiliza *labels* dinâmicas do Docker para mapear domínios a contêineres específicos na rede *overlay* `dokploy-network` [cite: 2, 3]. Erros comuns de "502 Bad Gateway" frequentemente derivam de falhas no mapeamento de portas ou de aplicações escutando em `127.0.0.1` em vez de `0.0.0.0` [cite: 4, 5].
*   **Contexto Específico (Projeto TDS)**: Os scripts de resgate locais (`dokploy_rescue.py`, etc.) revelam uma necessidade crítica de contornar limitações da UI/API do Dokploy na gestão em lote de variáveis de ambiente e mapeamento de domínios em aplicações Docker Compose [cite: 6].
*   **Construção de Imagens**: O Nixpacks atua como o motor primário de build *zero-config*, abstraindo Dockerfiles, mas exige gerenciamento estrito de memória (`default-shm-size` e limites de RAM) para evitar falhas durante o processo de build [cite: 7, 8].

O presente documento técnico foi elaborado primariamente para o consumo de Agentes de IA responsáveis pela manutenção, extensão, automação e resolução de incidentes no ambiente do Projeto TDS, hospedado sob a infraestrutura do Dokploy. A análise consolida o código-fonte, a documentação oficial, discussões da comunidade e o contexto local extraído dos scripts de resgate fornecidos.

---

## 1. Arquitetura Interna e Orquestração de Ciclo de Vida

A arquitetura do Dokploy foi projetada para minimizar a sobrecarga operacional, adotando um modelo onde o controle (Painel de Administração) e o plano de dados (Aplicações e Roteamento) coabitam o mesmo cluster ou se estendem via Docker Swarm [cite: 9].

### 1.1. O Papel do Docker e Docker Swarm
O Docker atua como a infraestrutura de base absoluta. Durante a instalação via comando curl (`install.sh`), o Dokploy inicializa automaticamente o Docker Swarm (`docker swarm init`), mesmo que opere em um único nó (single-node cluster) [cite: 2, 3]. 

A escolha do Docker Swarm no ecossistema Dokploy garante:
1.  **Rede Overlay Dinâmica**: O instalador cria a rede `dokploy-network` [cite: 2]. Todos os contêineres gerenciados (incluindo o Traefik e as aplicações do usuário) são anexados a esta rede para permitir resolução de DNS interno e tráfego seguro isolado [cite: 3].
2.  **Replicação e Alta Disponibilidade**: O uso do modo *Stack* e serviços do Swarm permite a definição de réplicas e limites de recursos diretamente da UI, refletindo no ciclo de vida orquestrado pelo *Docker Daemon*.
3.  **Clustering e Remote Deployments**: Utilizando arquitetura *Manager-Worker*, o Dokploy pode adicionar nós remotos. As aplicações podem ser agendadas em servidores diferentes usando restrições de *placement* (ex: executar uma base de dados no Manager e o frontend nos Workers) [cite: 10]. 

### 1.2. Traefik: Proxy Reverso e Service Discovery Dinâmico
O Traefik substitui o NGINX tradicional no ecossistema Dokploy devido à sua integração nativa com o Docker API [cite: 9]. Ele atua lendo declarativamente as *labels* anexadas aos contêineres/serviços e roteando o tráfego de entrada em portas 80 (HTTP) e 443 (HTTPS) [cite: 2, 3].

**Mecanismo de Roteamento para Compose e Aplicações:**
Quando o Dokploy faz o deploy de uma aplicação (seja via Nixpacks, Dockerfile ou Compose), ele injeta dinamicamente anotações do Traefik [cite: 11]. Exemplo de configuração gerada para o Traefik via Labels do Docker:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.<unique-name>.rule=Host(`dominio.exemplo.com`)"
  - "traefik.http.services.<unique-name>.loadbalancer.server.port=<PORTA>"
  - "traefik.http.routers.<unique-name>.entrypoints=websecure"
  - "traefik.http.routers.<unique-name>.tls.certresolver=letsencrypt"
```
Agentes de IA devem notar que a gestão de certificados SSL (Let's Encrypt) é tratada inteiramente pelo Traefik usando o desafio HTTP-01 ou DNS-01, automatizando a renovação [cite: 12].

### 1.3. Componentes de Suporte: PostgreSQL e Redis
*   **PostgreSQL**: O Dokploy não utiliza SQLite ou bancos de dados não-relacionais para seu estado interno; ele adota o PostgreSQL [cite: 9]. Isso inclui metadados de projetos, configurações de domínios, variáveis de ambiente encriptadas e credenciais de registro.
*   **Redis**: O Redis é fundamental para gerenciar filas e concorrência [cite: 9]. Durante deploys múltiplos ou requisições intensivas de build, o Redis atua como o *broker* de tarefas (usualmente via BullMQ no ecossistema Node.js) para assegurar que apenas um número seguro de construções Nixpacks ou Dockerfiles ocorra simultaneamente, impedindo travamento de CPU/RAM da VPS.

---

## 2. Mapeamento Profundo de Dependências da Stack

Para atuar na manutenção avançada, a IA deve compreender as camadas da *stack* tecnológica do próprio Dokploy e como elas interagem. O repositório utiliza um monorepo (gerenciado via `pnpm workspaces`) [cite: 13, 14].

### 2.1. Frontend e Backend: React, Next.js e Node.js
O Dokploy é construído sobre o framework Next.js, encapsulando tanto a lógica do cliente (React) quanto do servidor (Node.js) em uma aplicação coesa [cite: 9].
*   **UI Dinâmica**: Utiliza React Query e Zustand para gerenciamento de estado e requisições assíncronas [cite: 15].
*   **Execução Node.js**: O backend orquestra comandos do sistema operacional (invocando binários do Docker CLI, Nixpacks) usando o runtime Node.js. A versão recomendada para contribuição/modificação local é o Node v20 ou v24 [cite: 14, 16].

### 2.2. Camada de API e Comunicação: tRPC
O Dokploy adota o **tRPC** para criar APIs *end-to-end typesafe* [cite: 15, 17]. Isso significa que não há geração manual de schemas (como no GraphQL ou Swagger nativo); os tipos do backend fluem diretamente para o frontend React [cite: 17].
*   **Rotas e Procedures**: O mapeamento é feito via *Routers* e *Procedures* (ex: `project.all`, `compose.deploy`). As *Query Procedures* leem estado, enquanto as *Mutation Procedures* executam ações destrutivas ou de criação [cite: 17].
*   **Limitação do Adaptador OpenAPI**: Como integrações externas precisam de REST, o Dokploy utiliza a biblioteca `@dokploy/trpc-openapi` (um *fork* com customizações Dokploy-style) [cite: 18]. Contudo, isso gera o **Bug do Endpoint 500**: Requisições para `/api/project.all` com grandes volumes de dados aninhados (Projetos -> Ambientes -> Aplicações -> Domínios) frequentemente falham com HTTP 500 devido a gargalos de serialização no adaptador OpenAPI, enquanto a rota nativa `/api/trpc/project.all` continua funcional [cite: 1]. Agentes de IA devem utilizar `GET /api/project.all` com cautela ou focar em queries mais segmentadas se enfrentarem este erro.

### 2.3. Camada de Dados: Prisma ORM
O Prisma é a ponte entre o backend Node.js e o PostgreSQL interno [cite: 15, 19].
*   O schema do Prisma define entidades como `Project`, `Environment`, `Application`, `Compose`, `Domain`, e `Mounts`.
*   O Prisma executa validações estritas de tipagem. A IA deve estar ciente de que inserções manuais no banco (em cenários de *disaster recovery*) devem respeitar as relações estritas geradas pelo Prisma Client.

### 2.4. Motor de Construção de Imagem: Nixpacks e Railpack
O Dokploy abstém o usuário de escrever *Dockerfiles* através do uso do **Nixpacks** (e de seu sucessor experimental **Railpack**) [cite: 8, 20].
*   **Funcionamento Técnico**: O Nixpacks escaneia o repositório em busca de indicadores (ex: `package.json` para Node, `requirements.txt` para Python). Ele então formula um plano de build reprodutível baseado no ecossistema Nix, compila o código e embrulha o resultado em uma imagem OCI (Docker) minimizada [cite: 8, 21].
*   **Configuração via Variáveis**: Comportamentos podem ser alterados através de variáveis de ambiente prefixadas com `NIXPACKS_` (ex: `NIXPACKS_NODE_VERSION`). Em casos mais avançados, recomenda-se a criação de um arquivo `nixpacks.toml` na raiz do repositório da aplicação [cite: 8].
*   **Impacto de Memória**: O build do Nixpacks é altamente intensivo para CPU/RAM. Instâncias menores podem sofrer falhas ("Out of memory during build"), requerendo alteração em `/etc/docker/daemon.json` para aumentar `default-shm-size` ou configuração de *swap* [cite: 7].

---

## 3. API REST e Automação de Tarefas (Referência Avançada)

A automação no Dokploy é regida pelo uso de tokens JWT injetados no header `x-api-key` [cite: 22, 23]. A base de URL oficial é `http://<IP_DO_SERVIDOR>:3000/api` (ou HTTPS caso configurado) [cite: 22, 24].

### 3.1. Estrutura de Endpoints e Convenções
A rota sempre segue o padrão `/api/{router}.{procedure}` [cite: 17]. Todos os payloads e respostas usam `application/json` [cite: 24].

*   **Autenticação**:
    ```http
    GET /api/project.all HTTP/1.1
    Host: 46.202.150.132:3000
    x-api-key: aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU
    Content-Type: application/json
    ```

### 3.2. Referência de Endpoints Cruciais para o TDS

Para gerenciar o ecossistema (Evolução, N8N, Chatwoot, AnythingLLM, Frappe), os seguintes endpoints são exaustivamente utilizados:

#### A. Leitura de Projetos e Estrutura
*   **Endpoint**: `GET /api/project.all` [cite: 6]
*   **Propósito**: Retorna uma árvore JSON completa de Projetos contendo Arrays de `environments`, que por sua vez contêm arrays de `applications`, `compose`, e os serviços de bancos de dados nativos (`mariadb`, `postgres`, etc.) [cite: 25].
*   *Nota*: Estruturas de domínios estão profundamente aninhadas em `environments[].compose[].domains[]` [cite: 6].

#### B. Gestão de Domínios para Compose
A criação e atualização de domínios em aplicações *Docker Compose* tem nuances específicas exigidas pelo modelo de dados da API.

*   **Criação de Domínio** (`POST /api/domain.create`) [cite: 6]:
    Para atrelar um domínio a um serviço dentro de um arquivo `docker-compose.yml` e configurar o SSL do Let's Encrypt:
    ```json
    {
      "host": "chat.ipexdesenvolvimento.cloud",
      "composeId": "oal_DlgbJpbKfLvIL0wO2",
      "composeServiceName": "chatwoot", 
      "domainType": "compose",
      "port": 3005,
      "https": true,
      "certificateType": "letsencrypt"
    }
    ```
*   **Atualização de Domínio** (`POST /api/domain.update`) [cite: 6]:
    Requer estritamente que a chave `serviceName` (e não `composeServiceName`) seja enviada juntamente com `port` e `domainId`. Omissão de `serviceName` desvinculará a regra de roteamento do Traefik, causando erros 502 ou falha de roteamento [cite: 6].
    ```json
    {
      "domainId": "clk_12345abcde",
      "serviceName": "chatwoot",
      "port": 3005
    }
    ```

#### C. Deploy de Serviços Compose
*   **Endpoint**: `POST /api/compose.deploy` [cite: 6]
*   **Propósito**: Sinaliza ao Dokploy para engatilhar um pull do repositório/arquivos, recompilar as variáveis de ambiente em um arquivo `.env` seguro, e executar o comando equivalente a `docker stack deploy` ou `docker compose up -d` na rede swarm [cite: 6].
    ```json
    {
      "composeId": "oal_DlgbJpbKfLvIL0wO2"
    }
    ```

### 3.3. Comportamento das Variáveis de Ambiente na API
O Dokploy suporta variáveis nos níveis de **Projeto**, **Ambiente** e **Serviço** [cite: 25, 26]. Em aplicações de serviço individual, a integração das variáveis é injetada no container dinamicamente. No entanto, para **Docker Compose**, o Dokploy escreve as variáveis diretamente num arquivo físico `.env` na pasta de arquivos da stack (`../files/`) antes de disparar o deploy [cite: 27, 28].
*Limitação Crítica*: Não existe um endpoint padrão tRPC exposto na API OpenAPI para sobrescrever em massa (BULK) as variáveis de ambiente de um container Compose. Intervenções automatizadas podem requerer que o conteúdo seja passado de forma bruta ou através de scripts de injeção diretamente no servidor [cite: 6].

---

## 4. Contexto Local e Grounding (Análise do Projeto TDS)

Os scripts fornecidos pelo usuário (`dokploy_rescue.py` e variações como `fix_dokploy_domains_v2.py`) trazem métricas e contextos fundamentais sobre o estado operacional do cluster que hospeda o Projeto TDS [cite: 6].

### 4.1. Diagnóstico do Ambiente Atual (IP: 46.202.150.132)
O ecossistema TDS roda como uma arquitetura maciça de microsserviços sob o Dokploy utilizando **Docker Compose** (com ID mapeado em hardware: `oal_DlgbJpbKfLvIL0wO2`) [cite: 6]. A complexidade decorre da necessidade de provisionar domínios específicos para contêineres específicos na rede interna do compose [cite: 6].

**Mapeamento Extraído de Roteamento Interno do TDS:**
| Domínio Externo | Contêiner/Serviço Interno | Porta Exposta |
| :--- | :--- | :--- |
| `lms.ipexdesenvolvimento.cloud` | `frappe_frontend` | `8080` |
| `evolution.ipexdesenvolvimento.cloud` | `evolution` | `8080` |
| `n8n.ipexdesenvolvimento.cloud` | `n8n` | `5678` |
| `rag.ipexdesenvolvimento.cloud` | `anythingllm` | `3001` |
| `chat.ipexdesenvolvimento.cloud` | `chatwoot` | `3005` (ou `3000`) |

### 4.2. Dores e Correções Observadas nos Scripts
1.  **Dificuldade de Descoberta de ID**: A API do Dokploy não possui uma rota flat como `domain.all`. O script precisou fazer um *deep search* com loops aninhados 4 camadas abaixo (`projects -> environments -> compose -> domains`) para resgatar o `domainId` dinâmico do banco de dados antes de atualizar [cite: 6].
2.  **O Problema do Chatwoot**: Foi necessário criar uma rotina específica (`fix_chatwoot_domain()`) para reforçar a atualização do serviço associado ao domínio, evidenciando que deploys anteriores perderam a referência do `serviceName` do Traefik, o que corrompia as labels geradas e derrubava a interface do Chatwoot [cite: 6].
3.  **Gestão da Chave do Chatwoot**: O comentário no script `"CRITICAL: CHATWOOT_SECRET_KEY found..."` demonstra que o sincronismo de segredos vitais falhou na automação. Por restrições da API REST de Bulk Vars, a equipe precisou forçar a cópia manual do `.env` na UI [cite: 6]. Agentes de IA lidando com essa infraestrutura devem priorizar a via Web UI / tRPC puro para modificações pesadas de variáveis, ou atualizar diretamente o banco PostgreSQL caso o acesso shell esteja disponível.

---

## 5. Troubleshooting Avançado e Padrões de Erro

Para a IA atuar proativamente na resolução de problemas, seguem as árvores de decisão baseadas nos erros mais endêmicos relatados nas comunidades e repositórios do Dokploy [cite: 5, 7].

### 5.1. O Erro "502 Bad Gateway"
Este é o erro mais recorrente (reportado vastamente no NGINX e Traefik proxies) [cite: 29, 30]. No contexto do Dokploy, um "502 Bad Gateway" significa que o Traefik recebeu a requisição no IP correto da VPS, encontrou a *label* correta de Host, mas não conseguiu encaminhar os pacotes para o IP interno do contêiner Docker.

**Causas Raiz e Soluções (Procedimento para IA)**:
1.  **Porta Incorreta**: Verificar se a porta assinalada na aba de *Domains* (ex: 3000) corresponde exatamente à porta onde o servidor (Node, Python, Nginx) internamente atende (geralmente fixada pelo `EXPOSE` no Dockerfile) [cite: 4].
2.  **Binding em Loopback (`127.0.0.1`)**: Frameworks web modernos (Vite, Next.js, Flask em modo dev) frequentemente atam o socket de escuta apenas à interface `localhost` (`127.0.0.1`). Em um contêiner Docker, isso bloqueia o tráfego da ponte do Traefik. **Solução**: Modificar variáveis (ex: `HOST=0.0.0.0`) ou comandos de inicialização para escutar em `0.0.0.0` [cite: 4, 31].
3.  **Rede Overlay Sem Acesso**: Em clusters multi-node (Swarm), um erro 502 pode indicar que os nós *Worker* não conseguem se comunicar com o nó *Manager* via interface de rede overlay devido a MTUs inconsistentes ou firewalls bloqueando as portas UDP do Docker Swarm (4789, 7946) [cite: 31].
4.  **IP Dinâmico Não Reconhecido (Bug de Migração)**: Em instalações novas (pós v0.20.0), falha em reconhecer o IP da máquina na configuração do "Web Server" inviabiliza o SSL e gera 502. É mandatório navegar até "Settings -> Server" e registrar o IP público manualmente, recriando em seguida os domínios [cite: 29].

### 5.2. Falhas na Inicialização e Migração (Banco de Dados Ocupado)
Durante a restauração de backups ou *upgrades* massivos, os usuários frequentemente encontram erros do Prisma como:
`Database error: database "dokploy" is being accessed by other users` [cite: 32].
*   **Contexto Técnico**: O Dokploy tenta realizar rotinas de *drop* ou alteração destrutiva no banco, porém conexões passivas do backend travam os recursos.
*   **Ação de Intervenção**: Agentes devem instruir ou forçar reinicialização forçada (via shell) dos serviços que competem pela conexão: `docker service scale dokploy-postgres=0` antes de executar scripts diretos de migração, ou usar o comando `REVOKE CONNECT ON DATABASE dokploy` via psql.

### 5.3. "passHostHeader" Não Encontrado (Erro Traefik)
Ao analisar os logs de falha (`docker logs dokploy-traefik`), a ocorrência de:
`Configuration error: field not found, node: passHostHeader in /etc/dokploy/traefik/dynamic/dokploy.yml` [cite: 32].
*   **Diagnóstico**: Este é um erro gerado pela quebra de retrocompatibilidade do Traefik v3 (usado em Dokploy v0.21.4+). A propriedade `passHostHeader` foi depreciada ou movida no esquema de configuração.
*   **Ação**: Exige edição direta nos arquivos persistidos em `/etc/dokploy/traefik/dynamic/` ou atualização para a última versão *patch* do Dokploy (ex: `v0.28.x` [cite: 33]) que já mitiga esse template legado de domínio.

### 5.4. Crash por Falta de Memória (Nixpacks)
*   **Diagnóstico**: Log de build encerrado abruptamente com código 137 (SIGKILL) [cite: 5, 7].
*   **Ação**: Aumentar a capacidade base do Docker limitando concorrentes ou implementando Swap. Modifique `/etc/docker/daemon.json` para:
    ```json
    {
      "default-runtime": "runc",
      "default-shm-size": "2g"
    }
    ```
    E aplique `sudo systemctl restart docker` [cite: 7]. Alternativamente, recomende a migração do deploy para ferramentas CI/CD externas (GitHub Actions), fazendo apenas o envio da imagem já compilada para o Dokploy (via Docker Registry), delegando ao servidor apenas a execução [cite: 34].

---

## 6. Personalização, Modificação e Ambiente de Desenvolvimento

Para que Agentes de IA possam prover *pull requests*, patches ou criar customizações pontuais da plataforma Dokploy visando atender necessidades específicas da arquitetura TDS, é essencial o domínio da estrutura do repositório fonte [cite: 14, 16].

### 6.1. Bootstrap do Ambiente de Desenvolvimento
O fluxo de contribuição baseia-se na branch `canary` (fonte da verdade para novas correções antes de ir para a `main`) [cite: 16].
O repositório requer **pnpm** como gerenciador de dependências e a ferramenta **Biome** para linting/formatação [cite: 16, 35].

**Passos em ambiente shell (Ubuntu/Debian)**:
```bash
# 1. Clonagem e Isolamento
git clone -b canary https://github.com/dokploy/dokploy.git
cd dokploy

# 2. Utilização da versão correta do Node (v24.4.0 recomendada para master atual / v20 anterior)
nvm install 24.4.0 && nvm use

# 3. Instalação e Configuração Env
pnpm install
cp apps/dokploy/.env.example apps/dokploy/.env

# 4. Inicialização do Cluster de Dev (Sobe o Postgres, Redis, Traefik via Docker)
pnpm run dokploy:setup

# 5. Build Completo do Código e Início do Servidor Local
pnpm run server:build
pnpm run dokploy:dev
```
A plataforma ficará acessível em `http://localhost:3000` [cite: 14, 35].

### 6.2. Condição de Corrida (Chicken-and-Egg) no Setup
Uma nota crítica técnica é a conhecida falha reportada no workflow `dokploy:setup`. Desenvolvedores reportam `ECONNREFUSED` porque scripts de importação de módulos TS (como `lib/auth.ts`) tentam se conectar ao PostgreSQL antes que o comando de inicialização via Docker do próprio PostgreSQL tenha finalizado seu tempo de subida [cite: 36].
*   **Workaround**: Agentes devem sugerir assegurar explicitamente a saúde dos contêineres base (`docker pull postgres:15`, `docker swarm init` e rodar o Postgres no background) *antes* de executar instâncias do backend Next.js localmente.

### 6.3. Arquitetura de CLI Local
O Dokploy permite interações robustas pelo terminal com o projeto `@sebbev/dokploy-cli` (um *port* comunitário que reflete nativamente a estrutura de comandos do TRPC) [cite: 37]. Ele pode ser empregado para contornar problemas de automação.
O CLI permite `pull` e `push` de `env vars` que atualmente desafiam os scripts Python brutos do TDS [cite: 37, 38]:
```bash
npx @sebbev/dokploy-cli auth login --url "http://46.202.150.132:3000" --token "aaaaa..."
npx @sebbev/dokploy-cli env push .env --project <PROJ_ID> --app <APP_ID>
```
Sugerir o empacotamento do CLI junto às rotinas de resgate do TDS pode reduzir a fricção e substituir as requisições puras e cruas do `requests.post()` via Python [cite: 37].

---

## 7. Sumário Executivo de Recomendações para Agentes de IA

1.  **Manipulação Segura da API**: Devido ao bug de serialização com o `project.all` na camada REST OpenAPI, qualquer *fetch* da árvore estrutural da infraestrutura Dokploy via scripts Python deve obrigatoriamente validar a presença de um `HTTP 500`.
2.  **Operações sobre Compose**: Sempre que houver a intenção de modificar o direcionamento de um software multi-contêiner (como n8n, Frappe ou Chatwoot no TDS), a inclusão da chave `"serviceName"` nas propriedades JSON de domínio é indispensável. O Dokploy não atualizará o motor do Traefik sem esta amarração, isolando o contêiner do ambiente exterior [cite: 6].
3.  **Deploy em Escala**: Em momentos de lentidão no repositório Dokploy, aconselha-se aos Agentes monitorarem ativamente os *workers* do Redis e os *logs* do Traefik localizados no caminho `/etc/dokploy/traefik/dynamic/`, pois problemas de geração de TLS e rotas inválidas deixam traços residuais nesse diretório, exigindo limpeza manual em situações críticas [cite: 4, 32].

**Sources:**
1. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG20K9EASLb0Kjum4pjZkoU2WxISCEeip16FBDQ0-y48LWuusDbay1eHAXauMjy9ybk45FfLYaAgBTSUwwgMl9_zzLMbAKNIdLCi91qpxfirni--FD-x6b4fLFgeAiMcIG__uk=)
2. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEitg3TkJYUDObFMNt3UYHKqUY5bnabbuKXnpgeooRNbpAVdAbaE1U39oVBEqjl8UeOsEsdUkamR3pHmLNkFHZncmJJXC_Dukf1qeuoD2tjdRKAlSkVfW-gH8zQQAqWFBSDvTYkdRw=)
3. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFAkvlMcoblzyf9Eb7oBUGGw28eZzWBIURomuNXoBg4Gv1E1DfgQ0-qChlZfrmE-72XnmK0TZ3Ps715e5OU9YdzwnnOpKcAy6yvOivszJxNL6Vi6CpaFvBBAufzwehcZBm2Byp8J0_rvfKx)
4. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHX-gTTywONwvFhtLycubTReAer5seCQ-d-E7Mg5sdeM2qtAKLcw_ft5DPxTudlpjsO3OTCPnq6XnYlXT1DtJDpyCkVD19xez-dPOtJ8snLsbsijvQiUSnHrCsl27GEKT0TFVuXC_sk)
5. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGiBQnFPThrYAUvcO2zXRAQcYZS8FOrNj8mZn9i9j9UBU0I-_yCEjYKUEQNZV9yQduIvqbKiik-EdC5owjzCXIqY4awA7F_aHRwHixSU37SB6ss1ZTBDb_IFR3JA8xiZR2Pzx9oOGrHJtXRp7r3Q-wNWupy)
6. fix_dokploy_services.py (fileSearchStores/dokploytdscontext-f6n4izsmdn24)
7. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG60XBdaU7rUPXiANVBNanPJ_yOhE3rDYn6Ha1DSho6e-0tePwQG-cb1zBOQZxiOrYT-CqWNbnCjUmwlUwjuUgS5ZyDgQcHYeEFTTWxskwY5P5xVY5Nf1JRV7HelHKjo_PiPEil-j3QQvTahVDlP5AycG_XpmrZ4A==)
8. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFdelNQwWY5HIShtnqndpd-b72uETcuqiElbS-dKbmipqzRb3Hx4We9ylEQQV00xtxRxQtazTEue7i1F-TnDLKubG3xgPxIdb7ieWd4jbN1vtfTMgC3RifojYT11WIVtIMU2tu8ZZNlplwqTkCiyek=)
9. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHh1JjV-CDAbctJ0nNgryApGVsiyTJUAYBQYxelxWgT-9Hvo2uaustzufzF-FxRsAoM7fr_-36h0FFly_vEO_IkySZlJyatBvOYwihJsvjgYe4YnJPlx1_yIqrdjBvsJBmg9t8r)
10. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOIcAbWSHe9L351EEamyYEZf9PWLlmr-lLqTgLM6OnmBxun1ipGrqB1XF41keLnfXpxtgO_yi2pD02WP8DG3ASav1m5kbFUxcusMsNWc9aetnAsPEtiCdlFes3s4Y-kg==)
11. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCWA5CUjMxgG8P-tz5E8szQLBnl3_bgZyii47dnYIvtJNuXZFZlqxfCn9amYBhrVI6JNOjvsQ0TCQLo0eBxjkCfcybyave6n2Fcn8F7veNHQ1uoEtuql7Lwd-2drDLbR3bfo9OVpZUWfBwT9SL2g==)
12. [lobehub.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG_nNEyxMgLMHtL10MPMy7Rk7gt37LXL3aR9SxJEIWdpKCnoGfG6hM0Wfuvintm2USQgPPbd7OBN1TgpiALCsBQdtYbWCsI7LCdXmyr8Pt97D9GBuZNbxQF7-djqqEx7ApjKyKVvMfptriqsQlmUSjvdrCMoUc=)
13. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHXVrfB5-4CkoPEqBdJu2qaQVgEx3_9XtcQs7u_Qpxq-6D4ytv-ye9St2ORHodpISUol3Wa25cqC6_jFDA8LF1GQhHqbExb2gStNYtyUCueHPRw0cAL335DyDXa31vmxA==)
14. [softuniq.eu](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHdWKHvrxJLl37vDt73kNczU_LdxRR-uTXtNBqZUa6tO2bJhcactgR4Sfh7u2rXJE-aX-LVFjG0uoql_vatjOdRI7wo1nT4E7HuUmdSk1QW0Icy6vUBYz13G6Nz_kYnpGjSf9rfuQGklh-xHg0K3bcAJIGKQVm0lRiis_azEoR_gk6jNqGIcx3YUymkOJrJCUyw5lPzhx-TtLvcAKeuQbx0)
15. [malekgarahellal.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGF4ou5A9a2BkcqkvjYC3LQZs0Mk0WZSkKzQUUCIAVOpPbV4DxuOQ-PS7zWj_fQpS_hZV4XVs8REHDuF8lwPRjF8I1JutR1MdlmHc3lrP1uxutD_3IlaPIpjgs=)
16. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHJUE8HSKu3AB41_E7xJLwJIP5y_m0QERQoN1THrNIV87va4J0zP0REaJ5hK815bl80xvrMkNBEm48D8rtmOAKv_C1nj0IFo8rGQyYW4Mmq7-zlWB_OBKJE6O2uizdD_KARKcL5ZqjCMGEaGfzTvPh6lZY)
17. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHs3b7Q8WXDa7zrpmazJFAH1WlcvN_MjSIptogq-M14uZ-jzL-wuDz6a8gDReR8oLf76ANTgWzV0B_plZl7izK2bzdXn-truivdTmcyTzqjyKsL3oIwdqGC63UmeSMKI2COdpPgfIQHY2cL_TfgnNRD)
18. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGSU4hU8vXOdY6YS5R1wAd2hs6jf2peLFO51ZztZ6bwCJjWArF_2c9U8IGGhqtAgWvXTFqNANgYw4TOh5K_Un03Xz2Dmplu0kPXlMm7TqgcQjS7Oq-K1QmJDOA_1w==)
19. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFBG9RasjeBZKpUJ7Fk2TdZKO9XcW30OWqYMUAAqFS_YoZdC9uTewuvPs7yjlGtEpLQ5z47b0rCNe2WoR02_Gmc-qXBJYaL7fSuhJ_gX9PrjsrFaPkwLNE-ITayGX4=)
20. [nixpacks.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGbMgfnLoSthzTWjcZewG1CXX0gTdUFajJkVsYsRL9fOwtWrpQCaLa94ii_dWrtavULZEmtCGYDrdTPsCIlZ4jnUn1a1XMLYQuLb19raQ_oLeHuVCA5Lp3Pv-ymUWlPWRQ=)
21. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGE9BAHxVaulHUbHy_XY_9393J4v918MUoruEgJXuSkl5VrVAwnxeETFmjYoXsENsTGvDnS4aTyoL19hN-oZFYvaSwEx8y4F0tSUm12rltnPYVWQoPrm4XEsn-ZL2z0lEWMXd9D)
22. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEkDzswWcFevfjQEb34Dbp0VNWfoF6xUM4s3sGzFgB3jkZV41kMzRGlGW0bWTLFgK1C5TyUzebZgh0uBCev6fghEqTORBJQH73y-TDeJmpOzQFDFeKc3A==)
23. [fastmcp.me](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGIAcIuXoc073kdd34XaRM1zP2lwupNo33ZTBsTGPlviKFt5JBZVqTFS2Ff2CAv8o4zeKt0nMd9t3umiPULSDFR6lWUYtC4dIMJZQevIF4PWXS3qomU982PqaB3CPC5Pw==)
24. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFo0cVwfUnbCMornnAS4bDSR0MK9apYVS_dIhn5wUbiPs0wT9HUvlBMOYdVMt1_XUsmox__kHD_LeKFeRBin15MKTiQxpj1iL7YrA2t-WOw1C_ZZx5YZL-6ZzpfOoWIvjyjmkdCtVUP6dWXzjk=)
25. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEZ48X0qCX6JFH25OnWqnJU0XHrWVFR2ritVWMJOq88PqNZhCJMwo2sADOVy0USyirnPSwMzwbKpGVCiE7hX8WOJXvUELwiUhRqk8Yioyf6ODed03S3H_Xrf7QEcVuJEkrHZOkLwBEbk_r1aC7DDHueWsVoQFJwGEv79P75G-4Yolk=)
26. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEAzKOvStWnJhTtIFYAjgAyhMsHyOAPNe2l3KznUckzUPax-bPq6zK2-bu011lICU7Xz1DfSkkn0sRD8nvGPOX7rWRPtlAthNIkrOse1ywuMCPEWupBYEcZX8BZOqLJW-xF)
27. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEb-EOA0q8BENmlcKWutnKEz0dP24fRaKkR03YpCDbaa-iuAc_5bAanyKJAWIKzKSMUC8S2JF279_iIWPO5j5T7tOWLtRFIUt0tDiZR4bMnw_OA2Q15qBroIoLnb8bfsxRjwUqE5iA=)
28. [mintlify.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH2CSELAE7dWdXOuqGC7blP0JDn8xUtQo-AAwzQSCs5n2RoVHJXb7viLFcZbCtoMi6dJgTA3Zdgpbu2j8Clrw97JyKBRvlbNfQvy1T3LfsigZaJ8eb8JvJPFB3yWVEC66JZREv9XYK3PhbeIcl9J7zUXsfa)
29. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHV61f6d1ozt4TuQjuut14WaVsq1twdFyJhrIdJ3c6a4KzSD3VICXZVdt6OzTFq8ZLVyT0SWl1y0UNqNnQf6_ZvhGy1ZAUzTkRFvwvtZwCxKuGyv5v73-P5l5qU3tFdQU9NSoc=)
30. [answeroverflow.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF3Y1K6EOcpj56R0Inw8PHHu6v45JbEHcX2YUlK8mOWkVSN01UmbbejPpLi-TThTnmFGpmZmaPG1Ah0DHO5e5oSEoroRLKBA4RBW5T_IYLiFzjsK-thVtiYq8BMDIee_WSpcqwKku_YFF0=)
31. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFBUsO3O6C0TnpPIl8F0Ac7jF1i1hQrLLzKivtqhg1owG3-iWKQ3wxSTNL3xzNgVsbyhu0-2NhYo6EZiA-a0bSnA-nSRVbdyr6_GraAsG79Gs65HTSyIoYZe8Z6dKL-mv5bxEs=)
32. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOxG9OzvunZOKdbaknVcNBZNawAEC0sAAokIGvHOxEzhXq9IzYk5dr480T4w7QQsyeyepE4cSClKJ3UlHU8T6Sh5mE0u5DuKZK6b9muRqhUcfabJMSiJlqAVgFa6x5bGz9A3c=)
33. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOke15MN-NmdNAYOuQbe6Fp6jjiFRO4C-ag6JggtU3PVJuFGD30orlgy8XpEmi7_o6Z766PqWACoEMWUVYyrHQrfydwojGnGev-6tFAcOGu_FsQm4NP-nuQrtdvsNZlzE=)
34. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHzuwu_epdi8-c6wIQzhf-NJqaDjDQB0940uoTafliG4YFCL3zTCgdf25IZoqonUZ0Zzq7MXlbK4AmVgQTBZPco8g0JjSm8lnw-qmPgp73Pd06Sheva6PQ5Or_d8SqBCo2u3pXEZIF_DcFM9XzOrYLMf6HDCNM=)
35. [githubusercontent.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGuGgde5kIGBBQiUyM1p0rkmYBzgwbbef7pwtVLDg8kL4hGtZgLo4Rp5aAUwYkHuotDW4p4ndPwhf3pcXEqWTqi2liSpKzarIfHmUeAVWQ8_3PZCredd9kRKkxuSiayrdG3xaIPU24Jr3mwksbLBuQg1zBlnJiY671ZQFbgUGZPLn3PzDxWWGqDqcM5)
36. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6QDamrj1eCrdQ-r2oMvWIwIUIfaUa7ZJhe7FH1sbMMkAJduYqNzL9v9YFESMvqaiE7NW1WVm_F6M8bsMA1YQIIpOnCngkr0hxCQlVc1eocl5fxgp1aLer5bKB9lapfHatuuM=)
37. [npmjs.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqF45YqvROi5ipq1UzO_ENZX6dGZYYOPyKBzSsqebdBV7t_wvMsXL0EkI2j3JJoMdDw6BGeb4VTnOczyRsRFQXR0AzLscuiZHDonLGBHWDqFB0e3bFbnhLrCmNkh-GdMCo8PqSVLm-n-oX)
38. [dokploy.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGwCVvmPLPmbke-zP63Mvv8L5wHTOOunBY9BZo2r_DLur5m36QWu1PACYr_Wy8ku-kYlA17B9TE-3Bt3E0GkyRIU4DEKkeewbw9iYnA6ecI3JRgzT4VYIhv4Du6ZSPGB8xc)
