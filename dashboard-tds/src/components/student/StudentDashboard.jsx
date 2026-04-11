import { CourseCard } from '../shared/CourseCard';
import { ProgressBar } from '../shared/ProgressBar';

export default function StudentDashboard({ student }) {
  const interactions = student?.interactions || [];
  const badges = student?.badges || [];

  const activeCourse = student?.activeCourse || {
    title: student?.current_course?.title || student?.current_course || 'Introdução TDS',
    slug: student?.current_course?.slug || 'introducao-tds',
    progress: student?.progress || 0,
    status: 'active',
  };

  return (
    <div className="min-h-screen bg-surface pb-24">
      {/* TopAppBar */}
      <header className="sticky top-0 z-10 bg-surface px-6 py-4 flex justify-between items-center shadow-sm">
        <h1 className="text-xl font-bold text-primary font-headline">Horizonte Cerrado</h1>
        <div className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center overflow-hidden">
          {student?.avatar ? (
            <img src={student.avatar} alt={student?.name || 'Aluno'} className="w-full h-full object-cover" />
          ) : (
            <span className="material-symbols-outlined text-on-surface-variant">person</span>
          )}
        </div>
      </header>

      <main className="px-6 pt-6 space-y-10 max-w-2xl mx-auto">
        {/* Greeting */}
        <section>
          <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">
            Painel do Aluno
          </span>
          <h2 className="text-4xl font-bold text-on-surface font-headline tracking-tight mt-1">
            Olá, {student?.name || 'Aluno'}!
          </h2>
          <p className="text-on-surface-variant mt-2">
            A educação não transforma o mundo. Educação muda as pessoas, e pessoas transformam o mundo.
          </p>
        </section>

        {/* Active Course Card */}
        <section className="bg-surface-container-low rounded-xl p-6 space-y-4">
          <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">
            Seu Curso Ativo
          </span>
          <CourseCard course={activeCourse} />
        </section>

        {/* Achievements badges row */}
        <section className="space-y-3">
          <h3 className="font-bold text-on-surface">Conquistas</h3>
          <div className="flex gap-3 flex-wrap">
            {badges.length > 0 ? (
              badges.map((badge, idx) => (
                <span
                  key={badge.id || badge.name || idx}
                  className="bg-secondary-container text-on-secondary-container rounded-full px-4 py-2 text-sm font-bold flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">workspace_premium</span>
                  {badge.name || badge}
                </span>
              ))
            ) : (
              <span className="text-sm text-on-surface-variant">
                Complete atividades para ganhar conquistas!
              </span>
            )}
          </div>
        </section>

        {/* Recent AI interactions */}
        <section className="space-y-3">
          <h3 className="font-bold text-on-surface">Histórico com Tutor IA</h3>
          <div className="space-y-2">
            {interactions.slice(0, 5).map((item, index) => (
              <div
                key={item.id || index}
                className="bg-surface-container-low rounded-xl p-4 flex gap-3"
              >
                <span className="material-symbols-outlined text-primary shrink-0">smart_toy</span>
                <div>
                  <p className="text-sm text-on-surface line-clamp-2">
                    {item.message || item.content || 'Interação sem conteúdo'}
                  </p>
                  <p className="text-xs text-on-surface-variant mt-1">
                    {item.timestamp
                      ? new Date(item.timestamp).toLocaleString('pt-BR', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : item.date || ''}
                  </p>
                </div>
              </div>
            ))}
            {interactions.length === 0 && (
              <div className="bg-surface-container-low rounded-xl p-4 flex gap-3">
                <span className="material-symbols-outlined text-on-surface-variant shrink-0">smart_toy</span>
                <p className="text-sm text-on-surface-variant">Sem interações recentes com o tutor IA.</p>
              </div>
            )}
          </div>
        </section>

        {/* Next step CTA */}
        <section>
          <button
            type="button"
            className="bg-cerrado-gradient text-white rounded-xl py-4 px-8 font-bold w-full flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined">arrow_forward</span>
            Próximo passo
          </button>
        </section>
      </main>

      {/* WhatsApp FAB */}
      <div className="fixed bottom-6 right-6">
        <button
          type="button"
          className="bg-secondary-container text-on-secondary-container rounded-full p-4 shadow-cerrado-fab flex items-center gap-2 font-bold"
        >
          <span className="material-symbols-outlined">forum</span>
          Tutor
        </button>
      </div>
    </div>
  );
}
