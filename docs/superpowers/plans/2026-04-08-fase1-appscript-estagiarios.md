# Fase 1 — AppScript Adaptação para Estagiários

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adaptar o Google Apps Script (TDS Campo v2) para que estagiários possam buscar inscritos pelo telefone/CPF/nome e atualizar fichas a partir de contatos recebidos via WhatsApp no Chatwoot.

**Architecture:** Novo menu item "Buscar por WhatsApp" abre diálogo de busca; ao localizar o inscrito, abre a ficha existente em modo "Atualização WhatsApp"; ao salvar, respeita hierarquia de status (Contatado > Atualização WhatsApp > Em Contato > Pendente) e identifica o estagiário com prefixo `Estag -`.

**Tech Stack:** Google Apps Script (JavaScript server-side + HTML/CSS client-side)

---

## Arquivo a modificar

O Apps Script está vinculado à planilha Google Sheets do projeto TDS. O código está organizado em uma única função `getHtmlFicha()` + funções auxiliares no mesmo arquivo `.gs`.

Referência do código atual: `/root/kreativ-setup/` (não existe localmente — está no Google Apps Script Editor da planilha).

Para editar: Extensões → Apps Script → abrir editor.

---

## Task 1: Adicionar constante STATUS_WA e novo item de menu

**Files:**
- Modify: arquivo `.gs` principal (seção `onOpen` e constantes no topo)

- [ ] **Step 1: Adicionar constante no topo do arquivo**

Localizar a linha:
```javascript
const COL_OBS       = 19;
```

Adicionar logo depois:
```javascript
const STATUS_WA     = 'Atualização WhatsApp';
```

- [ ] **Step 2: Adicionar item ao menu em `onOpen()`**

Localizar:
```javascript
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📋 TDS Campo')
    .addItem('📝 Abrir Ficha do Inscrito',       'abrirFichaDaLinhaSelecionada')
    .addItem('🔧 Configurar Planilha',            'configurarPlanilha')
    .addItem('📊 Relatório Geral',               'gerarRelatorio')
    .addItem('👥 Atualizar Controle Aplicadores', 'gerarControleAplicadores')
    .addToUi();
}
```

Substituir por:
```javascript
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📋 TDS Campo')
    .addItem('📝 Abrir Ficha do Inscrito',        'abrirFichaDaLinhaSelecionada')
    .addItem('📱 Buscar Inscrito por WhatsApp',   'abrirBuscaWhatsApp')
    .addSeparator()
    .addItem('🔧 Configurar Planilha',            'configurarPlanilha')
    .addItem('📊 Relatório Geral',               'gerarRelatorio')
    .addItem('👥 Atualizar Controle Aplicadores', 'gerarControleAplicadores')
    .addToUi();
}
```

- [ ] **Step 3: Verificar no editor**

Salvar o arquivo no Apps Script Editor (Ctrl+S). Fechar e reabrir a planilha. Verificar que o menu "📋 TDS Campo" agora mostra "📱 Buscar Inscrito por WhatsApp" como segundo item.

---

## Task 2: Implementar `buscarPorContato(query)` e `abrirBuscaWhatsApp()`

**Files:**
- Modify: arquivo `.gs` principal — adicionar 3 novas funções após `buscarRegistroCompleto()`

- [ ] **Step 1: Adicionar função `abrirBuscaWhatsApp()`**

Adicionar após a função `buscarRegistroCompleto()`:

```javascript
// ── BUSCA WHATSAPP ──────────────────────────────────────────
function abrirBuscaWhatsApp() {
  const html = HtmlService.createHtmlOutput(getHtmlBusca())
    .setWidth(500)
    .setHeight(300);
  SpreadsheetApp.getUi().showModelessDialog(html, '📱 Buscar Inscrito por WhatsApp');
}
```

- [ ] **Step 2: Adicionar função `buscarPorContato(query)`**

Adicionar após `abrirBuscaWhatsApp()`:

