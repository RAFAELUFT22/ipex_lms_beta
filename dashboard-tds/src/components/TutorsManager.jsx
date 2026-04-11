import React, { useState, useEffect } from 'react';
import { UserPlus, RefreshCw, Trash2, Smartphone, CheckCircle, AlertCircle, QrCode, ShieldCheck, Play } from 'lucide-react';
import { evolutionApi } from '../api/evolution';
import { chatwootApi } from '../api/chatwoot';

export default function TutorsManager() {
  const [instances, setInstances] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newTutorName, setNewTutorName] = useState("");
  const [selectedQR, setSelectedQR] = useState(null);
  const [status, setStatus] = useState(null);
  const [stepLogs, setStepLogs] = useState([]);
  const addLog = (msg) => setStepLogs(prev => [...prev, `${new Date().toLocaleTimeString()} ${msg}`]);

  const loadInstances = async () => {
    setIsLoading(true);
    try {
      const data = await evolutionApi.fetchInstances();
      setInstances(data);
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadInstances();
  }, []);

  const createTutor = async () => {
    setIsLoading(true);
    setStepLogs([]);
    setStatus(null);
    try {
      const instanceName = `tutor_${newTutorName.toLowerCase().replace(/\s/g, '_')}`;

      addLog('⏳ Criando instância na Evolution API...');
      await evolutionApi.createInstance(instanceName);
      addLog(`✅ Instância "${instanceName}" criada.`);

      addLog('⏳ Criando Inbox no Chatwoot...');
      const inbox = await chatwootApi.createInbox(`Tutor - ${newTutorName}`);
      addLog(`✅ Inbox criada (ID: ${inbox.id}).`);

      addLog('⏳ Vinculando Chatwoot na Evolution...');
      await evolutionApi.setChatwoot(instanceName, {
        enabled: true,
        accountId: "1",
        token: "w8BYLTQc1s5VMowjQw433rGy",
        url: "https://chat.ipexdesenvolvimento.cloud",
        inboxId: String(inbox.id),
        signMsg: true,
        reopenConversation: true,
        conversationPending: false,
      });
      addLog('✅ Chatwoot vinculado. Escaneie o QR Code para ativar.');

      setStatus({ type: 'success', message: `Tutor "${newTutorName}" provisionado! Escaneie o QR Code para ativar.` });
      setNewTutorName('');
      loadInstances();
    } catch (e) {
      const detail = e.response?.data?.message || e.message || 'Erro desconhecido';
      addLog(`❌ Falhou: ${detail}`);
      setStatus({ type: 'error', message: `Erro no provisionamento: ${detail}` });
    }
    setIsLoading(false);
  };

  const showQR = async (instanceName) => {
    setIsLoading(true);
    try {
      const data = await evolutionApi.connectInstance(instanceName);
      setSelectedQR({ name: instanceName, code: data.base64 });
    } catch (e) {
      setStatus({ type: 'error', message: "Erro ao carregar QR Code: Instância pode estar offline ou já conectada." });
    }
    setIsLoading(false);
  };

  const deleteTutor = async (name) => {
    if (!window.confirm(`Excluir instância ${name}?`)) return;
    try {
      await evolutionApi.deleteInstance(name);
      loadInstances();
    } catch (e) {
      setStatus({ type: 'error', message: "Erro ao excluir." });
    }
  };

  const [isAutoTesting, setIsAutoTesting] = useState(false);

  const runFullHandoffTest = async () => {
    setIsAutoTesting(true);
    setStepLogs([]);
    setStatus(null);
    const targetPhone = "5563999374165";
    try {
      addLog(`⏳ Buscando contato ${targetPhone} no Chatwoot...`);
      await chatwootApi.assignAndGreet(targetPhone, "Rafael Tutor Senior");
      addLog('✅ Contato encontrado. Conversa assumida e apresentação enviada.');
      setStatus({ type: 'success', message: 'Tutor assumiu a conversa! Aguardando 3s para devolver ao bot...' });

      await new Promise(r => setTimeout(r, 3000));

      addLog('⏳ Resolvendo conversa e reativando bot...');
      await chatwootApi.resolveAndReturnToBot(targetPhone);
      addLog('✅ Atendimento resolvido. Bot reativado.');
      setStatus({ type: 'success', message: 'Ciclo completo! Bot reativado com sucesso.' });
    } catch (e) {
      const detail = e.message || 'Erro desconhecido';
      addLog(`❌ Falhou: ${detail}`);
      setStatus({ type: 'error', message: `Falha no teste: ${detail}` });
    }
    setIsAutoTesting(false);
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <UserPlus size={20} className="text-primary" />
          Provisionar Novo Tutor
        </h3>
        <div className="flex gap-4">
          <input 
            type="text" 
            className="flex-1"
            placeholder="Nome do Tutor (Ex: Rafael Suporte)"
            value={newTutorName}
            onChange={(e) => setNewTutorName(e.target.value)}
          />
          <button 
            type="button"
            className="btn btn-primary"
            onClick={createTutor}
            disabled={isLoading || !newTutorName}
          >
            {isLoading ? "Provisionando..." : "Criar Instância & Inbox"}
          </button>
        </div>
      </div>

      <div className="glass-card p-6 border-amber-500/20 bg-amber-500/5">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-amber-500">
          <ShieldCheck size={20} />
          Automação de Transbordo & Apresentação
        </h3>
        <p className="text-sm text-text-dim mb-6">
          Teste o ciclo completo: O bot silencia, o tutor se apresenta automaticamente e depois devolve o controle para a IA.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-black/20 rounded-xl border border-white/5">
            <h4 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">Ciclo Completo Automático</h4>
            <button 
              type="button"
              onClick={runFullHandoffTest}
              disabled={isAutoTesting}
              className={`btn ${isAutoTesting ? 'bg-amber-500/50' : 'bg-amber-500'} text-black w-full py-3 font-bold flex items-center justify-center gap-2`}
            >
              {isAutoTesting ? <RefreshCw className="animate-spin" size={18} /> : <Play size={18} />}
              {isAutoTesting ? "Rodando Ciclo..." : "Executar Teste de Ponta a Ponta"}
            </button>
            <p className="text-[10px] text-text-muted mt-2 text-center">Simula: Entrada de Rafael Tutor Senior &gt; Apresentação &gt; Atendimento &gt; Resolução.</p>
          </div>

          <div className="p-4 bg-black/20 rounded-xl border border-white/5 flex flex-col justify-center items-center text-center">
            <h4 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">Status do Handoff</h4>
            <div className="flex items-center gap-2 text-emerald-500 font-bold">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
              Sistema de Webhooks Pronto
            </div>
            <p className="text-[10px] text-text-muted mt-2">Integrado com Evolution API e n8n.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {instances?.map((inst) => (
          <div key={inst.instance?.instanceId || Math.random()} className="glass-card p-6 relative overflow-hidden group">
            <div className={`absolute top-0 right-0 p-2 ${inst.instance?.status === 'open' ? 'text-emerald-500' : 'text-amber-500'}`}>
              {inst.instance?.status === 'open' ? <CheckCircle size={18}/> : <AlertCircle size={18}/>}
            </div>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                <Smartphone size={24} />
              </div>
              <div>
                <h4 className="font-bold text-text-main">{inst.instance?.instanceName}</h4>
                <p className="text-xs text-text-dim uppercase tracking-widest">{inst.instance?.status}</p>
              </div>
            </div>

            <div className="flex gap-2">
              {inst.instance?.status !== 'open' && (
                <button 
                  className="btn btn-outline flex-1 py-2 text-sm gap-2"
                  onClick={() => showQR(inst.instance?.instanceName)}
                >
                  <QrCode size={16}/> Conectar
                </button>
              )}
              <button 
                className="btn border-red-500/20 text-red-500 hover:bg-red-500/10 p-2"
                onClick={() => deleteTutor(inst.instance?.instanceName)}
              >
                <Trash2 size={16}/>
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedQR && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-card p-8 max-w-sm w-full text-center">
            <h3 className="text-xl font-bold mb-4">Conectar {selectedQR.name}</h3>
            <div className="bg-white p-4 rounded-xl mb-6 mx-auto w-fit">
              <img src={selectedQR.code} alt="QR Code WhatsApp" className="w-64 h-64" />
            </div>
            <p className="text-sm text-text-dim mb-6">Escaneie com o seu WhatsApp para vincular esta conta de tutor.</p>
            <button 
              className="btn btn-primary w-full"
              onClick={() => setSelectedQR(null)}
            >
              Fechar
            </button>
          </div>
        </div>
      )}

      {stepLogs.length > 0 && (
        <div className="glass-card p-4 font-mono text-xs space-y-1">
          <p className="text-text-muted uppercase tracking-widest text-[10px] mb-2">Log de Operação</p>
          {stepLogs.map((l, i) => (
            <div key={i} className="py-0.5 border-b border-white/5 text-text-dim">{l}</div>
          ))}
        </div>
      )}

      {status && (
        <div className={`p-4 rounded-xl flex items-center gap-3 animate-fade ${status.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
          {status.type === 'success' ? <CheckCircle size={20}/> : <AlertCircle size={20}/>}
          <p className="font-medium">{status.message}</p>
        </div>
      )}
    </div>
  );
}
