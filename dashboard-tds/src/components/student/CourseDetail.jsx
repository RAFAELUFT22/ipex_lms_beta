import { useMemo } from 'react';
import { ChevronDown, Lock, CheckCircle2, Clock3, FileQuestion } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';

export default function CourseDetail({ courseSlug }) {
  const modules = useMemo(
    () => [
      { id: 1, title: 'Introdução', status: 'done', duration: '10 min', type: 'video' },
      { id: 2, title: 'Módulo Principal', status: 'available', duration: '25 min', type: 'lesson' },
      { id: 3, title: 'Projeto Final', status: 'locked', duration: '40 min', type: 'project' },
    ],
    [],
  );

  return (
    <main className="space-y-4 p-4">
      <header className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs text-slate-400">Curso</p>
        <h1 className="text-xl font-semibold text-white">{courseSlug}</h1>
        <p className="text-sm text-slate-300">Instrutor: TODO</p>
      </header>

      <ProgressBar value={42} label="Progresso geral" showPercent />

      <section className="space-y-2">
        {modules.map((module) => (
          <details key={module.id} className="rounded-xl border border-white/10 bg-black/20 p-3">
            <summary className="flex cursor-pointer list-none items-center justify-between text-sm text-white">
              <span className="inline-flex items-center gap-2">
                {module.status === 'done' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : module.status === 'locked' ? <Lock className="h-4 w-4 text-slate-500" /> : <Clock3 className="h-4 w-4 text-amber-300" />}
                {module.title}
              </span>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </summary>
            <div className="mt-2 text-xs text-slate-300">
              <p>Duração: {module.duration}</p>
              <p>Tipo: {module.type}</p>
              <p className="text-slate-400">TODO: renderizar conteúdo do módulo.</p>
            </div>
          </details>
        ))}
      </section>

      <article className="rounded-2xl border border-amber-400/40 bg-amber-400/10 p-4">
        <h3 className="mb-1 flex items-center gap-2 font-semibold text-amber-200">
          <FileQuestion className="h-4 w-4" /> Quiz disponível
        </h3>
        <p className="text-sm text-amber-100">TODO: mostrar status e ação para iniciar quiz.</p>
      </article>

      <article className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <h3 className="mb-1 font-semibold text-white">Certificado</h3>
        <p className="text-sm text-slate-300">TODO: desbloquear ao atingir 100% + quiz aprovado.</p>
      </article>
    </main>
  );
}
