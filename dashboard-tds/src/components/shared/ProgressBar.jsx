export function ProgressBar({ value = 0, label, showPercent = true }) {
  return (
    <div className="w-full space-y-1">
      {(label || showPercent) && (
        <div className="flex justify-between items-center">
          {label && <span className="text-xs font-bold text-on-surface-variant font-label uppercase tracking-wider">{label}</span>}
          {showPercent && <span className="text-xs font-bold text-secondary">{value}%</span>}
        </div>
      )}
      <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
        <div
          className="h-full bg-cerrado-gradient rounded-full transition-all duration-700 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}
export default ProgressBar;
