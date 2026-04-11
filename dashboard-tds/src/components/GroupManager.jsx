import React, { useState } from 'react';
import { Users, Plus, Upload, Search, Check, AlertCircle, Info } from 'lucide-react';
import { evolutionApi } from '../api/evolution';
import { FORM_FIELDS, BLOCKS } from '../api/form-fields';
import { supabase } from '../lib/supabase';

export default function GroupManager({ simulation }) {
  const [list, setList] = useState("");
  const [participants, setParticipants] = useState([]);
  const [groupName, setGroupName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);

  const processList = async () => {
    setIsLoading(true);
    const rows = list.split('\n').filter(r => r.trim());
    const processed = [];

    for (const row of rows) {
      const parts = row.split(',').map(p => p.trim());
      const number = parts[0];
      const nameGuess = parts[1] || "Aluno";
      
      try {
        // Fetch context from Supabase (Migrated from Frappe)
        const { data: profile, error } = await supabase
          .from('profiles')
          .eq('whatsapp', number)
          .single();
        
        if (!error && profile) {
          context = profile;
        }
      } catch (e) {
        console.error("Error fetching context for", number, e);
      }

      processed.push({
        number: number,
        name: context?.full_name || nameGuess,
        sisec: context ? "Disponível" : "Não encontrado",
        context: context
      });
    }

    setParticipants(processed);
    setIsLoading(false);
  };

  const createGroup = async () => {
    setIsLoading(true);
    try {
      const numbers = participants.map(p => p.number);
      // Logic for adding 55 or other rules could be here
      const result = await evolutionApi.createGroup("tds_suporte_audiovisual", groupName, "Grupo criado via TDS Dashboard", numbers);
      setStatus({ type: 'success', message: `Grupo "${groupName}" criado com ${participants.length} participantes!` });
    } catch (e) {
      setStatus({ type: 'error', message: "Erro ao criar grupo: " + e.message });
    }
    setIsLoading(false);
  };

  // Simulation mode auto-fill
  React.useEffect(() => {
    if (simulation) {
      setList("5563999374165, Rafael Teste");
      setGroupName("Grupo Simulação TDS");
    }
  }, [simulation]);

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload size={20} className="text-primary" />
          Importar Lista de Participantes
        </h3>
        <textarea 
          className="w-full h-32 mb-4"
          placeholder="5563999999999, Nome do Aluno&#10;5511888888888, Outro Nome"
          value={list}
          onChange={(e) => setList(e.target.value)}
        />
        <div className="flex gap-4">
          <button 
            className="btn btn-outline flex-1"
            onClick={processList}
            disabled={isLoading || !list}
          >
            {isLoading ? "Processando..." : "Validar Números & Buscar Contexto SISEC"}
          </button>
        </div>
      </div>

      {participants.length > 0 && (
        <div className="glass-card p-6 animate-fade">
          <h3 className="text-xl font-semibold mb-6">Configuração do Grupo</h3>
          
          <div className="input-group">
            <label className="input-label">Nome do Grupo</label>
            <input 
              type="text" 
              placeholder="Ex: TDS - Turma A 2026" 
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
            />
          </div>

          <div className="overflow-x-auto mb-8">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-border text-text-dim text-sm">
                  <th className="pb-3 px-2">WhatsApp</th>
                  <th className="pb-3">Nome Atribuído</th>
                  <th className="pb-3">Contexto SISEC</th>
                  <th className="pb-3">Ação</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {participants.map((p, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-glass">
                    <td className="py-3 px-2">{p.number}</td>
                    <td className="py-3 font-medium">{p.name}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-md text-xs font-semibold ${p.sisec === "Disponível" ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                        {p.sisec}
                      </span>
                    </td>
                    <td className="py-3">
                      <button 
                        className="text-text-muted hover:text-text-main transition-colors"
                        onClick={() => setSelectedStudent(p)}
                      >
                        <Info size={18}/>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-4">
            <button 
              className="btn btn-primary w-full py-4 text-lg"
              disabled={isLoading || !groupName}
              onClick={createGroup}
            >
              Criar Grupo na Evolution API
            </button>
          </div>
        </div>
      )}

      {status && (
        <div className={`p-4 rounded-xl flex items-center gap-3 animate-fade ${status.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
          {status.type === 'success' ? <Check size={20}/> : <AlertCircle size={20}/>}
          <p className="font-medium">{status.message}</p>
        </div>
      )}

      <StudentDetailModal 
        participant={selectedStudent} 
        onClose={() => setSelectedStudent(null)} 
      />
    </div>
  );
}

function StudentDetailModal({ participant, onClose }) {
  if (!participant) return null;

  const data = participant.context || {};
  
  // Agrupar campos por blocos
  const fieldsByBlock = {};
  FORM_FIELDS.forEach(f => {
    if (!fieldsByBlock[f.block]) fieldsByBlock[f.block] = [];
    fieldsByBlock[f.block].push(f);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-card w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-border flex justify-between items-center bg-white/5">
          <div>
            <h3 className="text-xl font-bold">{participant.name}</h3>
            <p className="text-sm text-text-dim">{participant.number} • Perfil Socioeconômico Completo</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-glass rounded-lg text-text-dim hover:text-text-main transition-colors">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          {Object.entries(fieldsByBlock).map(([blockId, fields]) => {
            const blockInfo = BLOCKS[blockId] || { title: `Bloco ${blockId}`, color: '#6366f1' };
            
            // Check if this block has any data
            const hasData = fields.some(f => data[f.id] && data[f.id] !== "N/A");
            if (!hasData && blockId !== "1") return null;

            return (
              <div key={blockId} className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-1 rounded-full" style={{ backgroundColor: blockInfo.color }}></div>
                  <h4 className="font-bold text-text-main text-sm uppercase tracking-wider">{blockInfo.title}</h4>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {fields.map(f => (
                    <div key={f.id} className="bg-white/3 border border-white/5 p-3 rounded-lg">
                      <label className="text-[10px] text-text-dim block uppercase mb-1 font-semibold">{f.label.split('.')[1] || f.label}</label>
                      <div className="text-sm font-medium text-text-main">
                        {data[f.id] && data[f.id] !== "N/A" ? data[f.id] : <span className="text-text-muted italic">Não informado</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
