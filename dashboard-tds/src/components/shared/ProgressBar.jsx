export function ProgressBar({ value = 0, label = '', showPercent = true }) {
  const normalized = Math.max(0, Math.min(100, Number(value) || 0));

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-slate-300">
        <span>{label}</span>
        {showPercent && <span>{normalized}%</span>}
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800/80">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${normalized}%`, backgroundColor: 'var(--accent, #f4bf00)' }}
        />
      </div>
    </div>
  );
}