```javascript
function buscarPorContato(query) {
  const ins = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA_INSCRITOS);
  if (!ins || ins.getLastRow() < 2) return [];

  const q = String(query || '').trim().toLowerCase().replace(/\D/g, '');
  const qText = String(query || '').trim().toLowerCase();
  if (!qText) return [];

  const numCols = Math.max(ins.getLastColumn(), COL_OBS);
  const dados = ins.getRange(2, 1, ins.getLastRow() - 1, numCols).getValues();
  const resultados = [];

  dados.forEach((row, idx) => {
    const id        = String(row[0] || '');
    const email     = String(row[2] || '').toLowerCase();
    const nome      = String(row[3] || '').toLowerCase();
    const tel       = String(row[4] || '').replace(/\D/g, '');
    const cpf       = String(row[8] || '').replace(/\D/g, '');
    const municipio = String(row[11] || '').toLowerCase();
    const status    = String(row[COL_STATUS - 1] || '');

    const telMatch  = q && tel.includes(q);
    const cpfMatch  = q && q.length >= 6 && cpf.includes(q);
    const nomeMatch = qText.length >= 3 && nome.includes(qText);
    const emailMatch = qText.includes('@') && email.includes(qText);

    if (telMatch || cpfMatch || nomeMatch || emailMatch) {
      resultados.push({
        linha: idx + 2,
        id: id,
        nome: row[3],
        telefone: row[4],
        municipio: row[11],
        status: status,
        score: (telMatch ? 3 : 0) + (cpfMatch ? 3 : 0) + (nomeMatch ? 1 : 0)
      });
    }
  });

  // Ordenar por score (mais relevante primeiro), limitar a 10
  resultados.sort((a, b) => b.score - a.score);
  return resultados.slice(0, 10);
}
```

- [ ] **Step 3: Adicionar função `abrirFichaWhatsApp(linhaNum)`**

Adicionar após `buscarPorContato()`:

```javascript
function abrirFichaWhatsApp(linhaNum) {
  const ss  = SpreadsheetApp.getActiveSpreadsheet();
  const ins = ss.getSheetByName(ABA_INSCRITOS);
  if (!ins || linhaNum < 2) {
    SpreadsheetApp.getUi().alert('⚠️ Linha inválida: ' + linhaNum);
    return;
  }

  const numCols = Math.max(ins.getLastColumn(), COL_OBS);
  const dados = ins.getRange(linhaNum, 1, 1, numCols).getValues()[0];
  const registroExistente = buscarRegistroCompleto(dados[0]);

  const props = PropertiesService.getScriptProperties();
  props.setProperty('dados_inscrito',    JSON.stringify(dados));
  props.setProperty('linha_inscrito',    String(linhaNum));
  props.setProperty('registro_existente',JSON.stringify(registroExistente));
  props.setProperty('modo_ficha',        'whatsapp');

  // Marcar como Em Contato (sem sobrescrever Contatado)
  const statusAtual = String(dados[COL_STATUS - 1] || '');
  if (statusAtual !== 'Contatado') {
    ins.getRange(linhaNum, COL_STATUS).setValue('Em Contato');
    ins.getRange(linhaNum, COL_DATA).setValue(new Date());
  }

  const html = HtmlService.createHtmlOutput(getHtmlFicha())
    .setWidth(960)
    .setHeight(720);
  SpreadsheetApp.getUi().showModelessDialog(html, '📱 Atualização WhatsApp – ' + (dados[3] || ''));
}
```

- [ ] **Step 4: Adicionar `obterModoFicha()` para a GUI acessar o modo**

Adicionar após `obterDadosFicha()`:

```javascript
function obterModoFicha() {
  return PropertiesService.getScriptProperties().getProperty('modo_ficha') || 'campo';
}
```

- [ ] **Step 5: Salvar e verificar no console**

No Apps Script Editor: Executar → `buscarPorContato` com argumento `"test"`. Esperado: array vazio (sem erros de sintaxe).

---

## Task 3: Implementar HTML do diálogo de busca `getHtmlBusca()`

**Files:**
- Modify: arquivo `.gs` principal — adicionar função após `getHtmlFicha()`

- [ ] **Step 1: Adicionar função `getHtmlBusca()`**

Adicionar após a função `getHtmlFicha()`:

