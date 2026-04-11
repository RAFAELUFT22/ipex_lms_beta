import React, { useState } from 'react';
import { Send, Sliders, AlertTriangle, Mic, MicOff, Tag, Info } from 'lucide-react';
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

  const startBroadcast = async () => {
    const list = numbers.split('\n').map(n => n.trim()).filter(Boolean);
    setIsSending(true);
    setProgress({ current: 0, total: list.length });

    let allStudents = [];
    try {
      allStudents = await lmsLiteApi.getStudents();
    } catch (e) {
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] ❌ Erro ao buscar perfis: ${e.message}`, ...prev]);
    }

    const profileMap = allStudents.reduce((acc, s) => ({ ...acc, [s.whatsapp]: s }), {});

    for (let i = 0; i < list.length; i++) {
      const num = list[i];
      const studentProfile = profileMap[num] || {};
      const enrollment = studentProfile.enrollments?.[0];
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
          <h3 className="text-xl font-semibold mb-4 flex justify-between items-center gap-2">
            <div className="flex items-center gap-2">
              <Send size={20} className="text-primary" />
              Nova Transmissão
            </div>
          </h3>
          
          <div className="input-group">
            <div className="flex justify-between items-center mb-2">
              <label className="input-label mb-0">Mensagem (Suporte a Variáveis {name})</label>
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

          <div className="input-group">
            <label className="input-label">Lista de Números (Um por linha)</label>
            <textarea 
              className="w-full h-32 font-mono text-sm"
              placeholder="5563999999999&#10;5563888888888"
              value={numbers}
              onChange={(e) => setNumbers(e.target.value)}
            />
          </div>

          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-4 mb-6">
            <AlertTriangle className="text-amber-500 shrink-0" size={24} />
            <div>
              <p className="text-amber-500 text-sm font-semibold mb-1">Atenção ao Spam</p>
              <p className="text-text-dim text-xs">O uso de listas de transmissão sem consentimento pode levar ao banimento imediato do número. Utilize intervalos longos.</p>
            </div>
          </div>

          <button 
            className="btn btn-primary w-full py-4"
            disabled={isSending || !message || !numbers}
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
            Variáveis do SISEC
          </h3>
          <p className="text-[10px] text-text-dim mb-4">Use as tags abaixo na sua mensagem para personalização automática:</p>
          <div className="grid grid-cols-1 gap-2">
            {[
              { id: 'name', label: 'Nome Completo' },
              { id: 'cpf', label: 'CPF' },
              { id: 'localidade', label: 'Localidade' },
              { id: 'cidade', label: 'Cidade' },
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
          </div>
          <div className="mt-6 p-3 bg-primary/5 rounded-lg border border-primary/10">
             <div className="flex items-center gap-2 text-primary mb-1">
               <Info size={14} />
               <span className="text-[10px] font-bold uppercase">Como funciona</span>
             </div>
             <p className="text-[10px] text-text-dim leading-relaxed">O sistema buscará automaticamente os dados vinculados ao número do WhatsApp via LMS API.</p>
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
            <p className="text-[10px] text-text-muted mt-2">Delay recomendado para listas &gt; 50 contatos: acima de 30s.</p>
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
