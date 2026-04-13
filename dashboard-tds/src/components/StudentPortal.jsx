import React, { useState, useEffect } from 'react';
import { BookOpen, GraduationCap, Award, MessageSquare, Download, CheckCircle, Clock, Send, RefreshCw, Trophy, ClipboardList, X } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { lmsLiteApi } from '../api/lms_lite';
import { supabase } from '../lib/supabase';
import QuizPlayer from './student/QuizPlayer';

const VALIDATE_BASE = import.meta.env.VITE_APP_URL || 'https://ops.ipexdesenvolvimento.cloud';
const CHATWOOT_TOKEN = import.meta.env.VITE_CHATWOOT_WEBSITE_TOKEN || 'twnJ2K7tWtP2Fqey97p4hcwV';
const CHATWOOT_BASE_URL = import.meta.env.VITE_CHATWOOT_BASE_URL || 'https://chat.ipexdesenvolvimento.cloud';

export default function StudentPortal() {
  const [step, setStep] = useState('phone'); // 'phone' | 'otp' | 'portal'
  const [phone, setPhone] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [certPreview, setCertPreview] = useState(null);
  const [quizModal, setQuizModal] = useState(null); // { courseSlug, courseTitle }

  // Restore session on mount
  useEffect(() => {
    const token = sessionStorage.getItem('tds_student_token');
    if (token) {
      lmsLiteApi.getMe()
        .then(data => { setStudent(data); setStep('portal'); })
        .catch(() => sessionStorage.removeItem('tds_student_token'));
    }
  }, []);

  // Chatwoot Integration
  useEffect(() => {
    if (step === 'portal' && CHATWOOT_TOKEN) {
      (function(d,t) {
        var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
        g.src=CHATWOOT_BASE_URL+"/packs/js/sdk.js";
        g.defer = true; g.async = true;
        g.onload=function(){
          window.chatwootSDK.run({
            websiteToken: CHATWOOT_TOKEN,
            baseUrl: CHATWOOT_BASE_URL
          })
          // Set user identity if student is loaded
          if (student) {
            window.chatwootSDK.setUser(student.whatsapp, {
              email: student.email || '',
              name: student.full_name || student.name,
              avatar_url: '',
              identifier_hash: ''
            });
            window.chatwootSDK.setCustomAttributes({
              whatsapp: student.whatsapp,
              catraca_estado: student.catraca?.estado || 'inativo'
            });
          }
        }
        s.parentNode.insertBefore(g,s);
      })(document,"script");
    }
  }, [step, student]);

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await lmsLiteApi.sendOtp(phone.trim());
      setStep('otp');
    } catch (err) {
      setError(err.message || 'Erro ao enviar código. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { token, student: s } = await lmsLiteApi.verifyOtp(phone.trim(), otpCode.trim());
      sessionStorage.setItem('tds_student_token', token);
      setStudent(s);
      setStep('portal');
    } catch (err) {
      setError(err.message || 'Código inválido. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  // Supabase Realtime Sync (optional — only runs when credentials are set)
  useEffect(() => {
    if (!supabase || step !== 'portal' || !student) return;

    const channel = supabase
      .channel('public:enrollments')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'enrollments', filter: `whatsapp=eq.${student.whatsapp}` },
        () => { lmsLiteApi.getMe().then(setStudent).catch(console.error); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [step, student?.whatsapp]);

  const handleLogout = () => {
    sessionStorage.removeItem('tds_student_token');
    setStudent(null);
    setPhone('');
    setOtpCode('');
    setStep('phone');
  };

  if (step === 'phone') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 max-w-md w-full">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-4">
              <GraduationCap size={32} />
            </div>
            <h2 className="text-2xl font-bold">Portal do Aluno TDS</h2>
            <p className="text-text-dim text-sm text-center mt-2">
              Informe seu número de WhatsApp para receber um código de acesso.
            </p>
          </div>
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div className="input-group">
              <label className="input-label">WhatsApp (com código do país)</label>
              <input
                type="tel"
                className="w-full"
                placeholder="Ex: 5563999999999"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-red-500 text-xs italic">{error}</p>}
            <button type="submit" className="btn btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Enviando...' : <><Send size={16} className="inline mr-2" />Receber Código por WhatsApp</>}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (step === 'otp') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 max-w-md w-full">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center text-secondary mb-4">
              <Send size={32} />
            </div>
            <h2 className="text-2xl font-bold">Código Enviado!</h2>
            <p className="text-text-dim text-sm text-center mt-2">
              Verifique o WhatsApp de <strong>{phone}</strong> e insira o código de 6 dígitos abaixo.
            </p>
          </div>
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="input-group">
              <label className="input-label">Código de Acesso</label>
              <input
                type="text"
                className="w-full text-center text-2xl tracking-widest font-mono"
                placeholder="000000"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                required
              />
            </div>
            {error && <p className="text-red-500 text-xs italic">{error}</p>}
            <button type="submit" className="btn btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Verificando...' : 'Entrar no Portal'}
            </button>
            <button
              type="button"
              className="text-xs text-text-muted hover:text-primary underline w-full text-center"
              onClick={() => { setStep('phone'); setError(''); setOtpCode(''); }}
            >
              <RefreshCw size={12} className="inline mr-1" />Usar outro número
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (!student) return null;

  const completedEnrollment = student.enrollments?.find(e => e.status === 'completed');

  return (
    <div className="space-y-8 animate-fade">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-main">
            Olá, {student.full_name || student.name}!
          </h2>
          <p className="text-text-dim">Bem-vindo à sua trilha de desenvolvimento.</p>
        </div>
        <button onClick={handleLogout} className="text-xs text-text-muted hover:text-red-500 underline">
          Sair do Portal
        </button>
      </div>

      {/* Minha Trilha */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <BookOpen size={20} className="text-primary" />
          Minha Trilha de Aprendizado
        </h3>
        <div className="space-y-6">
          {student.enrollments?.map((enroll) => (
            <div key={enroll.id} className="bg-white/5 border border-white/5 rounded-2xl p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-bold text-lg">{enroll.course?.title}</h4>
                  <p className="text-xs text-text-dim uppercase tracking-widest">{enroll.status}</p>
                </div>
                {enroll.status === 'completed' ? (
                  <span className="bg-emerald-500/20 text-emerald-500 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                    <CheckCircle size={14} /> Concluído
                  </span>
                ) : (
                  <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                    <Clock size={14} /> Em Andamento
                  </span>
                )}
              </div>
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-xs font-bold">
                  <span>Progresso</span>
                  <span>{enroll.progress_percent}%</span>
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div className="bg-primary h-full transition-all duration-1000" style={{ width: `${enroll.progress_percent}%` }} />
                </div>
              </div>
              {enroll.quiz_results && (
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs font-bold text-violet-200">
                  <Trophy size={14} />
                  Quiz: {enroll.quiz_results.score}/{enroll.quiz_results.total}
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                <a
                  href="https://wa.me/5563999374165?text=/ajuda"
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-outline flex-1 py-2 text-sm gap-2"
                >
                  <MessageSquare size={16} /> Falar com Tutor
                </a>
                <button
                  className="btn btn-outline flex-1 py-2 text-sm gap-2"
                  onClick={() => setQuizModal({ courseSlug: enroll.course?.slug, courseTitle: enroll.course?.title })}
                >
                  <ClipboardList size={16} /> Fazer Quiz
                </button>
                {enroll.status === 'completed' && (
                  <>
                    <button
                      className="btn btn-primary flex-1 py-2 text-sm gap-2"
                      onClick={() => setCertPreview(enroll)}
                    >
                      <Download size={16} /> Ver Certificado
                    </button>
                    <a
                      className="btn btn-outline flex-1 py-2 text-sm gap-2"
                      href={lmsLiteApi.getCertPdfUrl(enroll.certificate_hash)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Download size={16} /> Baixar PDF
                    </a>
                  </>
                )}
              </div>
            </div>
          ))}
          {(!student.enrollments || student.enrollments.length === 0) && (
            <p className="text-center text-text-dim italic">Nenhuma matrícula encontrada.</p>
          )}
        </div>
      </div>

      {/* Certificado com QR Code */}
      {completedEnrollment?.certificate_hash && (
        <div className="glass-card p-6 border-amber-500/20 bg-amber-500/5">
          <h3 className="text-xl font-bold text-amber-500 flex items-center gap-2 mb-4">
            <Award size={24} /> Certificado Validado
          </h3>
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="bg-white p-3 rounded-xl">
              <QRCodeSVG
                value={`${VALIDATE_BASE}/validate/${completedEnrollment.certificate_hash}`}
                size={140}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-text-dim mb-2">
                Escaneie o QR code para verificar a autenticidade deste certificado.
              </p>
              <p className="font-mono text-xs text-text-muted break-all">
                Hash: {completedEnrollment.certificate_hash}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Guia */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen size={18} className="text-primary" /> Como Usar o TDS
        </h3>
        {[
          { step: '1', title: 'Fale com o robô', desc: 'Envie uma mensagem para nosso WhatsApp. O assistente vai te guiar no curso.' },
          { step: '2', title: 'Peça ajuda humana', desc: 'A qualquer momento, envie "/ajuda" para ser atendido por um tutor real.' },
          { step: '3', title: 'Obtenha seu certificado', desc: 'Ao concluir o curso, envie "/certificado" e receba aqui no portal.' },
        ].map(({ step, title, desc }) => (
          <div key={step} className="flex gap-4 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm shrink-0">
              {step}
            </div>
            <div>
              <p className="font-semibold text-sm">{title}</p>
              <p className="text-xs text-text-dim">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quiz Modal */}
      {quizModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-card p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <ClipboardList size={20} className="text-primary" />
                Quiz — {quizModal.courseTitle}
              </h3>
              <button onClick={() => setQuizModal(null)} className="text-text-muted hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            <QuizPlayer
              courseSlug={quizModal.courseSlug}
              phone={student?.whatsapp}
              onClose={() => {
                setQuizModal(null);
                lmsLiteApi.getMe().then(setStudent).catch(console.error);
              }}
            />
          </div>
        </div>
      )}

      {/* Certificate Preview Modal */}
      {certPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-card p-8 max-w-sm w-full text-center">
            <Award size={48} className="text-amber-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2">{certPreview.course?.title}</h3>
            <p className="text-text-dim text-sm mb-2">Certificado de Conclusão</p>
            <p className="font-bold text-lg mb-4">{student.full_name || student.name}</p>
            <div className="bg-white p-3 rounded-xl mx-auto w-fit mb-4">
              <QRCodeSVG
                value={`${VALIDATE_BASE}/validate/${certPreview.certificate_hash}`}
                size={160}
              />
            </div>
            <p className="font-mono text-xs text-text-muted mb-6 break-all">
              {certPreview.certificate_hash}
            </p>
            <button className="btn btn-primary w-full" onClick={() => setCertPreview(null)}>
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
