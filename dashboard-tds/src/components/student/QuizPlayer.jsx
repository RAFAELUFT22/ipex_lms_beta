import { useEffect, useMemo, useState } from 'react';

const STEPS = {
  loading: 'loading',
  question: 'question',
  feedback: 'feedback',
  complete: 'complete',
};

export default function QuizPlayer({ quizId }) {
  const [step, setStep] = useState(STEPS.loading);
  const [selected, setSelected] = useState(null);
  const [score, setScore] = useState(0);
  const [index, setIndex] = useState(0);

  const questions = useMemo(
    () => [
      { id: 1, text: `Pergunta de exemplo para quiz ${quizId}`, options: ['A', 'B', 'C'], correct: 1 },
    ],
    [quizId],
  );

  useEffect(() => {
    // TODO: replace with async fetch by quizId
    setStep(STEPS.question);
  }, []);

  function confirmAnswer() {
    const current = questions[index];
    if (selected === current.correct) setScore((s) => s + 1);
    setStep(STEPS.feedback);
  }

  function next() {
    const nextIndex = index + 1;
    if (nextIndex >= questions.length) {
      setStep(STEPS.complete);
      return;
    }
    setSelected(null);
    setIndex(nextIndex);
    setStep(STEPS.question);
  }

  if (step === STEPS.loading) return <p className="p-4 text-slate-300">Carregando quiz...</p>;

  if (step === STEPS.complete) {
    return (
      <section className="space-y-3 p-4 text-center">
        <h2 className="text-2xl font-semibold text-white">Quiz concluído</h2>
        <p className="text-slate-300">Pontuação: {score}/{questions.length}</p>
        <span className="inline-flex rounded-full bg-amber-400/20 px-3 py-1 text-amber-200">Badge desbloqueada (stub)</span>
      </section>
    );
  }

  const current = questions[index];
  return (
    <section className="space-y-4 p-4">
      <h2 className="text-3xl font-semibold text-white" style={{ fontFamily: 'Lexend, sans-serif' }}>
        {current.text}
      </h2>
      <div className="space-y-2">
        {current.options.map((option, optionIndex) => (
          <button
            key={option}
            type="button"
            onClick={() => setSelected(optionIndex)}
            className={`w-full rounded-xl border px-4 py-3 text-left ${selected === optionIndex ? 'border-teal-400 bg-teal-500/10 text-white' : 'border-white/10 text-slate-300'}`}
          >
            {option}
          </button>
        ))}
      </div>

      {step === STEPS.question && (
        <button type="button" disabled={selected === null} onClick={confirmAnswer} className="w-full rounded-xl bg-teal-600 px-4 py-3 text-white disabled:opacity-40">
          Confirmar resposta
        </button>
      )}

      {step === STEPS.feedback && (
        <div className="space-y-2 rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-sm text-slate-200">
            {selected === current.correct ? '✅ Correto!' : '❌ Resposta incorreta.'}
          </p>
          <button type="button" onClick={next} className="w-full rounded-lg bg-[var(--accent,#f4bf00)] px-3 py-2 text-sm font-medium text-black">
            Avançar
          </button>
        </div>
      )}
    </section>
  );
}
