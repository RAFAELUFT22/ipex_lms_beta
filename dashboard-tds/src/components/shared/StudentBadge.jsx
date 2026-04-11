const modeClasses = {
  bot: 'bg-teal-500/20 text-teal-200',
  human: 'bg-amber-400/20 text-amber-200',
  new: 'bg-slate-600/20 text-slate-200',
};

export function StudentBadge({ phone, name, mode = 'new' }) {
  const initial = (name || '?').charAt(0).toUpperCase();

  return (
    <div className="flex items-center gap-3">
      <div className="grid h-9 w-9 place-items-center rounded-full bg-white/10 text-sm font-semibold text-white">
        {initial}
      </div>
      <div>
        <p className="text-sm font-medium text-white">{name || 'Sem nome'}</p>
        <p className="text-xs text-slate-400">{phone}</p>
      </div>
      <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] uppercase ${modeClasses[mode] || modeClasses.new}`}>
        {mode}
      </span>
    </div>
  );
}
