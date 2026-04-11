export function ModeToggle({ phone, currentMode = 'bot', onToggle }) {
  const isBot = currentMode === 'bot';

  function handleClick() {
    const nextMode = isBot ? 'human' : 'bot';
    if (typeof onToggle === 'function') onToggle(phone, nextMode);
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex rounded-full p-0.5 text-xs ${isBot ? 'bg-teal-500/30' : 'bg-amber-500/30'}`}
    >
      <span className={`rounded-full px-2 py-1 ${isBot ? 'bg-teal-500 text-white' : 'text-slate-300'}`}>Bot</span>
      <span className={`rounded-full px-2 py-1 ${!isBot ? 'bg-amber-500 text-black' : 'text-slate-300'}`}>Humano</span>
    </button>
  );
}