```javascript
function getHtmlBusca() {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#f0f2f5;padding:20px;font-size:13px}
h3{color:#1F4E78;margin-bottom:16px;font-size:15px}
.fg{display:flex;flex-direction:column;gap:4px;margin-bottom:12px}
.fg label{font-size:11px;color:#777;font-weight:700;text-transform:uppercase}
.fg input{border:1px solid #ddd;border-radius:5px;padding:8px 10px;font-size:13px;font-family:inherit}
.fg input:focus{outline:none;border-color:#1F4E78;box-shadow:0 0 0 2px rgba(31,78,120,.1)}
.btn-p{background:#1F4E78;color:#fff;border:none;padding:9px 20px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;width:100%}
.btn-p:hover{background:#153a54}
.result-list{margin-top:12px;max-height:180px;overflow-y:auto}
.result-item{background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:10px 12px;margin-bottom:6px;cursor:pointer;transition:background .15s}
.result-item:hover{background:#e8f0fe;border-color:#1F4E78}
.result-nome{font-weight:600;color:#1F4E78;font-size:13px}
.result-info{font-size:11px;color:#888;margin-top:2px}
.result-status{font-size:10px;padding:2px 7px;border-radius:10px;display:inline-block;margin-top:4px}
.s-pend{background:#fff3e0;color:#e65100}
.s-cont{background:#e3f2fd;color:#1565c0}
.s-contatado{background:#e8f5e9;color:#2e7d32}
.s-wa{background:#f3e5f5;color:#6a1b9a}
.empty{color:#aaa;text-align:center;padding:20px;font-size:12px}
.hint{font-size:11px;color:#aaa;margin-bottom:8px}
</style>
</head>
<body>
<h3>📱 Buscar Inscrito por WhatsApp</h3>
<div class="fg">
  <label>Telefone, CPF ou Nome parcial</label>
  <input id="q" type="text" placeholder="Ex: 63999, 123.456 ou Maria da Silva" autofocus
    oninput="buscar()" onkeydown="if(event.key==='Enter')buscar()">
</div>
<p class="hint">Digite pelo menos 3 caracteres. Resultados aparecem automaticamente.</p>
<div class="result-list" id="lista"></div>

<script>
let timer = null;
function buscar() {
  clearTimeout(timer);
  const q = document.getElementById('q').value.trim();
  if (q.length < 3) { document.getElementById('lista').innerHTML = ''; return; }
  timer = setTimeout(() => {
    google.script.run
      .withSuccessHandler(renderizar)
      .withFailureHandler(e => { document.getElementById('lista').innerHTML = '<p class="empty">Erro: ' + e.message + '</p>'; })
      .buscarPorContato(q);
  }, 400);
}

function renderizar(resultados) {
  const lista = document.getElementById('lista');
  if (!resultados || resultados.length === 0) {
    lista.innerHTML = '<p class="empty">Nenhum inscrito encontrado.</p>';
    return;
  }
  const statusCls = {
    'Pendente': 's-pend', 'Em Contato': 's-cont',
    'Contatado': 's-contatado', 'Atualização WhatsApp': 's-wa'
  };
  lista.innerHTML = resultados.map(r =>
    '<div class="result-item" onclick="abrir(' + r.linha + ')">' +
    '<div class="result-nome">' + r.nome + '</div>' +
    '<div class="result-info">📞 ' + (r.telefone || '—') + ' · ' + (r.municipio || '—') + '</div>' +
    '<span class="result-status ' + (statusCls[r.status] || 's-pend') + '">' + (r.status || 'Pendente') + '</span>' +
    '</div>'
  ).join('');
}

function abrir(linha) {
  google.script.host.close();
  google.script.run.abrirFichaWhatsApp(linha);
}
</script>
</body>
</html>`;
}
```

- [ ] **Step 2: Testar o fluxo de busca**

1. Na planilha: menu "📋 TDS Campo" → "📱 Buscar Inscrito por WhatsApp"
2. Digitar pelo menos 3 letras de um nome existente na aba INSCRITOS
3. Verificar que resultados aparecem
4. Clicar em um resultado — a ficha deve abrir com badge "📱 Via WhatsApp"

---

## Task 4: Modificar `getHtmlFicha()` para suporte ao modo WhatsApp

**Files:**
- Modify: função `getHtmlFicha()` no arquivo `.gs`

- [ ] **Step 1: Adicionar leitura do modo no `onDados()`**

Na função `getHtmlFicha()`, localizar dentro do `<script>`:

```javascript
function onDados(d) {
  DI    = d.inscrito;
  LINHA = d.linha;
```

Adicionar após `LINHA = d.linha;`:

```javascript
  // Detectar modo e exibir badge
  google.script.run.withSuccessHandler(function(modo) {
    if (modo === 'whatsapp') {
      document.getElementById('badgeModo').style.display = 'inline-block';
      document.getElementById('topNome').style.marginRight = '8px';
    }
  }).obterModoFicha();
```

- [ ] **Step 2: Adicionar badge no HTML do topo**

Localizar no HTML de `getHtmlFicha()`:

```html
<div class="top">
  <h2 id="topNome">⏳ Carregando...</h2>
```

Substituir por:

```html
<div class="top">
  <span id="badgeModo" style="display:none;background:#ce93d8;color:#4a148c;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:700;margin-right:8px">📱 Via WhatsApp</span>
  <h2 id="topNome" style="display:inline">⏳ Carregando...</h2>
```

- [ ] **Step 3: Verificar que o badge aparece ao abrir via busca WhatsApp**

Abrir a ficha via "📱 Buscar Inscrito por WhatsApp" → selecionar inscrito → verificar que a faixa azul do topo exibe "📱 Via WhatsApp" em roxo.

---

## Task 5: Modificar `salvarFicha(p)` para respeitar hierarquia de status

**Files:**
- Modify: função `salvarFicha(p)` no arquivo `.gs`

- [ ] **Step 1: Modificar a função `atualizarStatusInscrito()`**

Localizar:

```javascript
function atualizarStatusInscrito(linhaNum, status, aplicador) {
  const ins = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA_INSCRITOS);
  if (!ins || linhaNum < 2) return;
  ins.getRange(linhaNum, COL_STATUS).setValue(status);
  if (aplicador) ins.getRange(linhaNum, COL_APLICADOR).setValue(aplicador);
  ins.getRange(linhaNum, COL_DATA).setValue(new Date());
}
```

Substituir por:

```javascript
function atualizarStatusInscrito(linhaNum, novoStatus, aplicador) {
  const ins = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA_INSCRITOS);
  if (!ins || linhaNum < 2) return;

  // Hierarquia: Contatado > Atualização WhatsApp > Em Contato > Pendente
  const hierarquia = { 'Contatado': 4, 'Atualização WhatsApp': 3, 'Em Contato': 2, 'Pendente': 1 };
  const statusAtual = String(ins.getRange(linhaNum, COL_STATUS).getValue() || 'Pendente');
  const priorAtual  = hierarquia[statusAtual]  || 1;
  const priorNovo   = hierarquia[novoStatus]   || 1;

  // Só atualiza se o novo status for igual ou superior ao atual
  if (priorNovo >= priorAtual) {
    ins.getRange(linhaNum, COL_STATUS).setValue(novoStatus);
  }
  if (aplicador) ins.getRange(linhaNum, COL_APLICADOR).setValue(aplicador);
  ins.getRange(linhaNum, COL_DATA).setValue(new Date());
}
```

- [ ] **Step 2: Modificar `salvarFicha(p)` para usar STATUS_WA quando em modo whatsapp**

Localizar dentro de `salvarFicha(p)`:

```javascript
  if (comp) comp.appendRow(linha);
  atualizarStatusInscrito(p.linha, 'Contatado', p.aplicador);
