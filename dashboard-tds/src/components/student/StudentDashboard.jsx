import { CourseCard } from '../shared/CourseCard';
import { ProgressBar } from '../shared/ProgressBar';

export default function StudentDashboard({ student }) {
  const interactions = student?.interactions || [];

  return (
    <main className="mx-auto w-full max-w-md space-y-5 p-4">
      <header className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs uppercase text-slate-400">Olá,</p>
        <h1 className="text-2xl font-semibold text-white">{student?.name || 'Aluno(a)'}</h1>
      </header>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-200">Curso ativo</h2>
        <CourseCard
          course={{
            title: student?.current_course?.title || 'Sem curso ativo',
            slug: student?.current_course?.slug || 'n/a',
            progress: student?.progress || 0,
            status: 'active',
          }}
        />
        <ProgressBar value={student?.progress || 0} label="Seu progresso" showPercent />
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-slate-200">Conquistas</h2>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {(student?.badges || []).map((badge) => (
            <span key={badge.id || badge.name} className="rounded-full border border-amber-400/30 bg-amber-400/15 px-3 py-1 text-xs text-amber-200">
              {badge.name || 'Badge'}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-slate-200">Últimas interações com IA</h2>
        <ul className="space-y-2">
          {interactions.slice(0, 5).map((item, index) => (
            <li key={item.id || index} className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
              {item.message || 'Interação sem conteúdo'}
            </li>
          ))}
          {interactions.length === 0 && <li className="text-xs text-slate-400">Sem interações recentes.</li>}
        </ul>
      </section>

      <button type="button" className="w-full rounded-xl bg-[var(--accent,#f4bf00)] px-4 py-3 text-sm font-semibold text-black">
        Próximo passo
      </button>
    </main>
  );
}
