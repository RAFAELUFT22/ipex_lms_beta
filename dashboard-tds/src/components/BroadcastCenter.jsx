import React, { useState, useEffect } from 'react';
import { Send, Sliders, AlertTriangle, Mic, MicOff, Tag, Info, FileSpreadsheet, RefreshCcw, CheckCircle2 } from 'lucide-react';
import { evolutionApi } from '../api/evolution';
import { recognitionService } from '../utils/RecognitionService';
import { lmsLiteApi } from '../api/lms_lite';
import { replaceVariables } from '../utils/variableReplacer';

export default function BroadcastCenter() {
  const [message, setMessage] = useState("");
  const [numbers, setNumbers] = useState("");
  const [delay, setDelay] = useState(10); // seconds
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [logs, setLogs] = useState([]);

  // Sheets Integration
  const [useExternalSheet, setUseExternalSheet] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [sheetData, setSheetData] = useState(null); // { headers: [], rows: [] }
  const [isLoadingSheet, setIsLoadingSheet] = useState(false);
  const [mapping, setMapping] = useState({
    whatsapp: "",
    name: "",
    course: ""
  });

  const handleDictation = () => {
    if (isListening) {
      recognitionService.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionService.start(
        (transcript) => {
          setMessage(prev => prev + (prev ? " " : "") + transcript);
        },
        () => setIsListening(false)
      );
    }
  };

  const connectSheet = async () => {
    if (!sheetUrl) return;
    setIsLoadingSheet(true);
    try {
      const data = await lmsLiteApi.fetchSheet(sheetUrl);
      setSheetData(data);
      // Auto-map if headers match common names
      const newMapping = { ...mapping };
      data.headers.forEach(h => {
        const lower = h.toLowerCase();
        if (lower.includes("whatsapp") || lower.includes("telefone") || lower.includes("number")) newMapping.whatsapp = h;
        if (lower.includes("nome") || lower.includes("name") || lower.includes("aluno")) newMapping.name = h;
        if (lower.includes("curso") || lower.includes("trilha")) newMapping.course = h;
      });
      setMapping(newMapping);
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] 📊 Planilha conectada: ${data.rows.length} registros encontrados.`, ...prev]);
    } catch (e) {
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] ❌ Erro ao conectar planilha: ${e.message}`, ...prev]);
    } finally {
      setIsLoadingSheet(false);
    }
  };

  const startBroadcast = async () => {
    let list = [];
    let externalData = [];

    if (useExternalSheet) {
      if (!sheetData || !mapping.whatsapp) {
        alert("Conecte uma planilha e mapeie o campo de Whatsapp");
        return;
      }
      externalData = sheetData.rows;
      list = externalData.map(row => row[mapping.whatsapp]).filter(Boolean);
    } else {
      list = numbers.split('\n').map(n => n.trim()).filter(Boolean);
    }

    if (list.length === 0) return;

    setIsSending(true);
    setProgress({ current: 0, total: list.length });

    let allStudents = [];
    try {
      // Still fetch students to enrich data if possible
      allStudents = await lmsLiteApi.getStudents();
    } catch (e) {
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] ⚠️ Aviso: Falha ao buscar perfis locais para enriquecimento.`, ...prev]);
    }

    const profileMap = allStudents.reduce((acc, s) => ({ ...acc, [s.whatsapp]: s }), {});

    for (let i = 0; i < list.length; i++) {
      const num = list[i];
      let studentProfile = profileMap[num] || {};
      let enrollment = studentProfile.enrollments?.[0] || {};
      
      // Merge with External Data if available
      if (useExternalSheet) {
        const row = externalData[i];
        studentProfile = {
           ...studentProfile,
           full_name: row[mapping.name] || studentProfile.full_name,
           name: row[mapping.name] || studentProfile.name,
           whatsapp: num,
           ...row // Inject all columns as potential variables
        };
        if (mapping.course && row[mapping.course]) {
          enrollment = { course: { title: row[mapping.course] } };
        }
      }

      const personalizedMessage = replaceVariables(message, studentProfile, enrollment?.course || {});

      try {
        await evolutionApi.sendMessage("tds_suporte_audiovisual", num, personalizedMessage);
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ✅ Enviado para ${studentProfile.full_name || studentProfile.name || num}`, ...prev]);
      } catch (e) {
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ❌ Erro para ${num}: ${e.message}`, ...prev]);
      }

      setProgress(prev => ({ ...prev, current: i + 1 }));

      if (i < list.length - 1) {
        const waitTime = delay * 1000 * (0.85 + Math.random() * 0.3);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    setIsSending(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-6 flex justify-between items-center gap-2">
            <div className="flex items-center gap-2">
              <Send size={20} className="text-primary" />
              Nova Transmissão
            </div>
          </h3>

          <div className="flex gap-4 mb-8 p-1 bg-slate-900/50 rounded-xl">
             <button 
               onClick={() => setUseExternalSheet(false)}
               className={`flex-1 py-2 px-4 rounded-lg text-sm font-bold transition-all ${!useExternalSheet ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-dim hover:text-text-main'}`}
             >
               Lista Manual
             </button>
             <button 
               onClick={() => setUseExternalSheet(true)}
               className={`flex-1 py-2 px-4 rounded-lg text-sm font-bold transition-all ${useExternalSheet ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-dim hover:text-text-main'}`}
             >
               Planilha Google (SISEC)
             </button>
          </div>
          
          <div className="input-group">
            <div className="flex justify-between items-center mb-2">
              <label className="input-label mb-0">Mensagem (Variáveis {`{tags}`})</label>
              <button 
                onClick={handleDictation}
                className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg transition-all ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-primary/10 text-primary hover:bg-primary/20'}`}
              >
                {isListening ? <MicOff size={14} /> : <Mic size={14} />}
                {isListening ? "Ouvindo..." : "Ditar Mensagem"}
              </button>
            </div>
            <textarea 
              className="w-full h-40"
              placeholder="Olá {name}, como posso ajudar?"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>

          {!useExternalSheet ? (
            <div className="input-group">
              <label className="input-label">Lista de Números (Um por linha)</label>
              <textarea 
                className="w-full h-32 font-mono text-sm"
                placeholder="5563999999999&#10;5563888888888"
                value={numbers}
                onChange={(e) => setNumbers(e.target.value)}
              />
            </div>
          ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
              <div className="input-group">
                <label className="input-label">URL da Planilha Google (Compartilhada via link)</label>
                <div className="flex gap-2">
                  <input 
                    type="text"
                    className="flex-1"
                    placeholder="https://docs.google.com/spreadsheets/d/..."
                    value={sheetUrl}
                    onChange={(e) => setSheetUrl(e.target.value)}
                  />
                  <button 
                    className="btn btn-secondary px-4 flex items-center gap-2"
                    onClick={connectSheet}
                    disabled={isLoadingSheet}
                  >
                    {isLoadingSheet ? <RefreshCcw size={16} className="animate-spin" /> : <FileSpreadsheet size={16} />}
                    {sheetData ? "Atualizar" : "Conectar"}
                  </button>
                </div>
              </div>

              {sheetData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-primary/5 rounded-xl border border-primary/10">
                  <div className="md:col-span-3 mb-2 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase text-primary flex items-center gap-1">
                      <CheckCircle2 size={14} /> Mapeamento de Colunas
                    </span>
                    <span className="text-[10px] text-text-dim">{sheetData.rows.length} contatos carregados</span>
                  </div>
                  <div className="input-group mb-0">
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Whatsapp</label>
                    <select 
                      className="w-full text-xs"
                      value={mapping.whatsapp}
                      onChange={(e) => setMapping({...mapping, whatsapp: e.target.value})}
                    >
                      <option value="">Selecione...</option>
                      {sheetData.headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                  <div className="input-group mb-0">
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Nome do Aluno</label>
                    <select 
                      className="w-full text-xs"
                      value={mapping.name}
                      onChange={(e) => setMapping({...mapping, name: e.target.value})}
                    >
                      <option value="">Selecione...</option>
                      {sheetData.headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                  <div className="input-group mb-0">
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Curso/Turma</label>
                    <select 
                      className="w-full text-xs"
                      value={mapping.course}
                      onChange={(e) => setMapping({...mapping, course: e.target.value})}
                    >
                      <option value="">Selecione...</option>
                      {sheetData.headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-4 my-6">
            <AlertTriangle className="text-amber-500 shrink-0" size={24} />
            <div>
              <p className="text-amber-500 text-sm font-semibold mb-1">Atenção ao Spam</p>
              <p className="text-text-dim text-xs">O uso de listas de transmissão sem consentimento pode levar ao banimento imediato do número. Utilize intervalos longos.</p>
            </div>
          </div>

          <button 
            className="btn btn-primary w-full py-4"
            disabled={isSending || !message || (useExternalSheet ? !sheetData : !numbers)}
            onClick={startBroadcast}
          >
            {isSending ? "Processando Envio..." : "Iniciar Transmissão"}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Tag size={18} className="text-primary" />
            Variáveis Dinâmicas
          </h3>
          <p className="text-[10px] text-text-dim mb-4">Use as tags abaixo ou qualquer nome de coluna da sua planilha (ex: {'{custom}'}):</p>
          <div className="grid grid-cols-1 gap-2">
            {[
              { id: 'name', label: 'Nome Completo' },
              { id: 'cpf', label: 'CPF (LMS)' },
              { id: 'localidade', label: 'Localidade' },
              { id: 'curso', label: 'Curso Atual' },
            ].map(v => (
              <div 
                key={v.id} 
                className="bg-white/5 border border-white/5 p-2 rounded-lg cursor-pointer hover:bg-primary/10 transition-colors group"
                onClick={() => setMessage(prev => prev + `{${v.id}}`)}
              >
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono text-primary">{"{" + v.id + "}"}</span>
                  <span className="text-[10px] text-text-muted group-hover:text-text-main">{v.label}</span>
                </div>
              </div>
            ))}
            {useExternalSheet && sheetData && sheetData.headers.map(h => (
               <div 
                 key={h} 
                 className="bg-secondary/5 border border-secondary/10 p-2 rounded-lg cursor-pointer hover:bg-secondary/10 transition-colors group"
                 onClick={() => setMessage(prev => prev + `{${h}}`)}
               >
                 <div className="flex justify-between items-center">
                   <span className="text-xs font-mono text-secondary">{"{" + h + "}"}</span>
                   <span className="text-[10px] text-text-muted italic">Coluna Planilha</span>
                 </div>
               </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Sliders size={18} className="text-secondary" />
            Anti-Spam Settings
          </h3>
          
          <div className="input-group">
            <label className="input-label font-medium mb-4 flex justify-between">
              Delay entre mensagens <span>{delay}s</span>
            </label>
            <input 
              type="range" 
              min="3" 
              max="120" 
              value={delay}
              onChange={(e) => setDelay(e.target.value)}
              className="accent-primary"
            />
          </div>

          <div className="mt-8">
            <label className="input-label">Status do Lote</label>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-2">
              <div 
                className="h-full bg-primary transition-all duration-500" 
                style={{ width: `${(progress.current / (progress.total || 1)) * 100}%` }}
              />
            </div>
            <p className="text-xs text-text-dim">{progress.current} de {progress.total} enviados</p>
          </div>
        </div>

        <div className="glass-card p-6 h-[400px] flex flex-col">
          <h3 className="text-lg font-semibold mb-4">Log de Atividade</h3>
          <div className="flex-1 overflow-y-auto space-y-2 font-mono text-[10px]">
            {logs.length === 0 && <p className="text-text-muted italic">Nenhuma atividade registrada.</p>}
            {logs.map((log, i) => (
              <div key={i} className="py-1 border-b border-white/5">{log}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
