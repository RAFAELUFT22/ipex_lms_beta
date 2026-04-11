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
      {
        id: 1,
        text: `Pergunta de exemplo para quiz ${quizId}`,
        options: ['Opção A', 'Opção B', 'Opção C'],
        correct: 1,
      },
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

  const current = questions[index];
  const progressPercent =
    step === STEPS.complete
      ? 100
      : Math.round(((index + (step === STEPS.feedback ? 1 : 0)) / questions.length) * 100);

  /* ── Loading ─────────────────────────────────────────────── */
  if (step === STEPS.loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl text-primary animate-pulse">quiz</span>
          <p className="font-bold font-headline text-on-surface">Carregando quiz...</p>
        </div>
      </div>
    );
  }

  /* ── Complete ─────────────────────────────────────────────── */
  if (step === STEPS.complete) {
    const passed = score >= Math.ceil(questions.length / 2);
    return (
      <div className="min-h-screen bg-surface flex flex-col items-center justify-center px-6 text-center space-y-6">
        <span className="material-symbols-outlined text-8xl text-secondary">workspace_premium</span>
        <div>
          <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">
            Quiz concluído
          </span>
          <p className="text-5xl font-bold text-primary font-headline mt-2">
            {score}/{questions.length}
          </p>
          <p className="text-on-surface-variant mt-2 text-sm">
            {passed ? 'Parabéns! Você foi aprovado.' : 'Continue estudando e tente novamente.'}
          </p>
        </div>

        {passed && (
          <div className="bg-secondary-fixed text-on-secondary-fixed rounded-full px-6 py-3 text-sm font-bold flex items-center gap-2">
            <span className="material-symbols-outlined text-base">workspace_premium</span>
            Badge desbloqueada!
          </div>
        )}

        <button
          type="button"
          className="bg-cerrado-gradient text-white rounded-xl py-4 px-8 font-bold w-full max-w-sm flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined">verified</span>
          Ver Certificado
        </button>
      </div>
    );
  }

  /* ── Question / Feedback ──────────────────────────────────── */
  const isCorrect = selected === current.correct;

  function getOptionClass(optionIndex) {
    const isSelected = selected === optionIndex;

    // During feedback
    if (step === STEPS.feedback) {
      if (optionIndex === current.correct) {
        return 'bg-secondary-fixed text-on-secondary-fixed border-2 border-transparent';
      }
      if (isSelected && !isCorrect) {
        return 'bg-tertiary-fixed text-on-tertiary-fixed border-2 border-transparent';
      }
      return 'bg-surface-container-high text-on-surface opacity-50 border-2 border-transparent';
    }

    // During question selection
    if (isSelected) {
      return 'bg-primary-fixed border-2 border-primary text-on-primary-fixed';
    }
    return 'bg-surface-container-high text-on-surface border-2 border-transparent hover:bg-surface-container-highest';
  }

  return (
    <div className="min-h-screen bg-surface pb-24">
      {/* Progress bar at top */}
      <div className="bg-surface-container-high h-1.5 w-full">
        <div
          className="bg-cerrado-gradient h-full transition-all duration-700 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Question card */}
      <div className="bg-surface-container-low rounded-xl p-8 mx-4 my-6 shadow-cerrado-fab space-y-2">
        <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">
          Pergunta {index + 1} de {questions.length}
        </span>
        <p className="text-xl font-bold text-on-surface font-headline leading-tight">
          {current.text}
        </p>
      </div>

      {/* Options */}
      <div className="px-4 space-y-3">
        {current.options.map((option, optionIndex) => (
          <button
            key={option}
            type="button"
            disabled={step === STEPS.feedback}
            onClick={() => setSelected(optionIndex)}
            className={`w-full rounded-xl py-4 px-6 font-bold text-left transition-all duration-200 ${getOptionClass(optionIndex)}`}
          >
            {option}
          </button>
        ))}
      </div>

      {/* Confirm button */}
      {step === STEPS.question && (
        <div className="px-4 mt-6">
          <button
            type="button"
            disabled={selected === null}
            onClick={confirmAnswer}
            className="bg-cerrado-gradient text-white rounded-xl py-4 px-8 font-bold w-full disabled:opacity-40 transition-opacity"
          >
            Confirmar resposta
          </button>
        </div>
      )}

      {/* Feedback banner */}
      {step === STEPS.feedback && (
        <div className="px-4 mt-6 space-y-3">
          {isCorrect ? (
            <div className="bg-secondary-fixed text-on-secondary-fixed p-4 rounded-xl flex gap-3 items-start">
              <span className="material-symbols-outlined text-xl shrink-0">check_circle</span>
              <div>
                <p className="font-bold">Correto!</p>
                <p className="text-sm opacity-80 mt-0.5">Excelente! Continue assim.</p>
              </div>
            </div>
          ) : (
            <div className="bg-tertiary-fixed text-on-tertiary-fixed p-4 rounded-xl flex gap-3 items-start">
              <span className="material-symbols-outlined text-xl shrink-0">cancel</span>
              <div>
                <p className="font-bold">Resposta incorreta.</p>
                <p className="text-sm opacity-80 mt-0.5">
                  A resposta certa era: {current.options[current.correct]}
                </p>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={next}
            className="bg-cerrado-gradient text-white rounded-xl py-4 px-8 font-bold w-full flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined">arrow_forward</span>
            {index + 1 >= questions.length ? 'Ver resultado' : 'Próxima pergunta'}
          </button>
        </div>
      )}
    </div>
  );
}
