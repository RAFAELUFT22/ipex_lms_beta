export function ModeToggle({ phone, currentMode, onToggle }) {
  const isBot = currentMode === 'bot';
  return (
    <div className="flex rounded-full overflow-hidden border border-outline-variant text-xs font-bold">
      <button
        onClick={() => !isBot && onToggle(phone, 'bot')}
        className={`flex items-center gap-1 px-3 py-1 transition-colors ${isBot ? 'bg-cerrado-gradient text-white' : 'bg-surface text-on-surface-variant hover:bg-surface-container-low'}`}
      >
        <span className="material-symbols-outlined text-sm">smart_toy</span>
        Bot
      </button>
      <button
        onClick={() => isBot && onToggle(phone, 'human')}
        className={`flex items-center gap-1 px-3 py-1 transition-colors ${!isBot ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface text-on-surface-variant hover:bg-surface-container-low'}`}
      >
        <span className="material-symbols-outlined text-sm">person</span>
        Humano
      </button>
    </div>
  );
}
export default ModeToggle;
