import React, { useEffect, useState } from 'react';
import { lmsLiteApi } from '../api/lms_lite';

function emptyQuestion() {
  return {
    text: '',
    options: ['', '', '', ''],
    correct: 0,
  };
}

export default function QuizBuilder() {
  const [courseSlug, setCourseSlug] = useState('');
  const [courses, setCourses] = useState([]);
  const [questions, setQuestions] = useState([emptyQuestion()]);
  const [existingQuestions, setExistingQuestions] = useState([]);
  const [loadingExisting, setLoadingExisting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    lmsLiteApi.getCourses()
      .then((data) => {
        setCourses(data || []);
        if (data?.[0]?.slug) setCourseSlug(data[0].slug);
      })
      .catch(() => setCourses([]));
  }, []);

  useEffect(() => {
    if (!courseSlug) return;
    setLoadingExisting(true);
    lmsLiteApi.getQuiz(courseSlug)
      .then((data) => setExistingQuestions(data?.questions || []))
      .catch(() => setExistingQuestions([]))
      .finally(() => setLoadingExisting(false));
  }, [courseSlug]);

  const updateQuestion = (idx, updater) => {
    setQuestions((prev) => prev.map((q, i) => (i === idx ? updater(q) : q)));
  };

  const addQuestion = () => setQuestions((prev) => [...prev, emptyQuestion()]);

  const removeQuestion = (idx) => {
    setQuestions((prev) => prev.filter((_, i) => i !== idx));
  };

  const saveQuiz = async () => {
    if (!courseSlug) {
      alert('Selecione um curso.');
      return;
    }
    setSaving(true);
    try {
      await lmsLiteApi.saveQuiz(courseSlug, questions);
      alert('Quiz salvo com sucesso!');
      const fresh = await lmsLiteApi.getQuiz(courseSlug);
      setExistingQuestions(fresh?.questions || []);
    } catch (e) {
      alert(`Erro ao salvar quiz: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-xl font-bold">Construtor de Avaliações</h3>
        <div className="input-group">
          <label className="input-label">Curso</label>
          <select value={courseSlug} onChange={(e) => setCourseSlug(e.target.value)}>
            <option value="">Selecione...</option>
            {courses.map((c) => (
              <option key={c.slug} value={c.slug}>{c.title || c.slug}</option>
            ))}
          </select>
        </div>

        {questions.map((q, idx) => (
          <div key={idx} className="p-4 border border-border rounded-xl space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold">Questão {idx + 1}</h4>
              <button className="btn btn-outline py-1 px-2 text-xs" onClick={() => removeQuestion(idx)}>
                Remover
              </button>
            </div>
            <input
              type="text"
              placeholder="Texto da pergunta"
              value={q.text}
              onChange={(e) => updateQuestion(idx, (old) => ({ ...old, text: e.target.value }))}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {q.options.map((op, opIdx) => (
                <input
                  key={opIdx}
                  type="text"
                  placeholder={`Opção ${opIdx + 1}`}
                  value={op}
                  onChange={(e) => updateQuestion(idx, (old) => {
                    const next = [...old.options];
                    next[opIdx] = e.target.value;
                    return { ...old, options: next };
                  })}
                />
              ))}
            </div>
            <div className="input-group mb-0">
              <label className="input-label">Resposta correta</label>
              <select
                value={q.correct}
                onChange={(e) => updateQuestion(idx, (old) => ({ ...old, correct: Number(e.target.value) }))}
              >
                {[0, 1, 2, 3].map((v) => (
                  <option key={v} value={v}>Opção {v + 1}</option>
                ))}
              </select>
            </div>
          </div>
        ))}

        <div className="flex gap-3">
          <button className="btn btn-outline" onClick={addQuestion}>Adicionar questão</button>
          <button className="btn btn-primary" onClick={saveQuiz} disabled={saving}>
            {saving ? 'Salvando...' : 'Salvar Quiz'}
          </button>
        </div>
      </div>

      <div className="glass-card p-6">
        <h4 className="font-semibold mb-3">Questões existentes</h4>
        {loadingExisting && <p className="text-sm text-text-dim">Carregando...</p>}
        {!loadingExisting && existingQuestions.length === 0 && (
          <p className="text-sm text-text-dim">Nenhuma questão cadastrada para este curso.</p>
        )}
        <ol className="space-y-3 list-decimal pl-5">
          {existingQuestions.map((q, i) => (
            <li key={i}>
              <p className="font-medium">{q.text}</p>
              <ul className="list-disc pl-5 text-sm text-text-dim">
                {(q.options || []).map((op, idx) => <li key={idx}>{op}</li>)}
              </ul>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
