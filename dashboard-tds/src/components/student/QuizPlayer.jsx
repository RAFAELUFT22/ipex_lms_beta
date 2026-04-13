import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, ChevronRight, Award, RotateCcw, Loader } from 'lucide-react';
import { lmsLiteApi } from '../../api/lms_lite';

const STEPS = { loading: 'loading', error: 'error', question: 'question', feedback: 'feedback', result: 'result' };

export default function QuizPlayer({ courseSlug, phone, onClose }) {
  const [step, setStep] = useState(STEPS.loading);
  const [questions, setQuestions] = useState([]);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!courseSlug) return;
    lmsLiteApi.getQuiz(courseSlug)
      .then(data => {
        if (!data.questions || data.questions.length === 0) {
          setError('Nenhuma questão cadastrada para este curso ainda.');
          setStep(STEPS.error);
          return;
        }
        setQuestions(data.questions);
        setStep(STEPS.question);
      })
      .catch(err => {
        setError(err.message || 'Erro ao carregar quiz.');
        setStep(STEPS.error);
      });
  }, [courseSlug]);

  const current = questions[index];
  const progressPct = questions.length > 0
    ? Math.round(((index + (step === STEPS.feedback ? 1 : 0)) / questions.length) * 100)
    : 0;

  function confirmAnswer() {
    setStep(STEPS.feedback);
  }

  async function next() {
    const newAnswers = [...answers, selected];
    const nextIndex = index + 1;

    if (nextIndex >= questions.length) {
      // Submit all answers
      setSubmitting(true);
      try {
        const res = await lmsLiteApi.submitQuiz(phone, courseSlug, newAnswers);
        setResult(res);
        setStep(STEPS.result);
      } catch (err) {
        setError(err.message || 'Erro ao enviar respostas. Tente novamente.');
        setStep(STEPS.error);
      } finally {
        setSubmitting(false);
      }
    } else {
      setAnswers(newAnswers);
      setSelected(null);
      setIndex(nextIndex);
      setStep(STEPS.question);
    }
  }

  function restart() {
    setStep(STEPS.loading);
    setIndex(0);
    setSelected(null);
    setAnswers([]);
    setResult(null);
    setError('');
    lmsLiteApi.getQuiz(courseSlug)
      .then(data => { setQuestions(data.questions || []); setStep(STEPS.question); })
      .catch(err => { setError(err.message); setStep(STEPS.error); });
  }

  if (step === STEPS.loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4 text-text-dim">
        <Loader size={32} className="animate-spin text-primary" />
        <p className="text-sm">Carregando quiz...</p>
      </div>
    );
  }

  if (step === STEPS.error) {
    return (
      <div className="text-center py-12 space-y-4">
        <XCircle size={40} className="text-red-400 mx-auto" />
        <p className="text-red-400 text-sm">{error}</p>
        <button onClick={onClose} className="btn btn-outline text-sm px-6">Fechar</button>
      </div>
    );
  }

  if (step === STEPS.result) {
    const passed = result?.passed;
    const score = result?.score ?? 0;
    const total = result?.total ?? questions.length;
    return (
      <div className="text-center space-y-6 py-8">
        <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto ${passed ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
          {passed
            ? <Award size={40} className="text-emerald-400" />
            : <XCircle size={40} className="text-red-400" />}
        </div>
        <div>
          <p className="text-4xl font-bold">{score}<span className="text-xl text-text-dim">/{total}</span></p>
          <p className={`text-lg font-semibold mt-1 ${passed ? 'text-emerald-400' : 'text-red-400'}`}>
            {passed ? 'Aprovado!' : 'Não aprovado'}
          </p>
          <p className="text-text-dim text-sm mt-2">
            {passed
              ? 'Parabéns! Você pode solicitar seu certificado agora.'
              : 'Revise o material e tente novamente quando quiser.'}
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          {!passed && (
            <button onClick={restart} className="btn btn-outline text-sm flex items-center gap-2">
              <RotateCcw size={14} /> Tentar Novamente
            </button>
          )}
          <button onClick={onClose} className="btn btn-primary text-sm px-6">
            {passed ? 'Ver Certificado' : 'Fechar'}
          </button>
        </div>
      </div>
    );
  }

  const isCorrect = selected === current?.correct;

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-muted">
          <span>Pergunta {index + 1} de {questions.length}</span>
          <span>{progressPct}%</span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-primary transition-all duration-500" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      {/* Question */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <p className="text-lg font-semibold leading-snug">{current?.text}</p>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {current?.options?.map((opt, i) => {
          let cls = 'w-full text-left rounded-xl px-4 py-3 border font-medium text-sm transition-all duration-150 ';
          if (step === STEPS.feedback) {
            if (i === current.correct) cls += 'border-emerald-500 bg-emerald-500/20 text-emerald-300';
            else if (i === selected && !isCorrect) cls += 'border-red-500 bg-red-500/20 text-red-300';
            else cls += 'border-white/5 bg-white/5 text-text-muted opacity-50';
          } else {
            if (selected === i) cls += 'border-primary bg-primary/20 text-primary';
            else cls += 'border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20';
          }
          return (
            <button
              key={i}
              className={cls}
              disabled={step === STEPS.feedback}
              onClick={() => setSelected(i)}
            >
              <span className="font-mono text-xs mr-3 opacity-60">{String.fromCharCode(65 + i)}.</span>
              {opt}
            </button>
          );
        })}
      </div>

      {/* Feedback */}
      {step === STEPS.feedback && (
        <div className={`flex items-start gap-3 p-4 rounded-xl border ${isCorrect ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
          {isCorrect
            ? <CheckCircle size={18} className="text-emerald-400 mt-0.5 shrink-0" />
            : <XCircle size={18} className="text-red-400 mt-0.5 shrink-0" />}
          <div>
            <p className={`font-semibold text-sm ${isCorrect ? 'text-emerald-400' : 'text-red-400'}`}>
              {isCorrect ? 'Correto!' : 'Incorreto'}
            </p>
            {!isCorrect && (
              <p className="text-text-dim text-xs mt-0.5">
                Resposta correta: <strong>{current?.options?.[current.correct]}</strong>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      {step === STEPS.question && (
        <button
          className="btn btn-primary w-full py-3 disabled:opacity-40"
          disabled={selected === null}
          onClick={confirmAnswer}
        >
          Confirmar Resposta
        </button>
      )}
      {step === STEPS.feedback && (
        <button
          className="btn btn-primary w-full py-3 flex items-center justify-center gap-2"
          onClick={next}
          disabled={submitting}
        >
          {submitting ? <Loader size={16} className="animate-spin" /> : <ChevronRight size={16} />}
          {index + 1 >= questions.length ? 'Ver Resultado' : 'Próxima Pergunta'}
        </button>
      )}
    </div>
  );
}
