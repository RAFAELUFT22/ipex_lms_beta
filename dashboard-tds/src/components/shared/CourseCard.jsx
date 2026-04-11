import { ProgressBar } from './ProgressBar';

export function CourseCard({ course = {}, onClick }) {
  const { title = 'Curso', progress = 0, status = 'active' } = course;
  const statusLabel = status === 'completed' ? 'Concluído' : status === 'active' ? 'Em andamento' : 'Bloqueado';
  const statusColor = status === 'completed' ? 'bg-secondary-fixed text-on-secondary-fixed' : status === 'active' ? 'bg-primary-fixed text-on-primary-fixed' : 'bg-surface-container-highest text-on-surface-variant';
  return (
    <div onClick={onClick} className="cerrado-card p-6 cursor-pointer space-y-4">
      <div className="flex justify-between items-start gap-2">
        <h3 className="font-bold text-on-surface text-base leading-tight">{title}</h3>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${statusColor}`}>{statusLabel}</span>
      </div>
      <ProgressBar value={progress} showPercent />
      <button className="w-full bg-cerrado-gradient text-white rounded-xl py-2 font-bold text-sm">
        {status === 'completed' ? 'Ver Certificado' : 'Continuar'}
      </button>
    </div>
  );
}
export default CourseCard;
