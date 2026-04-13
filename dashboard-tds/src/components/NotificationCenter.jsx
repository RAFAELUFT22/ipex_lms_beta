import React, { useEffect, useMemo, useState } from 'react';
import { lmsLiteApi } from '../api/lms_lite';
import { replaceVariables } from '../utils/variableReplacer';

export default function NotificationCenter() {
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [targetType, setTargetType] = useState('all');
  const [courseSlug, setCourseSlug] = useState('');
  const [inactiveDays, setInactiveDays] = useState(7);
  const [message, setMessage] = useState('Olá {nome}, lembrete do curso {curso}. Progresso atual: {progresso}%');
  const [channel, setChannel] = useState('whatsapp');
  const [delayMinutes, setDelayMinutes] = useState(0);
  const [logs, setLogs] = useState([]);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    Promise.all([lmsLiteApi.getStudents(), lmsLiteApi.getCourses(), lmsLiteApi.getNotificationLog()])
      .then(([studentData, courseData, logData]) => {
        setStudents(studentData || []);
        setCourses(courseData || []);
        setLogs(logData?.items || []);
        if (courseData?.[0]?.slug) setCourseSlug(courseData[0].slug);
      })
      .catch(() => {});
  }, []);

  const target = useMemo(() => {
    if (targetType === 'course') return `course:${courseSlug}`;
    if (targetType === 'inactive') return `inactive:${inactiveDays}`;
    return 'all';
  }, [targetType, courseSlug, inactiveDays]);

  const recipientsPreview = useMemo(() => {
    if (targetType === 'all') return students.map((s) => s.whatsapp);
    if (targetType === 'course') {
      return students
        .filter((s) => s.enrollments?.some((e) => e.course?.slug === courseSlug))
        .map((s) => s.whatsapp);
    }
    const threshold = Date.now() - Number(inactiveDays || 0) * 24 * 60 * 60 * 1000;
    return students
      .filter((s) => s.last_activity_at && new Date(s.last_activity_at).getTime() < threshold)
      .map((s) => s.whatsapp);
  }, [students, targetType, courseSlug, inactiveDays]);

  const sendNow = async () => {
    setIsSending(true);
    try {
      await lmsLiteApi.sendNotification({ target, message, channel });
      const refreshed = await lmsLiteApi.getNotificationLog();
      setLogs(refreshed?.items || []);
      alert('Notificação enviada.');
    } catch (e) {
      alert(`Falha no envio: ${e.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const schedule = async () => {
    setIsSending(true);
    try {
      await lmsLiteApi.scheduleNotification({ target, message, channel, delay_minutes: Number(delayMinutes) || 0 });
      alert('Envio agendado com sucesso.');
    } catch (e) {
      alert(`Falha ao agendar: ${e.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const previewText = useMemo(() => {
    const example = students[0] || { full_name: 'Aluno Exemplo', progress: 25 };
    const enrollment = example.enrollments?.[0]?.course || { title: 'TDS' };
    return replaceVariables(message, { ...example, progresso: example.progress || 0 }, enrollment);
  }, [message, students]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 glass-card p-6 space-y-4">
        <h3 className="text-xl font-bold">Central de Notificações</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select value={targetType} onChange={(e) => setTargetType(e.target.value)}>
            <option value="all">Todos</option>
            <option value="course">Por Curso</option>
            <option value="inactive">Inativos há X dias</option>
          </select>
          {targetType === 'course' && (
            <select value={courseSlug} onChange={(e) => setCourseSlug(e.target.value)}>
              {courses.map((c) => <option key={c.slug} value={c.slug}>{c.title || c.slug}</option>)}
            </select>
          )}
          {targetType === 'inactive' && (
            <input
              type="number"
              min="1"
              value={inactiveDays}
              onChange={(e) => setInactiveDays(Number(e.target.value))}
              placeholder="Dias"
            />
          )}
          <select value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="whatsapp">WhatsApp</option>
            <option value="telegram">Telegram</option>
            <option value="both">Ambos</option>
          </select>
        </div>

        <textarea
          className="w-full h-36"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Mensagem com variáveis: {nome}, {curso}, {progresso}"
        />

        <div className="p-3 rounded-xl border border-border text-sm">
          <p className="font-semibold mb-1">Preview da mensagem</p>
          <p className="text-text-dim">{previewText}</p>
        </div>

        <div className="flex gap-3 items-center">
          <button className="btn btn-primary" onClick={sendNow} disabled={isSending}>Enviar agora</button>
          <input
            type="number"
            min="0"
            value={delayMinutes}
            onChange={(e) => setDelayMinutes(e.target.value)}
            className="w-24"
          />
          <button className="btn btn-outline" onClick={schedule} disabled={isSending}>Agendar (min)</button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="glass-card p-4">
          <h4 className="font-semibold mb-2">Preview destinatários ({recipientsPreview.length})</h4>
          <div className="max-h-48 overflow-auto text-xs space-y-1">
            {recipientsPreview.slice(0, 30).map((phone) => <p key={phone}>{phone}</p>)}
          </div>
        </div>
        <div className="glass-card p-4">
          <h4 className="font-semibold mb-2">Últimos 10 envios</h4>
          <div className="space-y-2 text-xs">
            {logs.map((item, idx) => (
              <div key={idx} className="border border-border rounded-lg p-2">
                <p><b>Target:</b> {item.target}</p>
                <p><b>Canal:</b> {item.channel}</p>
                <p><b>Sucesso/Falha:</b> {item.sent}/{item.failed}</p>
              </div>
            ))}
            {logs.length === 0 && <p className="text-text-dim">Nenhum envio registrado.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
