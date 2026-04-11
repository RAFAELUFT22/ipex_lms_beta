const MODE_CONFIG = {
  bot:    { label: 'Bot',    bg: 'bg-primary-fixed text-on-primary-fixed' },
  human:  { label: 'Humano', bg: 'bg-secondary-fixed text-on-secondary-fixed' },
  new:    { label: 'Novo',   bg: 'bg-tertiary-fixed text-on-tertiary-fixed' },
};

export function StudentBadge({ phone, name, mode = 'new' }) {
  const cfg = MODE_CONFIG[mode] || MODE_CONFIG.new;
  const initial = (name || phone || '?')[0].toUpperCase();
  return (
    <div className="flex items-center gap-3 min-w-0">
      <div className="w-9 h-9 rounded-full bg-surface-container-high flex items-center justify-center shrink-0">
        <span className="text-sm font-bold text-on-surface-variant">{initial}</span>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-bold text-on-surface truncate">{name || 'Aluno'}</p>
        <p className="text-xs text-on-surface-variant truncate">{phone}</p>
      </div>
      <span className={`ml-auto shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${cfg.bg}`}>{cfg.label}</span>
    </div>
  );
}
export default StudentBadge;
