import React, { useState } from 'react';
import { Send, CheckCircle, User, MessageCircle, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { lmsLiteApi } from '../api/lms_lite';

export default function Matricula() {
  const [form, setForm] = useState({ name: '', whatsapp: '', course_interest: 'Geral' });
  const [status, setStatus] = useState('idle'); // 'idle', 'submitting', 'success', 'error'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    try {
      // Limpar formatação do whatsapp (apenas números)
      const cleanPhone = form.whatsapp.replace(/\D/g, '');
      await lmsLiteApi.requestEnrollment({ ...form, whatsapp: cleanPhone });
      setStatus('success');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center space-y-6 animate-fade">
        <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center shadow-lg shadow-green-500/20">
          <CheckCircle className="text-green-400 w-12 h-12" />
        </div>
        <h2 className="text-2xl font-bold text-white">Solicitação Enviada!</h2>
        <p className="text-text-dim max-w-sm">
          Recebemos seu interesse. Um de nossos tutores entrará em contato pelo WhatsApp em breve para finalizar sua inscrição.
        </p>
        <button 
          onClick={() => window.location.href = '/'}
          className="btn btn-primary px-8"
        >
          Voltar ao Início
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 space-y-6 border border-white/10 shadow-2xl"
      >
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-white tracking-tight">Comece sua Jornada</h2>
          <p className="text-text-dim text-sm">Preencha os dados abaixo para solicitar sua matrícula no projeto TDS.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 text-left">
          <div className="input-group">
            <label className="input-label flex items-center gap-2">
              <User size={14} className="text-secondary" /> Nome Completo
            </label>
            <input 
              type="text" 
              required
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              placeholder="Ex: João Silva"
              className="bg-bg-deep border-border text-white w-full p-3 rounded-xl focus:ring-2 focus:ring-secondary/50 transition-all"
            />
          </div>

          <div className="input-group">
            <label className="input-label flex items-center gap-2">
              <MessageCircle size={14} className="text-secondary" /> WhatsApp
            </label>
            <input 
              type="tel" 
              required
              value={form.whatsapp}
              onChange={e => setForm({...form, whatsapp: e.target.value})}
              placeholder="DDD + Número"
              className="bg-bg-deep border-border text-white w-full p-3 rounded-xl focus:ring-2 focus:ring-secondary/50 transition-all"
            />
          </div>

          <div className="input-group">
            <label className="input-label flex items-center gap-2">
              <BookOpen size={14} className="text-secondary" /> Curso de Interesse
            </label>
            <select 
              value={form.course_interest}
              onChange={e => setForm({...form, course_interest: e.target.value})}
              className="bg-bg-deep border-border text-white w-full p-3 rounded-xl focus:ring-2 focus:ring-secondary/50 transition-all appearance-none"
            >
              <option value="Geral">Quero conhecer todos</option>
              <option value="Agrofloresta">Agricultura Sustentável</option>
              <option value="Audiovisual">Produção Audiovisual</option>
              <option value="Empreendedorismo">Empreendedorismo Social</option>
            </select>
          </div>

          {status === 'error' && (
            <p className="text-red-400 text-xs italic">Ops! Ocorreu um erro. Tente novamente ou fale conosco no WhatsApp.</p>
          )}

          <button 
            type="submit" 
            disabled={status === 'submitting'}
            className="btn btn-primary w-full py-4 flex items-center justify-center gap-2 text-lg font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all"
          >
            {status === 'submitting' ? (
              <span className="animate-pulse">Enviando...</span>
            ) : (
              <>Solicitar Matrícula <Send size={18} /></>
            )}
          </button>
        </form>

        <p className="text-[10px] text-center text-text-muted uppercase tracking-widest font-bold pt-4">
          Território de Desenvolvimento Social
        </p>
      </motion.div>
    </div>
  );
}