```

Substituir por:

```javascript
  if (comp) comp.appendRow(linha);
  // Determinar status baseado no modo de abertura
  const props = PropertiesService.getScriptProperties();
  const modo = props.getProperty('modo_ficha') || 'campo';
  const statusFinal = modo === 'whatsapp' ? STATUS_WA : 'Contatado';
  atualizarStatusInscrito(p.linha, statusFinal, p.aplicador);
  props.deleteProperty('modo_ficha'); // limpar modo após salvar
```

E a chamada anterior de `atualizarStatusInscrito` antes do `appendRow` também precisa ajuste. Localizar:

```javascript
        comp.getRange(i+2, 1, 1, linha.length).setValues([linha]);
        atualizarStatusInscrito(p.linha, 'Contatado', p.aplicador);
        return { ok: true, msg: 'Registro atualizado com sucesso!' };
```

Substituir por:

```javascript
        comp.getRange(i+2, 1, 1, linha.length).setValues([linha]);
        const modoAtual = PropertiesService.getScriptProperties().getProperty('modo_ficha') || 'campo';
        const statusAtualizar = modoAtual === 'whatsapp' ? STATUS_WA : 'Contatado';
        atualizarStatusInscrito(p.linha, statusAtualizar, p.aplicador);
        PropertiesService.getScriptProperties().deleteProperty('modo_ficha');
        return { ok: true, msg: 'Registro atualizado com sucesso!' };
```

- [ ] **Step 3: Testar a hierarquia**

1. Abrir um inscrito com status "Contatado" via "📱 Buscar por WhatsApp"
2. Salvar a ficha
3. Verificar que o status NÃO mudou para "Atualização WhatsApp" (permanece "Contatado")
4. Abrir um inscrito com status "Pendente" via busca WhatsApp, salvar
5. Verificar que o status virou "Atualização WhatsApp"

---

## Task 6: Modificar `gerarControleAplicadores()` para cores por tipo

**Files:**
- Modify: função `gerarControleAplicadores()` no arquivo `.gs`

- [ ] **Step 1: Substituir a lógica de coloração final**

Localizar ao final de `gerarControleAplicadores()`:

```javascript
    linhas.forEach(function(l, i) {
      const taxa = parseFloat(l[4]);
      const cor  = taxa >= 80 ? '#c8e6c9' : taxa >= 50 ? '#fff9c4' : '#ffcdd2';
      ctrl.getRange(i + 2, 5).setBackground(cor).setFontWeight('bold');
    });
