import { ProgressBar } from './ProgressBar';

const statusClasses = {
  active: 'bg-teal-500/20 text-teal-200',
  completed: 'bg-emerald-500/20 text-emerald-200',
  locked: 'bg-slate-700/30 text-slate-300',
};

export function CourseCard({ course, onClick }) {
  if (!course) return null;

  return (
    <article
      className="glass-card rounded-2xl border border-white/10 bg-white/5 p-4 transition-transform duration-200 hover:-translate-y-1"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' && onClick) onClick(event);
      }}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold text-white">{course.title}</h3>
        <span className={`rounded-full px-2 py-1 text-[10px] uppercase ${statusClasses[course.status] || statusClasses.locked}`}>
          {course.status || 'locked'}
        </span>
      </div>

      <p className="mb-3 text-xs text-slate-400">/{course.slug}</p>
      <ProgressBar value={course.progress || 0} label="Progresso" showPercent />

      <button type="button" className="mt-4 w-full rounded-xl bg-teal-600/80 px-3 py-2 text-sm text-white">
        Continuar
      </button>
    </article>
  );
}
