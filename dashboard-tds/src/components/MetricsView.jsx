import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, MessageSquare, Clock, GraduationCap, Award, ExternalLink } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';
import { supabase } from '../lib/supabase';

export default function MetricsView() {
  const [rafaelData, setRafaelData] = useState(null);
  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const WHATSAPP_ID = "5563999374165";

  useEffect(() => {
    async function fetchData() {
      const student = await lmsLiteApi.getStudent(WHATSAPP_ID);
      setRafaelData(student);
      setLoading(false);
    }
    fetchData();

    // Set up Realtime subscription
    const subscription = supabase
      .channel('lms-progress')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'enrollments'
        },
        async (payload) => {
          console.log('Realtime update received:', payload);
          // Refresh student data if the update belongs to our student
          const student = await lmsLiteApi.getStudent(WHATSAPP_ID);
          setRafaelData(student);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(subscription);
    };
  }, []);

  const stats = [
    { label: "Total de Grupos", value: "12", icon: <Users className="text-primary" />, trend: "+2 este mês" },
    { label: "Alunos Ativos", value: "482", icon: <TrendingUp className="text-secondary" />, trend: "+15% vs sem. passada" },
    { label: "Mensagens (24h)", value: "1.250", icon: <MessageSquare className="text-emerald-400" />, trend: "+320 hoje" },
    { label: "Tempo de Resposta", value: "8 min", icon: <Clock className="text-amber-400" />, trend: "-2 min vs média" },
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="glass-card p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-glass rounded-xl">{stat.icon}</div>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-500 px-2 py-1 rounded-full font-bold">
                {stat.trend}
              </span>
            </div>
            <p className="text-text-dim text-sm font-medium">{stat.label}</p>
            <p className="text-3xl font-bold mt-1 tracking-tight">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-6">Atividade por Turno</h3>
          <div className="flex items-end gap-3 h-48">
            {[40, 70, 45, 90, 65, 30].map((h, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-3">
                <div 
                  className="w-full bg-gradient-to-t from-primary/20 to-primary rounded-t-lg transition-all duration-1000" 
                  style={{ height: `${h}%` }}
                />
                <span className="text-[10px] text-text-muted font-mono">{i*4}h</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-6">Status da Trilha Formativa (MDS)</h3>
          <div className="space-y-4">
            {[
              { t: "Conclusão de Módulos (Média)", v: 68 },
              { t: "Frequência no WhatsApp", v: 82 },
              { t: "Taxa de Acerto em Quizzes", v: 74 },
              { t: "Engajamento com Tutor IA", v: 91 },
              { t: "Solicitações de Handoff", v: 12 },
            ].map((item, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-text-main font-medium">{item.t}</span>
                  <span className="text-text-dim">{item.v}%</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full ${item.t.includes('Handoff') ? 'bg-amber-400' : 'bg-primary'}`} style={{ width: `${item.v}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 pt-6 border-t border-border">
            <a 
              href={lmsLiteApi.getExportUrl()} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn btn-outline w-full text-xs flex items-center justify-center gap-2"
            >
              <Users size={14} /> Baixar Relatório de Alunos (CSV)
            </a>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        <div className="glass-card p-6 border-primary/20 bg-primary/5">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-primary/10 rounded-xl">
              <GraduationCap className="text-primary" size={24} />
            </div>
            <div>
              <h3 className="text-xl font-semibold leading-none">LMS Lite Monitor</h3>
              <p className="text-xs text-text-dim mt-1">Acompanhamento em Tempo Real</p>
            </div>
          </div>

          {loading ? (
            <div className="h-40 flex items-center justify-center">Carregando dados...</div>
          ) : rafaelData ? (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-text-main">{rafaelData.name}</p>
                  <p className="text-xs text-text-dim font-mono">{rafaelData.whatsapp}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-emerald-400">
                    {rafaelData.enrollments?.[0]?.progress_percent || 0}%
                  </p>
                  <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">Progresso Geral</p>
                </div>
              </div>
 
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase font-bold text-text-dim">
                  <span>Curso Atual</span>
                  <span className="text-primary">{rafaelData.enrollments?.[0]?.course?.title || 'Nenhum'}</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: `${rafaelData.enrollments?.[0]?.progress_percent || 0}%` }} />
                </div>
              </div>

              {certs.length > 0 && (
                <div className="pt-4 border-t border-border">
                  <h4 className="text-xs font-bold uppercase text-text-dim mb-3 flex items-center gap-2">
                    <Award size={14} className="text-amber-400" /> Certificados Emitidos
                  </h4>
                  <div className="space-y-2">
                    {certs.map((cert, i) => (
                      <div key={i} className="flex justify-between items-center bg-glass p-3 rounded-lg border border-border">
                        <div className="flex gap-3 items-center">
                          <div className="p-2 bg-amber-400/10 rounded-lg">
                            <Award size={16} className="text-amber-400" />
                          </div>
                          <div>
                            <p className="text-xs font-semibold">{cert.course}</p>
                            <p className="text-[10px] text-text-dim font-mono">{cert.cert_id}</p>
                          </div>
                        </div>
                        <a 
                          href={`${import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud'}/validate_cert/${cert.cert_id}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-primary"
                        >
                          <ExternalLink size={14} />
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-text-dim">Rafael não encontrado no LMS Lite</div>
          )}
        </div>
      </div>
    </div>
  );
}