```

Substituir por:

```javascript
    linhas.forEach(function(l, i) {
      const taxa = parseFloat(l[4]);
      const nome = String(l[0]);
      const rowRange = ctrl.getRange(i + 2, 1, 1, 8);

      // Cor por tipo de aplicador
      if (nome.startsWith('Estag -') || nome.startsWith('Estag-')) {
        rowRange.setBackground('#ede7f6'); // lilás — estagiário
      } else if (nome === 'Bot TDS') {
        rowRange.setBackground('#f5f5f5'); // cinza — bot
      } else {
        rowRange.setBackground('#ffffff'); // branco — aplicador de campo
      }

      // Cor da taxa de conclusão (coluna 5)
      const taxaCor = taxa >= 80 ? '#c8e6c9' : taxa >= 50 ? '#fff9c4' : '#ffcdd2';
      ctrl.getRange(i + 2, 5).setBackground(taxaCor).setFontWeight('bold');
    });
```

- [ ] **Step 2: Adicionar legenda de cores no topo da aba CONTROLE_APLICADORES**

Localizar no `gerarControleAplicadores()` o trecho de inicialização da aba (onde cria os headers):

```javascript
    ctrl.setColumnWidth(8, 300);
```

Adicionar após:

```javascript
    // Legenda de cores (linha 2 placeholder, dados começam na linha 2 quando há dados)
    // Adicionar legenda na célula I1 (fora da tabela principal)
    ctrl.getRange(1, 10).setValue('Legenda: branco=campo | roxo=estagiário | cinza=bot').setFontSize(9).setFontColor('#888');
```

- [ ] **Step 3: Testar o painel de controle**

1. Menu → "👥 Atualizar Controle Aplicadores"
2. Verificar que linhas com prefixo "Estag - " ficam com fundo lilás
3. Verificar que a taxa de conclusão mantém sua coloração (verde/amarelo/vermelho)

---

## Task 7: Teste manual completo do fluxo de estagiário

- [ ] **Step 1: Simular contato via WhatsApp**

1. Abrir a planilha com dados na aba INSCRITOS
2. Menu → "📱 Buscar Inscrito por WhatsApp"
3. Digitar o telefone de um inscrito existente (ex: `9999`)
4. Verificar que o inscrito aparece na lista de resultados

- [ ] **Step 2: Abrir e atualizar ficha**

1. Clicar no resultado para abrir a ficha
2. Verificar badge "📱 Via WhatsApp" no topo
3. Preencher campo "Aplicador Responsável" com `Estag - [Seu Nome]`
4. Atualizar um campo (ex: email)
5. Clicar em "💾 Salvar Ficha"

- [ ] **Step 3: Verificar resultado nas abas**

Na aba INSCRITOS:
- [ ] Coluna APLICADOR mostra `Estag - [Nome]`
- [ ] Coluna STATUS mostra "Atualização WhatsApp" (ou "Contatado" se já estava Contatado)
- [ ] Coluna DATA CONTATO atualizada

Na aba REGISTROS_COMPLETOS:
- [ ] Linha do inscrito atualizada com os novos dados

- [ ] **Step 4: Verificar painel de controle**

Menu → "👥 Atualizar Controle Aplicadores"
- [ ] Linha do estagiário aparece com fundo lilás
- [ ] Taxa de conclusão calculada corretamente

---

## Notas de implementação

**Prefixo para estagiários:** Orientar os estagiários a preencher o campo "Aplicador" sempre como `Estag - [Primeiro Nome]`. Exemplo: `Estag - Maria`, `Estag - João`.

**Acesso à planilha:** Cada estagiário precisa ter acesso de edição à planilha Google Sheets. Compartilhar via Google Drive com o e-mail de cada um.

**Sessões simultâneas:** O Apps Script usa `PropertiesService.getScriptProperties()` que é compartilhado entre todos os usuários. Em versões futuras, considerar usar `PropertiesService.getUserProperties()` para isolamento por usuário. Para o MVP atual com poucos estagiários simultâneos, `getScriptProperties()` é suficiente.
