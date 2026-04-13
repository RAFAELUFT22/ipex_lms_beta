import React, { useEffect, useMemo, useState } from 'react';
import { BarChart3, Users, TrendingUp, Award, Clock, Download } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';

export default function MetricsView() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month');
  const [phone, setPhone] = useState('');
  const [lgpdStatus, setLgpdStatus] = useState('');

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await lmsLiteApi.getMetricsSummary();
      setSummary(data);
    } catch (e) {
      setLgpdStatus(`Erro ao carregar métricas: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const filteredActivity = useMemo(() => {
    if (!summary?.activity_by_day) return [];
    const days = period === 'week' ? 7 : period === 'quarter' ? 90 : 30;
    return summary.activity_by_day.slice(-days);
  }, [summary, period]);

  const maxActivity = Math.max(...filteredActivity.map((d) => d.lessons_viewed), 1);

  const handleExportStudent = async () => {
    if (!phone.trim()) return;
    try {
      const data = await lmsLiteApi.exportStudentLgpd(phone.trim());
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `student_${phone.trim()}_lgpd.json`;
      a.click();
      URL.revokeObjectURL(url);
      setLgpdStatus('Dados exportados com sucesso.');
    } catch (e) {
      setLgpdStatus(`Erro ao exportar: ${e.message}`);
    }
  };

  const handleDeleteStudent = async () => {
    if (!phone.trim()) return;
    if (!window.confirm(`Tem certeza que deseja excluir ${phone}?`)) return;
    try {
      await lmsLiteApi.deleteStudentLgpd(phone.trim());
      setLgpdStatus('Aluno excluído com sucesso.');
      loadSummary();
    } catch (e) {
      setLgpdStatus(`Erro ao excluir: ${e.message}`);
    }
  };

  if (loading) return <div className="glass-card p-6">Carregando métricas...</div>;
  if (!summary) return <div className="glass-card p-6">Sem dados de métricas.</div>;

  const cards = [
    { label: 'Total', value: summary.total_students, icon: <Users size={18} className="text-primary" /> },
    { label: 'Ativos', value: summary.active_students, icon: <TrendingUp size={18} className="text-secondary" /> },
    { label: 'Concluintes', value: summary.completed_students, icon: <Award size={18} className="text-emerald-400" /> },
    { label: 'Inativos 7d', value: summary.inactive_7d, icon: <Clock size={18} className="text-amber-400" /> },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="glass-card p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-text-dim">{card.label}</span>
              {card.icon}
            </div>
            <p className="text-3xl font-bold">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Por curso</h3>
          <a href={lmsLiteApi.getExportUrl()} className="btn btn-outline text-xs"><Download size={14} /> CSV</a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-dim border-b border-border">
                <th className="text-left p-2">Curso</th>
                <th className="text-left p-2">Matrículas</th>
                <th className="text-left p-2">Progresso Médio</th>
                <th className="text-left p-2">% Conclusão</th>
              </tr>
            </thead>
            <tbody>
              {summary.by_course.map((course) => {
                const completion = course.enrolled ? ((course.completed / course.enrolled) * 100).toFixed(1) : '0.0';
                return (
                  <tr key={course.slug} className="border-b border-border/40">
                    <td className="p-2">{course.title}</td>
                    <td className="p-2">{course.enrolled}</td>
                    <td className="p-2">{course.avg_progress}%</td>
                    <td className="p-2">{completion}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2"><BarChart3 size={18} /> Atividade</h3>
          <select className="bg-black/20 border border-border rounded-md px-2 py-1 text-sm" value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="week">Última semana</option>
            <option value="month">Último mês</option>
            <option value="quarter">Último trimestre</option>
          </select>
        </div>
        <div className="space-y-1">
          {filteredActivity.map((day) => (
            <div key={day.date} className="flex items-center gap-3 text-xs">
              <span className="w-24 text-text-dim">{day.date}</span>
              <div className="h-3 bg-primary/20 rounded w-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${(day.lessons_viewed / maxActivity) * 100}%` }} />
              </div>
              <span className="w-8 text-right">{day.lessons_viewed}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-6 space-y-3">
        <h3 className="text-lg font-semibold">LGPD</h3>
        <input
          type="text"
          className="w-full"
          placeholder="Buscar por WhatsApp (ex: 5563999991111)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <button className="btn btn-outline" onClick={handleExportStudent}>Exportar Dados (LGPD)</button>
          <button className="btn btn-primary" onClick={handleDeleteStudent}>Excluir Aluno</button>
        </div>
        {lgpdStatus && <p className="text-xs text-text-dim">{lgpdStatus}</p>}
      </div>
    </div>
  );
}
